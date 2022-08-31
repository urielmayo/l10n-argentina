# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 E-MIPS (http://www.e-mips.com.ar)
#    Copyright (c) 2014 Eynes (http://www.eynes.com.ar)
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import os
import shlex
from zipfile import ZipFile, is_zipfile
from tempfile import mkdtemp
from base64 import b64decode
from io import StringIO
from odoo import _, fields, models
from odoo.tools import config
from odoo.exceptions import ValidationError, Warning


_logger = logging.getLogger(__name__)

try:
    from rarfile import RarFile, is_rarfile
except (ImportError, IOError) as err:
    _logger.warning(err)


def get_dsn_pg(cr):
    """
    Receives Cursor as parameter.
    Return array with paramenter ready to be used in call to psql command.
    Also it ensures that PGPASSWORD is an Environmental Variable,
    if this is not ensured psql command fails.
    """
    env_db_pass = os.environ.get("PGPASSWORD")  # Ensure PGPASSWORD
    if not env_db_pass:  # PGPASSWORD is not an environmental variable, set it
        db_password = config.get("db_password")
        os.environ["PGPASSWORD"] = db_password
    db_name = config.get("db_name", cr.dbname)
    if not db_name:
        db_name = cr.dbname
    db_port = config.get("db_port")
    if not db_port:
        db_port = 5432
    db_user = config.get("db_user")
    assert db_user is not None, "db_user must be set in config file"
    db_host = config.get("db_host")
    if not db_host:
        db_host = "localhost"
    res_string = "--dbname={0} --host={1} --username={2} --port={3}".format(
        db_name, db_host, db_user, db_port
    )
    res_list = shlex.split(res_string)
    return res_list


TYPE_FILES_DEFAULT = {
    "901": "zip",
    "902": "zip",
    "914": "excel",
    "924": "text",
}


class PadronImportFiles(models.TransientModel):
    _name = "padron.import.files"

    wiz_id = fields.Many2one("padron.import.padron", string="Wizard")
    file = fields.Binary(string="File", help="File to import")
    file_name = fields.Char(string="File Name")


class PadronImportPadron(models.TransientModel):
    _name = "padron.import.padron"
    _description = "Importer of padron file"

    data_compressed = fields.Binary(string="Zip or Rar", help="File to import")
    data_files = fields.One2many("padron.import.files", "wiz_id", string="Files")
    province_id = fields.Many2one("res.country.state", string="Province")
    type_file = fields.Selection(
        [("excel", "Excel"), ("text", "Text"), ("zip", "Zip"), ("rar", "Rar")],
        string="Type of File",
    )

    def onchange_province(self, cr, uid, ids, province_id, context=None):
        if not province_id:
            return False

        res_state_obj = self.pool["res.country.state"]
        province = res_state_obj.browse(cr, uid, province_id, context=context)
        jur_code = province.jurisdiction_code

        if not jur_code:
            raise Exception("The Province does not have a Jurisdiccion Code")

        func_name = "import_" + jur_code + "_file"
        if not hasattr(self, func_name):
            raise Exception("The Province does not have support to import the Padron")

        return {"value": {"type_file": TYPE_FILES_DEFAULT.get(jur_code, "")}}

    def extract_file(self, out_path, data_compressed, context=None):
        """
        Extract file using Zipfile or RarfileL

        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param out_path: path of temp folder
        @param data_compressed: files compressed
        @param context: A standard dictionary

        :return: a list with the path of the created files

        """
        decoded = b64decode(data_compressed)
        file_like = StringIO(decoded)
        files_extracted = []

        if is_rarfile(file_like):
            z = RarFile(file_like)
        elif is_zipfile(file_like):
            z = ZipFile(file_like)
        else:
            # TODO: Deberiamos hacer un raise de otro tipo de excepcion
            raise Exception(
                "Format of compressed file not recognized, please check if it is the correct file."
            )

        for name in z.namelist():
            z.extract(name, out_path)
            files_extracted.append(out_path + "/" + name)

        return files_extracted

    def create_tmp_file(self, cr, uid, out_path, data_files):
        """
        Convert data to temporaly files

        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param out_path: path of temp folder
        @param data_files: A list whit record of model padron.import.files
        @param context: A standard dictionary

        :return: a list with the path of the created files

        """
        files_path = []
        for rec_data in data_files:
            file = b64decode(rec_data.file)
            file_name = rec_data.file_name
            file_path = out_path + "/" + file_name

            with open(file_path, "w+") as f:
                f.write(file)

            files_path.append(file_path)

        return files_path

    def import_file(self, context=None):
        """
        Import padron of uploaded files

        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        """

        record = self.browse()
        type_file = record.type_file
        province = record.province_id

        if record.data_compressed or record.data_files:

            if not province:
                raise ValueError("Province is not set.")

            if not province.jurisdiction_code:
                raise ValueError("Province not have set Jurisdiction Code.")

            out_path = mkdtemp()  # Directorio temporal

            if type_file in ("zip", "rar"):
                data = record.data_crompressed
                files = self.extract_file(out_path, data, context=context)

            elif type_file in ("text", "excel"):
                data_files = record.data_files
                files = self.create_tmp_file(out_path, data_files, context=context)

            msg = (
                "["
                + province.name
                + "]"
                + " file from "
                + province.name
                + " is loaded: START"
            )

            _logger.info(msg)

            # Las funciones de importacion de cada jurisdiccion
            # tienen un patron para el nombre. Se compone
            # de un cierto prefijo generico y el codigo de jurisdiccion
            # y un subfijo
            func_name = "import_" + province.jurisdiction_code + "_file"
            function_import = getattr(self, func_name)
            function_import(out_path, files, province, context=context)
        return True
