##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 E-MIPS (http://www.e-mips.com.ar)
#    Copyright (c) 2018 Eynes Ingenieria del software (http://www.eynes.com.ar)
#    Copyright (c) 2018 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
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

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    renum_pick_id = fields.Many2one(
        'stock.picking',
        string='Renumerated',
        help="Reference to the new picking created for renumerate this one. You"
        " cannot delete pickings if it is done, so it is cancelled and a new on"
        "e is created, corrected and renumerated",
    )
    name_original = fields.Char(string="Original picking number")

    @api.constrains('name')
    def _check_repeat_sequence(self):
        for picking in self:
            stock_picking = self.search([
                ('name', '=', picking.name),
                ('id', '!=', picking.id)
            ])
            if stock_picking:
                raise UserError(_(
                    'There is another identical sequence'
                ))

    @api.multi
    def action_done(self):
        res = super().action_done()
        sequence_id = self.picking_type_id.sequence_transfer_id.id
        if self.picking_type_id.sequence_transfer_id.code:
            self.write({'name_original': self.name})
            name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            self.write({'name': name})

        return res


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    # Secuencia para renumerar el stock.picking luego de una transferencia
    # Es opcional, por lo tanto, puede servirnos para cuando son Delivery Orders
    # y dependen del Warehouse, por lo tanto, podemos tener para varias sucursales
    sequence_transfer_id = fields.Many2one(
        'ir.sequence',
        string='Sequence After Transfer',
    )
