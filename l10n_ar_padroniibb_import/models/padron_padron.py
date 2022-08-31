# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
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

from odoo import fields, models


class PadronPadron(models.Model):
    """
    This model represent the unification of padrons
    """

    _name = "padron.padron"
    _description = "Definition of Padron"

    name_partner = fields.text("Company name")
    province_id = fields.many2one("res.country.state", string="Province", readonly=True)
    jurisdiction_code = fields.related(
        "province_id", "jurisdiction_code", type="char", string="Jurisdiction Code"
    )
    from_date = fields.date("From date", readonly=True)
    to_date = fields.date("To date", readonly=True)
    vat = fields.char("Vat", size=15, select=1, readonly=True)
    percentage_perception = fields.float(
        digits=(16, 4), string="Percentage of perception"
    )
    percentage_retention = fields.float(
        digits=(16, 4), string="Percentage of retention"
    )
    coeficient = fields.float(digits=(16, 4), string="Coeficient")
    sit_iibb = fields.selection(
        [
            ("1", "Local"),
            ("2", "Convenio Multilateral"),
            ("4", "No Inscripto"),
            ("5", "Regimen Simplificado"),
        ],
        string="Situation of IIBB",
    )

    _defaults = {
        "percentage_perception": 0.0,
        "percentage_retention": 0.0,
        "coeficient": 0.0,
        "sit_iibb": "4",
    }

    _sql_constraints = [
        (
            "unique_province_vat",
            "UNIQUE (province_id,vat)",
            "You can not have two lines whit the same province and vat!",
        )
    ]

    def get_padron_vals(self, cr, uid, vat, province_id, context=None):
        """
        Match vat and province in padron

        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param vat: vat of partner
        @param province_id: ID of province
        @param context: A standard dictionary

        :return: Dictionary whit vals of padron

        """
        record_id = self.search(
            cr,
            uid,
            [("province_id", "=", province_id), ("vat", "=", vat)],
            context=context,
        )

        record_id = record_id and record_id[0] or []
        if record_id:
            vals = self.copy_data(cr, uid, record_id, context=context)
        else:
            vals = {}

        return vals

    def get_padron_vals_924(self, cr, uid, vat, context=None):
        """
        -En Tucuman si la situacion es de Convenio Multilateral entonces
         la alicuota se reduce un 50%.
        -Si tiene un coeficiente distinto de 0, entonces
         la alicuota se la multiplica por ese coeficiente

        Match vat and province in padron

        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param vat: vat of partner
        @param context: A standard dictionary

        :return: Dictionary whit modificate vals of padron

        """
        res_state_obj = self.pool["res.country.state"]
        province_id = res_state_obj.search(cr, uid, [("jurisdiction_code", "=", 924)])[
            0
        ]

        vals = self.get_padron_vals(cr, uid, vat, province_id, context=context)

        if vals and vals["sit_iibb"] == "2":
            vals["percentage_perception"] *= 0.5

        if vals and vals["coeficient"] != 0.0:
            vals["percentage_perception"] *= vals["coeficient"]

        return vals


class res_country_state(models.Model):
    _name = "res.country.state"
    _inherit = "res.country.state"

    jurisdiction_code = fields.char(string="Jurisdiction Code", size=15)
