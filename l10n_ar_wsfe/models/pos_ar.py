##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'pos.ar'

    fcred_is_fce_emitter = fields.Boolean(string='FCE Emitter?', default=False)

    @api.constrains('fcred_is_fce_emitter', 'shop_id')
    def _check_no_more_than_one_pos_fce_per_company(self):
        if self.fcred_is_fce_emitter:
            pos = self.env['pos.ar'].search_count([
                ('shop_id', '=', self.shop_id.id),
                ('fcred_is_fce_emitter', '=', True)
            ])
            if pos > 1:
                raise ValidationError(
                    _("You are not allowed to have more than one PoS per shop with FCE Enabled. %s") % self.shop_id)
