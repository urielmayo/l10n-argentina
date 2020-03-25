##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import fields, models


class PerceptionPerception(models.Model):
    _inherit = 'perception.perception'

    is_bank_settlement = fields.Boolean('Is Bank Settlement')
