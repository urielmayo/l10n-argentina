import logging
import os
import tempfile
import re
import shlex
from subprocess import call, STDOUT
from shutil import rmtree
from odoo import registry
from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)

def get_dsn_pg(cr):
    """
    Receives Cursor as parameter.
    Return array with paramenter ready to be used in call to psql command.
    Also it ensures that PGPASSWORD is an Environmental vatiable,
    if this is not ensured psql command fails.
    """
    env_db_pass = os.environ.get('PGPASSWORD')  # Ensure PGPASSWORD
    if not env_db_pass:  # PGPASSWORD is not an environmental vatiable, set it
        db_password = config.get('db_password')
        os.environ['PGPASSWORD'] = db_password
    db_name = config.get('db_name', cr.dbname)
    if not db_name:
        db_name = cr.dbname
    db_port = config.get('db_port')
    if not db_port:
        db_port = 5432
    db_user = config.get('db_user')
    assert db_user is not None, 'db_user must be set in config file'
    db_host = config.get('db_host')
    if not db_host:
        db_host = 'localhost'
    res_string = "--dbname={0} --host={1} --username={2} --port={3}".format(
        db_name, db_host, db_user, db_port)
    res_list = shlex.split(res_string)
    return res_list

class PadronImport(models.Model):
    _name = "padron.import"
    _inherit = "padron.import"

    @api.model
    def import_909_file(self, out_path, files):
        _logger.info('[FORMOSA] Inicio de importacion')
        dsn_pg_splitted = get_dsn_pg(self.env.cr)
        _logger.info('[FORMOSA] Files extracted: ' + str(len(files)))
        if len(files) != 1:
            raise ValidationError(
                _("Expected only one file compressed, got: %d") %
                len(files))

        txt_path = self.correct_padron_formosa(files[0])
        dbname = self.env.cr.dbname
        cursor = registry(dbname).cursor()  # Get a new cursor
        try:
            _logger.info('[FORMOSA] Creando tabla temporal')
            create_q = """
            CREATE TABLE temp_import(
                vat varchar(11),
                denomination varchar(200),
                period varchar,
                category varchar(20),
                category_description varchar(18),
                ac_ret_28_97 varchar,
                ac_per_23_14 varchar,
                date_ret_28_97 varchar(10),
                date_per_23_14 varchar(10),
                ac_per_33_99 varchar,
                ac_per_27_00 varchar,
                date_per_33_99 varchar(10),
                date_per_27_00 varchar(10),
                regime varchar(80),
                exent varchar(2)
            )
            """
            cursor.execute("DROP TABLE IF EXISTS temp_import")
            cursor.execute(create_q)
        except Exception:
            cursor.rollback()
            raise ValidationError(
                _("Could not create the temporary table with the file data"))
        else:
            cursor.commit()

        _logger.info('[FORMOSA] Copiando del csv a tabla temporal')
        psql_args_list = [
            "psql",
            "--command=\copy temp_import(vat, denomination, period, category, category_description, ac_ret_28_97, ac_per_23_14, date_ret_28_97, date_per_23_14, ac_per_33_99, ac_per_27_00, date_per_33_99, date_per_27_00, regime, exent) FROM " + txt_path + " WITH DELIMITER '|' NULL '' CSV QUOTE E'\b' ENCODING 'latin1'"  # noqa
        ]
        psql_args_list[1:1] = dsn_pg_splitted
        retcode = call(psql_args_list, stderr=STDOUT)
        assert retcode == 0, \
            "Call to psql subprocess copy command returned: " + str(retcode)

        try:
            # TODO: Creacion de los grupos de retenciones y percepciones
            _logger.info('[FORMOSA] Verificando grupos')

            _logger.info('[FORMOSA] Copiando de tabla temporal a definitiva')
            query = """
            INSERT INTO padron_formosa
            (create_uid, create_date, write_date, write_uid,
            vat, denomination, period, category, category_description, ac_ret_28_97, ac_per_23_14, date_ret_28_97, date_per_23_14, ac_per_33_99, ac_per_27_00, date_per_33_99, date_per_27_00, regime, exent)
            SELECT 1 as create_uid,
                    current_date,
                    current_date,
                    1,
                    vat,
                    denomination,
                    period,
                    category,
                    category_description,
                    to_number(ac_ret_28_97, '999.99'),
                    to_number(ac_per_23_14, '999.99'),
                    to_date(date_ret_28_97, 'YYYY/MM/DD'),
                    to_date(date_per_23_14, 'YYYY/MM/DD'),
                    to_number(ac_per_33_99, '999.99'),
                    to_number(ac_per_27_00, '999.99'),
                    to_date(date_per_33_99, 'YYYY/MM/DD'),
                    to_date(date_per_27_00, 'YYYY/MM/DD'),
                    regime,
                    (CASE
                        WHEN exent = 'SI'
                        THEN True ELSE False
                    END) as exent
                    FROM temp_import
            """
            cursor.execute("DELETE FROM padron_formosa")
            cursor.execute(query)
            cursor.execute("DROP TABLE IF EXISTS temp_import")
            cursor.commit()
        except Exception:
            cursor.rollback()
            _logger.warning('[FORMOSA] ERROR: Rollback')
        else:
            # Mass Update
            mass_wiz_obj = self.env['padron.mass.update.formosa']
            wiz = mass_wiz_obj.create({
                'formosa': True,
            })
            # TODO
            wiz.action_update_formosa()

            cursor.commit()
            _logger.info('[FORMOSA] SUCCESS: Fin de carga de padron de formosa')

        finally:
            rmtree(out_path)  # Delete temp folder
            cursor.close()
        return True

    def correct_padron_formosa(self, filename):
        new_file_path = tempfile.mkstemp()[1]
        with open(filename, "r", encoding='latin1') as old_file:
            with open(new_file_path, "w", encoding='latin1') as new_file:
                # the | simbol is the separator in this padron and
                # there are lines that have a | in the middle of the name
                # so checking how many | are in each line you could know
                # if line needs to be fixed
                for line in old_file:
                    fields = line.strip().split("|")
                    if len(fields) > 15:
                        fields[1] += fields[2]
                        del fields[2]
                        new_line = "|".join(fields)
                        new_file.write(new_line + "\n")
                    else:
                        new_file.write(line)
        return new_file_path
