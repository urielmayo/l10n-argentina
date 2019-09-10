##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

#import logging

from odoo import _, api, models
from odoo.exceptions import UserError

#_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def _get_pos_ar(self, denom):
        pos_ar_obj = self.env['pos.ar']
        res_pos = self.env.user.get_default_pos_id(self)
        if not res_pos:
            res_pos = pos_ar_obj.search(
                [
                    ('shop_id', '=', self.warehouse_id.id),
                    ('denomination_ids', 'in', denom.id),
                ],
                order='priority',
                limit=1,
            )

        if not len(res_pos):
            err = _(
                'Error!\nYou need to set up a Shop and/or a Fiscal Position'
            )
            raise UserError(err)

        return res_pos

    @api.model
    def _prepare_invoice(self):
        fpos_obj = self.env['account.fiscal.position']
        res = super()._prepare_invoice()

        fiscal_position = res['fiscal_position_id']
        if not fiscal_position:
            err = _(
                'Error\nCheck the Fiscal Position Configuration. Order[#%s] %s'
            )
            raise UserError(err % (self.id, self.name))

        fiscal_position = fpos_obj.browse(fiscal_position)
        denom = fiscal_position.denomination_id

        pos_ar = self._get_pos_ar(denom)
        vals = {'denomination_id': denom.id, 'pos_ar_id': pos_ar.id}
        res.update(vals)
        return res
