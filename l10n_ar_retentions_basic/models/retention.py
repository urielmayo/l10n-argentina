##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields


class RetentionRetention(models.Model):
    """
    Object that define the retentions available for use.

    Set available retentions. retention.tax objects applied
    to a voucher are created based on retention.retention objects.
    This object also provides the configuration to generate retention.tax
    objects with data like amount, certificate number, etc.
    """
    _name = "retention.retention"
    _description = "Retention Configuration"

    # TODO: Maybe it would be better to erase this object
    # and add fields "jurisdiccion" and "state_id" to account.tax
    name = fields.Char(
        string='Retention',
        required=True,
        size=64,
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        required=True,
        help="Tax configuration for this retention",
    )
    type_tax_use = fields.Selection(
        string='Tax Application',
        related='tax_id.type_tax_use',
        readonly=True,
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State/Province',
        domain="[('country_id','=','Argentina')]",
    )
    type = fields.Selection([
            ('vat', 'VAT'),
            ('gross_income', 'Gross Income'),
            ('profit', 'Profit'),
            ('other', 'Other'),
        ],
        required=True,
    )

    jurisdiccion = fields.Selection([
            ('nacional', 'Nacional'),
            ('provincial', 'Provincial'),
            ('municipal', 'Municipal'),
        ],
        default='nacional',
    )
