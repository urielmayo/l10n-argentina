import logging
import os
import shlex
import tempfile
import re
from base64 import b64decode
from io import BytesIO
from zipfile import ZipFile, is_zipfile
from tempfile import mkdtemp
from subprocess import call, STDOUT
from shutil import rmtree
from odoo import registry
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, Warning
from odoo.tools import config

_logger = logging.getLogger(__name__)

def get_dsn_pg(cr):
    """
    Receives Cursor as parameter.
    Return array with paramenter ready to be used in call to psql command.
    Also it ensures that PGPASSWORD is an Environmental Variable,
    if this is not ensured psql command fails.
    """
    env_db_pass = os.environ.get('PGPASSWORD')  # Ensure PGPASSWORD
    if not env_db_pass:  # PGPASSWORD is not an environmental variable, set it
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
    def import_914_file(self, out_path, files, province):
        _logger.info('[JUJUY] Inicio de importacion')
        dsn_pg_splitted = get_dsn_pg(self.env.cr)


        _logger.info('[JUJUY] Files extracted: ' + str(len(files)))
        if len(files) != 1:
            raise ValidationError(
                _("Expected only one file compressed, got: %d") %
                len(files))

        # Corregimos porque los craneos de AGIP hacen mal el arhivo,
        # metiendo ; donde no deberian ir
        txt_path = self.correct_padron_file(files[0])
        dbname = self.env.cr.dbname
        cursor = registry(dbname).cursor()  # Get a new cursor
        try:
            _logger.info('[JUJUY] Creando tabla temporal')
            create_q = """
            CREATE TABLE temp_import(
            vat varchar(32),
            period varchar(6),
            percentage_perception varchar(10),
            percentage_retention varchar(10),
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

        _logger.info('[AGIP] Copiando del csv a tabla temporal')
        psql_args_list = [
            "psql",
            "--command=\copy temp_import(create_date,from_date,to_date,vat,multilateral,u1,u2,percentage_perception,percentage_retention,group_per,group_ret,name_partner) FROM " + txt_path + " WITH DELIMITER ';' NULL '' CSV QUOTE E'\b' ENCODING 'latin1'"  # noqa
        ]
        psql_args_list[1:1] = dsn_pg_splitted
        retcode = call(psql_args_list, stderr=STDOUT)
        assert retcode == 0, \
            "Call to psql subprocess copy command returned: " + str(retcode)

        try:
            # TODO: Creacion de los grupos de retenciones y percepciones
            _logger.info('[JUJUY] Verificando grupos')

            _logger.info('[JUJUY] Copiando de tabla temporal a definitiva')
            query = """
            INSERT INTO padron_jujuy_percentages
            (create_uid, write_date, write_uid,
            period, percentage_perception, percentage_retention,
            vat)
            SELECT 1 as create_uid,
            current_date,
            1,
            period(period, 'YYYYMM'),
            to_number(percentage_perception, '999.99')/100,
            to_number(percentage_retention, '999.99')/100,
            vat
            """
            cursor.execute("DELETE FROM padron_jujuy_percentages")
            cursor.execute(query)
            cursor.execute("DROP TABLE IF EXISTS temp_import")
        except Exception:
            cursor.rollback()
            _logger.warning('[JUJUY] ERROR: Rollback')
        else:
            # Mass Update
            mass_wiz_obj = self.env['padron.mass.update']
            wiz = mass_wiz_obj.create({
                'arba': False,
                'agip': False,
            })
            # TODO
            wiz.action_update(province)

            cursor.commit()
            _logger.info('[JUJUY] SUCCESS: Fin de carga de padron de jujuy')

        finally:
            rmtree(out_path)  # Delete temp folder
            cursor.close()
        return True
