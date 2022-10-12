import logging
import os
import shlex
from subprocess import call, STDOUT
from shutil import rmtree
from odoo import registry
from odoo import _, api, models
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
    def import_arba_file(self, out_path, files, province):
        _logger.info('[ARBA] Inicio de importacion')
        dsn_pg_splitted = get_dsn_pg(self.env.cr)


        _logger.info('[ARBA] Files extracted: ' + str(len(files)))
        if len(files) != 2:
            raise ValidationError(
                _('Expected two files compressed, got: %d') %
                len(files))

        dbname = self.env.cr.dbname
        cursor = registry(dbname).cursor()  # Get a new cursor
        for file_name in files:
            txt_path = "'" + file_name + "'"
            if 'Ret' in file_name:
                _logger.info('[ARBA] Ret - Inicio de carga ')
                # copiar a postgresql padron_arba_retention
                self.create_temporary_table()
                _logger.info('[ARBA] Ret - Copiando a tabla temporal')
                psql_args_list = [
                    "psql",
                    "--command=\copy temp_import(regimen,create_date,from_date,to_date,vat,multilateral,u1,u2,percentage,u3,u4) FROM " + txt_path + " WITH DELIMITER ';' NULL '' "  # noqa
                ]
                psql_args_list[1:1] = dsn_pg_splitted
                retcode = call(psql_args_list, stderr=STDOUT)
                assert retcode == 0, 'Call expected return 0'
                try:
                    query = """
                    INSERT INTO padron_arba_retention
                    (create_uid, create_date, write_date, write_uid,
                    vat, percentage, from_date, to_date, multilateral)
                    SELECT 1 as create_uid,
                    to_date(create_date,'DDMMYYYY'),
                    current_date,
                    1,
                    vat,
                    to_number(percentage, '999.99')/100,
                    to_date(from_date,'DDMMYYYY'),
                    to_date(to_date,'DDMMYYYY'),
                    (CASE
                        WHEN multilateral = 'C'
                        THEN True ELSE False
                    END) as multilateral
                    FROM temp_import
                    """
                    cursor.execute("DELETE FROM padron_arba_retention")
                    _logger.info('[ARBA] Ret - Copiando a tabla definitiva')
                    cursor.execute(query)
                    cursor.execute("DROP TABLE IF EXISTS temp_import")
                except Exception:
                    cursor.rollback()
                    _logger.warning('[ARBA]ERROR: Rollback')
                else:
                    cursor.commit()
                    _logger.info('[ARBA]SUCCESS: Fin de carga de retenciones')
            if 'Per' in file_name:
                self.create_temporary_table()
                _logger.info('[ARBA] Per - Copiando a tabla temporal')
                psql_args_list = [
                    "psql",
                    "--command=\copy temp_import(regimen,create_date,from_date,to_date,vat,multilateral,u1,u2,percentage,u3,u4) FROM " + txt_path + " WITH DELIMITER ';' NULL '' "  # noqa
                ]
                psql_args_list[1:1] = dsn_pg_splitted
                retcode = call(psql_args_list, stderr=STDOUT)
                assert retcode == 0, 'Call expected return 0'
                try:
                    query = """
                    INSERT INTO padron_arba_perception
                    (create_uid, create_date, write_date, write_uid,
                    vat, percentage, from_date, to_date, multilateral)
                    SELECT 1 as create_uid,
                    to_date(create_date,'DDMMYYYY'),
                    current_date,
                    1,
                    vat,
                    to_number(percentage, '999.99')/100,
                    to_date(from_date,'DDMMYYYY'),
                    to_date(to_date,'DDMMYYYY'),
                    (CASE
                        WHEN multilateral = 'C'
                        THEN True ELSE False
                    END) as multilateral
                    FROM temp_import
                    """
                    cursor.execute("DELETE FROM padron_arba_perception")
                    _logger.info('[ARBA] Per - Copiando a tabla definitiva')
                    cursor.execute(query)
                    cursor.execute("DROP TABLE IF EXISTS temp_import")
                except Exception:
                    cursor.rollback()
                    _logger.warning('[ARBA]ERROR: Rollback')
                else:
                    # Mass Update
                    mass_wiz_obj = self.env['padron.mass.update']
                    wiz = mass_wiz_obj.create({
                        'arba': True,
                        'agip': False,
                    })
                    # TODO
                    wiz.action_update(province)

                    cursor.commit()
                    _logger.info('[ARBA]SUCCESS: Fin de carga de percepciones')
        rmtree(out_path)  # Delete temp folder
        cursor.close()
        return True

