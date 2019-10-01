##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from datetime import datetime

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import RedirectWarning, ValidationError, UserError
from odoo.tools import float_compare

class DatePeriod(models.Model):
    _name = 'date.period'
    _inherit = 'date.period'

    @api.multi
    def _hook_affected_models(self, affected_models):
        affected_models.append('account.payment.order')
        return super()._hook_affected_models(affected_models)
