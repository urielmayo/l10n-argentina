##############################################################################
#   Copyright (c) 2022 Eynes (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models, _


class ReasonRejectedCheck(models.Model):
    _name = "reason.rejected.check"
    _description = "Reasons for rejected checks"

    name = fields.Char(string='Reason')
    type = fields.Selection([('rejected', 'Rejected'), ('returned', 'Returned')], string='Type')
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
