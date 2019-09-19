##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 E-MIPS (http://www.e-mips.com.ar)
#    Copyright (c) 2018 Eynes Ingenieria del software (http://www.eynes.com.ar)
#    Copyright (c) 2018 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
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

from odoo import _, fields, models


class CancelPickingDone(models.TransientModel):
    _name = 'cancel.picking.done'

    reason = fields.Text(string='Reason of cancellation')
    next_action = fields.Selection(
        [
            ('renumerate', 'Cancel & Create draft'),
            ('cancel', 'Cancel only'),
        ],
        string='Next Action',
        required=True,
    )

    def create_returns(self):

        # Get active picking
        active_id = self.env.context.get('active_id', False)
        active_pickings = self.env['stock.picking'].browse(active_id)

        new_picking_ids = []
        for pick in active_pickings:
            # Renumerate... clone pick
            pick_vals = {}
            if self.next_action == 'renumerate':
                new_pick = pick.copy()

                note = _('{}\nPick renumerated from {}. {}').format(
                    pick.note or '',
                    pick.name,
                    self.reason or '',
                )

                new_pick.write(
                    {
                        'note': note,
                        'origin': pick.name,
                    }
                )

                new_picking_ids.append(new_pick.id)
                pick_vals['renum_pick_id'] = new_pick.id

            # Cancel current picking and its moves
            pick_vals['state'] = 'cancel'
            pick.write(pick_vals)
            pick.move_lines.write({'state': 'cancel'})

        form = self.env.ref('stock.view_picking_form')
        if new_picking_ids:
            if len(new_picking_ids) == 1:
                return {
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window',
                    'views': [(form.id, 'form')],
                    'view_id': form.id,
                    'res_id': new_picking_ids[0],
                }
            else:
                tree = self.env.ref('stock.action_picking_tree')
                return {
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window',
                    'views': [(tree.id, 'tree'), (form.id, 'form')],
                    'view_id': False,
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', new_picking_ids)],
                }
