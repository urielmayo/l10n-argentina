import logging
import os
import tempfile
import re
import shlex
import calendar
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
    def import_924_file(self, out_path, files, province):

        _logger.info("[TUCUMAN] Inicio de importacion")
        dsn_pg_splitted = get_dsn_pg(self.env.cr)  # Configuracion base de datos

        _logger.info("[TUCUMAN] Files extracted: " + str(len(files)))
        if len(files) != 1:
            raise ValidationError(
                _("Expected one files, get: %d") % len(files)
            )

        # Obtengo un nuevo cursor a partir del cursor existente
        dbname = self.env.cr.dbname
        cursor = registry(dbname).cursor()

        # Se eliminan todos los registros de esta jurisdiccion
        # para volver a cargarlos
        #cursor.execute(
        #    "DELETE FROM padron_padron WHERE province_id = %s", (province.id,))

        for file_name in files:


            if "ACREDITAN" in file_name:
                _logger.info('[TUCUMAN] ACREDITAN - Inicio de carga ')
                txt_path = self.correct_padron_tucuman(file_name)

                self.create_temp_table_acreditan(cursor)
                _logger.info('[TUCUMAN] ACREDITAN - Copiando a tabla temporal')
                psql_args_list = [
                    "psql",
                    "--command=\copy temp_import(vat,u1,sit_iibb,from_date,to_date,percentage_perception) FROM " + txt_path + " WITH DELIMITER ';'  NULL '' CSV QUOTE E'\b' ENCODING 'latin1'"  # noqa
                ]
                psql_args_list[1:1] = dsn_pg_splitted
                retcode = call(psql_args_list, stderr=STDOUT)
                assert retcode == 0, 'Call expected return 0'

                try:
                    query = """ INSERT INTO padron_tucuman_acreditan
                        (create_uid, create_date, write_date, write_uid,
                        from_date, to_date, percentage_perception, vat, sit_iibb)
                    SELECT  1 as create_uid,
                        to_date(create_date, 'DDMMYYYY'),
                        current_date,
                        1,
                        to_date(from_date, 'YYYYMMDD'),
                        to_date(to_date, 'YYYYMMDD'),
                        to_number(percentage_perception, '999.9999'),
                        vat,
                        CASE WHEN sit_iibb = 'CM' THEN True
                             ELSE False
                        END AS sit_iibb
                    FROM temp_import
            """


                    cursor.execute("DELETE FROM padron_tucuman_acreditan")
                    _logger.info('[TUCUMAN] Acreditan - Copiando a tabla definitiva')
                    cursor.execute(query)
                    cursor.execute("DROP TABLE IF EXISTS temp_import")
                except Exception:
                    cursor.rollback()
                    _logger.warning('[TUCUMAN]ERROR: Rollback')
                else:
                    cursor.commit()
                    _logger.info('[TUCUMAN]SUCCESS: Fin de carga de acreditan')

            if "archivocoef" in file_name:
                _logger.info('[TUCUMAN] COEFICIENTE - Inicio de carga ')
                txt_path = self.correct_coeficient_tucuman(file_name)
                self.create_temp_table_coeficiente(cursor)
                _logger.info('[TUCUMAN] COEFICIENTE - Copiando a tabla temporal')
                psql_args_list = [
                    "psql",
                    "--command=\copy temp_import(vat,u1,coeficiente,from_date,to_date,percentage_perception) FROM " + txt_path + " WITH DELIMITER ';' NULL '' CSV QUOTE E'\b' ENCODING 'latin1'"  # noqa
                ]
                psql_args_list[1:1] = dsn_pg_splitted
                retcode = call(psql_args_list, stderr=STDOUT)
                assert retcode == 0, 'Call expected return 0'

                try:
                    query = """ INSERT INTO padron_tucuman_coeficiente
                    (create_uid, create_date, write_date, write_uid,
                    from_date, to_date, coeficiente, percentage_perception, vat)
                    SELECT  1 as create_uid,
                        current_date,
                        current_date,
                        1,
                        to_date(from_date, 'YYYYMMDD'),
                        to_date(to_date, 'YYYYMMDD'),
                        to_number(coeficiente, '999.9999'),
                        to_number(percentage_perception, '999.9999'),
                        vat
                    FROM temp_import"""
                    cursor.execute("DELETE FROM padron_tucuman_coeficiente")
                    _logger.info('[TUCUMAN] Coeficiente - Copiando a tabla definitiva')
                    cursor.execute(query)
                    cursor.execute("DROP TABLE IF EXISTS temp_import")
                except Exception:
                    cursor.rollback()
                    _logger.warning('[TUCUMAN]ERROR: Rollback')
                else:
                    cursor.commit()
                    _logger.info('[TUCUMAN]SUCCESS: Fin de carga de Coeficiente')

        return True

    def create_temp_table_acreditan(self, cursor):
        """Crea una tabla temporal donde carga los datos del archivo
        para luego ser subidos a la definitiva"""
        try:
            create_q = """
            CREATE TABLE temp_import (
                create_date varchar(8),
                vat varchar(32),
                u1 varchar(8),
                sit_iibb varchar(2),
                from_date varchar(8),
                to_date varchar(8),
                percentage_perception varchar(10)
            ) """

            cursor.execute("DROP TABLE IF EXISTS temp_import")
            cursor.execute(create_q)
        except Exception:
            cursor.rollback()
            raise ValidationError(_("Could not create the temporary table with the file data"))
        else:
            cursor.commit()
        return True

    def correct_padron_tucuman(self, filename):
        """Los datos se resctructuran como
        CUIT;E;SITIIBB;DESDE;HASTA;PORCENTAJE
        """

        exp_reg = "^(\d+)(\s+)([\sa-zA-Z])(\s+)([\sa-zA-Z]{2})(\s+)(\d+)(\s+)(\d+)(.*\s)([\d.-]+)(.*)$"
        regex = re.compile(exp_reg)
        new_file_path = tempfile.mkstemp()[1]
        with open(filename, "r", encoding='latin1') as old_file:
            with open(new_file_path, "w+", encoding='latin1') as new_file:
                for line in old_file.readlines():
                    reg = regex.match(line)
                    if not reg:
                        #_logger.info("[TUCUMAN] Linea de archivo ignorada: %s" % line)
                        continue

                    """ Se modifican los datos que vienen en el archivo:
                        - El porcentaje viene escrito como "---" si esta seteado
                        "E" en su columna, se lo cambia por 0.0 si es asi.
                        - Si la columna "E" no tiene la "E" seteada viene con
                        un espacio vacio, por las dudas lo remplazo con una "None".
                    """

                    groups = list(reg.groups())
                    if groups[2] == "E":
                        groups[-2] = "0.0"
                        groups[4] = groups[4] != " " and groups[4] or "None"
                    else:
                        groups[2] = "None"

                    groups_index = [0, 2, 4, 6, 8, 10]  # Grupos requeridos
                    groups = [groups[i] for i in groups_index]

                    newline = (";").join(groups)

                    new_file.write(newline)
                    new_file.write("\n")


            return new_file_path

    def create_temp_table_coeficiente(self, cursor):
        """Crea una tabla temporal donde carga los datos del archivo
        para luego ser subidos a la definitiva"""
        try:
            create_q = """
            CREATE TABLE temp_import (
                create_date varchar(8),
                vat varchar(32),
                u1 varchar(8),
                coeficiente varchar(10),
                from_date varchar(8),
                to_date varchar(8),
                percentage_perception varchar(10)
            ) """

            cursor.execute("DROP TABLE IF EXISTS temp_import")
            cursor.execute(create_q)
        except Exception:
            cursor.rollback()
            raise ValidationError(_("Could not create the temporary table with the file data"))
        else:
            cursor.commit()
        return True

    def correct_coeficient_tucuman(self, filename):
        """Los datos se resctructuran como
        CUIT;E;COEF;DESDE;HASTA;PORCENTAJE
        """

        exp_reg = "^(\d+)(\s+)([\sa-zA-Z])(\s+)([\d.-]+)(\s+)(\d+)(.*\s)([\d.-]+)(.*)$"
        regex = re.compile(exp_reg)
        new_file_path = tempfile.mkstemp()[1]

        with open(filename, "r", encoding='latin1') as old_file:
            with open(new_file_path, "w", encoding='latin1') as new_file:
                for line in old_file.readlines():
                    reg = regex.match(line)
                    if not reg:
                        #_logger.info("Linea de archivo ignorada: %s" % line)
                        continue
                    groups = list(reg.groups())
                    if groups[2] == "E":
                        groups[4] = "0.0"
                        groups[-2] = "0.0"
                    else:
                        groups[2] = "None"

                    groups_index = [0, 2, 4, 6, 8]  # Grupos requeridos
                    groups = [groups[i] for i in groups_index]
                    date = groups[3]
                    if not date:
                        raise Exception(_("Error"), ("Date is not provide in coeficient file"))
                    year = date[0:4]
                    month = date[-2:]
                    f_day, month_range = calendar.monthrange(int(year), int(month))
                    from_date = "".join([year, month, "01"])
                    to_date = "".join([year, month, str(month_range)])
                    groups.pop(3)
                    groups[3:3] = [from_date, to_date]
                    newline = (";").join(groups)

                    new_file.write(newline)
                    new_file.write("\n")
        return new_file_path


