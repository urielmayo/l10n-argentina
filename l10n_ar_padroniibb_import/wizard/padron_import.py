##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

import logging
import os
import shlex
import tempfile
import re
import patoolib
from base64 import b64decode
from io import BytesIO
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from tempfile import mkdtemp
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

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

TYPE_FILES_DEFAULT = {
    "901": "zip",
    "902": "zip",
    "914": "excel",
    "924": "text",
}

class PadronImportFiles(models.Model):
    _name = "padron.import.files"

    wiz_id = fields.Many2one("padron.import", string="Wizard")
    file = fields.Binary(string="File", help="File to import")
    file_name = fields.Char(string="File Name")


class PadronImport(models.Model):
    _name = "padron.import"
    _description = "Importer of padron file"

    data_compressed = fields.Binary(string="Zip or Rar", help="File to import")
    data_files = fields.One2many("padron.import.files", "wiz_id", string="Files")
    province_id = fields.Many2one("res.country.state", string="Province", required=True)
    type_file = fields.Selection(
        [("excel", "Excel"), ("text", "Text"), ("zip", "Zip"), ("rar", "Rar")],
        string="Type of File",
        required=True,
    )
    def onchange_province(self, province_id):
        if not province_id:
            return False

        res_state_obj = self.pool["res.country.state"]
        province = res_state_obj.browse(province_id)
        jur_code = province.jurisdiction_code

        if not jur_code:
            raise NameError(
                _("Error"),
                _("The Province does not have a Jurisdiccion Code"),
            )
        func_name = "import_" + jur_code + "_file"

        if not hasattr(self, func_name):
            raise ValueError(
                _("Support Error"),
                _("The Province does not have support to import the Padron"),
            )

        return {"value": {"type_file": TYPE_FILES_DEFAULT.get(jur_code, "")}}


    @api.model
    def create_temporary_table(self):
        cursor = self.env.cr
        try:
            create_q = """
            CREATE TABLE temp_import(
                regimen varchar(2),
                create_date varchar(8),
                from_date varchar(8),
                to_date varchar(8),
                vat varchar(32),
                multilateral varchar(2),
                u1 varchar,
                u2 varchar,
                percentage varchar(10),
                u3 varchar,
                u4 varchar
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
        return True



    def correct_padron_file(self, filename):
        exp_reg = "^((\d+;){4}(\w;){3}([\d,]+;){4})(.*)$"
        regex = re.compile(exp_reg)
        new_file_path = tempfile.mkstemp()[1]
        with open(filename, "r", encoding='latin1') as old_file:
            with open(new_file_path, "w", encoding='latin1') as new_file:
                for line in old_file.readlines():
                    reg = regex.match(line)
                    if not reg:
                        _logger.info("[AGIP] Linea de archivo ignorada: %s" % line)
                        continue
                    newline = reg.groups()[0]
                    new_file.write(newline)
                    new_file.write("\n")
        return new_file_path

    def extract_file(self, out_path, data_compressed):
        decoded = b64decode(data_compressed)
        file_like = BytesIO(decoded)
        files_extracted = []

        if is_rarfile(file_like):
            is_rar = True
            z = RarFile(file_like)
            os.system("mkdir -p " + out_path)

            with open(out_path + "f.rar", "wb") as f:
                f.write(decoded)
            patoolib.extract_archive(out_path + "f.rar",  program='rar', outdir="/tmp")
            _logger.info("Rarfile type")
        elif is_zipfile(file_like):
            is_rar = False
            z = ZipFile(file_like)
            _logger.info("Zipfile type")
        else:
            # TODO: Deberiamos hacer un raise de otro tipo de excepcion
            raise TypeError(
                _("Extract Error"),
                _(
                    "Format of compressed file not recognized, \
                  please check if it is the correct file."
                ),
            )

        for name in z.namelist():
            if not is_rar:
                z.extract(name, out_path)
            files_extracted.append(out_path + "/" + name)
        return files_extracted

    @api.model
    def create_tmp_file(self, out_path, data_files):
        files_path = []
        for rec_data in data_files:
            file = b64decode(rec_data.file)
            file = file.decode()
            file_name = rec_data.file_name
            file_path = out_path + "/" + file_name

            with open(file_path, "w+") as f:
                f.write(file)

            files_path.append(file_path)

        return files_path

    @api.model
    def import_file(self, archivo):
        record = self.browse(archivo)
        type_file = record.type_file
        province = record.province_id
        _logger.info("Inicio de importacion")
        out_path = mkdtemp()
        if record.data_compressed or record.data_files:
            if not province:
                raise ValueError(_("Error"), _("Province is not set."))
            if not province.jurisdiction_code:
                raise ValueError(
                    _("Error"), _("Province not have set Jurisdiction Code.")
                )
            out_path = mkdtemp()  # Directorio temporal
            if type_file in ("zip", "rar"):
                data = record.data_compressed
                files = self.extract_file(out_path, data)

            elif type_file in ("text", "excel"):
                data_files = record.data_files
                files = self.create_tmp_file(out_path, data_files)

            msg = (
                "["
                + province.name
                + "]"
                + " file from "
                + province.name
                + " is loaded: START"
            )
            _logger.info(msg)

            if province.jurisdiction_code == "901":
                func_name = "import_agip_file"
            elif province.jurisdiction_code == "902":
                func_name = "import_arba_file"
            else:
                code = province.jurisdiction_code
                func_name = "import_" + code + "_file"

            function_import = getattr(self, func_name)
            function_import(out_path, files, province)

        return True
