# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
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

from openerp.osv import osv, fields
from openerp import api

class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"

    _columns = {
        'renum_pick_id' : fields.many2one('stock.picking', 'Renumerated', help="Reference to the new picking created for renumerate this one. You cannot delete pickings if it is done, so it is cancelled and a new one is created, corrected and renumerated"),
    }


    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):

        res = super(stock_picking, self).do_transfer(cr, uid, picking_ids, context)
        for picking in self.browse(cr, uid, picking_ids, context=context):
            ptype_id = picking.picking_type_id.id
            sequence_id = self.pool.get('stock.picking.type').browse(cr, uid, ptype_id, context=context).sequence_transfer_id.id

            if sequence_id:
                name = self.pool.get('ir.sequence').get_id(cr, uid, sequence_id, 'id', context=context)
                self.write(cr, uid, picking.id, {'name': name}, context)

        return res
 
stock_picking()

class stock_picking_type(osv.osv):
    _name = "stock.picking.type"
    _inherit = "stock.picking.type"


    # Secuencia para renumerar el stock.picking luego de una transferencia
    # Es opcional, por lo tanto, puede servirnos para cuando son Delivery Orders
    # y dependen del Warehouse, por lo tanto, podemos tener para varias sucursales
    _columns = {
        'sequence_transfer_id': fields.many2one('ir.sequence', 'Sequence After Transfer', required=False),
    }

stock_picking_type()
