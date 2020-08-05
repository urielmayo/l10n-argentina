##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PerceptionPerception(models.Model):
    _name = "perception.perception"
    _description = "Perception Configuration"
    """
    Object that define the perceptions available for use.

    Set available perceptions. perception.tax objects used
    in account invoices are created based on perception.perception objects.
    This model also creates account.invoice.tax objects used as
    perceptions in the invoices from both clients and providers and allowing
    to create the corresponding moves. This object also provides
    the configuration to generate perception.tax and account.invoice.tax
    objects with data like amount, certificate number, etc.
    """

    name = fields.Char(
        string='Perception',
        required=True,
        size=64,
    )
    tax_id = fields.Many2one(
        'account.tax',
        string='Tax',
        required=True,
        help="Tax configuration for this perception",
    )
    type_tax_use = fields.Selection([
            ('sale', 'Sales'),
            ('purchase', 'Purchases'),
            ('none', 'None'),
        ],
        related='tax_id.type_tax_use',
        string='Tax Application',
        readonly=True,
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='State/Province',
    )
    type = fields.Selection([
            ('vat', 'VAT'),
            ('gross_income', 'Gross Income'),
            ('profit', 'Profit'),
            ('other', 'Other'),
        ],
        default='vat',
    )
    jurisdiccion = fields.Selection([
            ('nacional', 'Nacional'),
            ('provincial', 'Provincial'),
            ('municipal', 'Municipal'),
        ],
        default='nacional',
    )
    active = fields.Boolean('Active', default=True)

    @api.multi
    def unlink(self):
        field_obj = self.env['ir.model.fields']
        fields = field_obj.search([
            ('relation', '=', 'perception.perception')
        ])
        msg = ('Can not delete the record %s '
               'because is used in %s on %s.')
        for perception in self:
            for field in fields:
                model_obj = self.env[field.model]
                if field.ttype == 'one2many':
                    if not perception[field.relation_field]:
                        continue
                elif field.ttype == 'many2many':
                    if field.relation_table:
                        cr = self.env.cr
                        select = 'SELECT * FROM'
                        where = 'WHERE perception_id = %(perception)s'
                        query = ' '.join([select, field.relation_table, where])
                        data = {
                            'perception': perception.id
                        }
                        cr.execute(query, data)
                        res = cr.fetchall()
                        if not res:
                            continue
                    else:
                        continue
                else:
                    res = model_obj.search([
                        (field.name, '=', perception.id)
                    ])
                    if not res:
                        continue
                raise UserError(_(msg % (
                    perception.name, field.model_id.name,
                    field.field_description
                )))
        return super(PerceptionPerception, self).unlink()
