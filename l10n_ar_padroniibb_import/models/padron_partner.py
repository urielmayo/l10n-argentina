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

from odoo import models


class res_partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    def _get_situation_iibb(self, cr, uid, province, partner, context=None):
        padron_obj = self.pool["padron.padron"]
        sit_iibb = super(res_partner, self)._get_situation_iibb(
            cr, uid, province, partner, context=context
        )

        if not sit_iibb:
            vat = partner.vat or False
            if province and vat:
                vals = padron_obj.get_padron_vals(
                    cr, uid, vat, province.id, context=context
                )
                sit_iibb = vals and vals["sit_iibb"] or False

        return sit_iibb

    def _get_perceptions_to_apply(self, cr, uid, partner_id, context=None):
        padron_obj = self.pool["padron.padron"]
        perceptions = super(res_partner, self)._get_perceptions_to_apply(
            cr, uid, partner_id, context=context
        )

        # Si viene con alicuota -1 se la busca en el padron
        # y si esta se le carga el porcentaje que figure ahi.

        partner = self.browse(cr, uid, partner_id, context)
        for key, perception in perceptions.items():

            if perception["percent"] == -1:
                vat = partner.vat
                province = perception["perception"].state_id
                code = province.jurisdiction_code

                # Se busca si hay una funcion especial
                # para traer los valores del padron por provincia
                func_name = "get_padron_vals_" + str(code)
                if hasattr(padron_obj, func_name):
                    func = getattr(padron_obj, func_name)
                    vals = func(cr, uid, vat, context=context)
                else:
                    vals = padron_obj.get_padron_vals(
                        cr, uid, vat, province.id, context=context
                    )

                if vals:
                    perception["percent"] = vals["percentage_perception"]
                    perceptions[key].update(perception)

        # Actualizamos el diccionario de percepciones
        return perceptions

    def _get_retentions_to_apply(self, cr, uid, partner_id, context=None):
        padron_obj = self.pool["padron.padron"]
        retentions = super(res_partner, self)._get_retentions_to_apply(
            cr, uid, partner_id, context=context
        )

        # Si viene con alicuota -1 se la busca en el padron
        # y si esta se le carga el porcentaje que figure ahi.

        partner = self.browse(cr, uid, partner_id, context)
        for key, retention in retentions.items():

            if retention["percent"] == -1:
                vat = partner.vat
                province = retention["retention"].state_id
                code = province.jurisdiction_code

                # Se busca si hay una funcion especial
                # para traer los valores del padron por provincia
                func_name = "get_padron_vals_" + str(code)
                if hasattr(padron_obj, func_name):
                    func = getattr(padron_obj, func_name)
                    vals = func(cr, uid, vat, context=context)
                else:
                    vals = padron_obj.get_padron_vals(
                        cr, uid, vat, province.id, context=context
                    )

                if vals:
                    retention["percent"] = vals["percentage_retention"]
                    retentions[key].update(retention)

        # Actualizamos el diccionario de retenciones
        return retentions
