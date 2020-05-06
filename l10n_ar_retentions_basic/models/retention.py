##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    active = fields.Boolean('Active', default=True)

    @api.multi
    def unlink(self):
        affected_models = [
            'res.partner',
            'res.partner.retention',
            'res.partner.advance.retention'
            'retention.tax.application',
            'retention.tax.line',
            'account.payment.order',
            'account.fiscal.position',
        ]
        affected_models = self._hook_affected_models(affected_models)
        self._check_affected_models(affected_models)

        return super().unlink()

    @api.multi
    def _hook_affected_models(self, affected_models):
        return affected_models

    @api.multi
    def _check_model(self, model):
        try:
            self.env[model]
            return True
        except Exception:
            return False

    @api.multi
    def _check_affected_models(self, affected_models):
        affected_models = list(filter(self._check_model, affected_models))
        for record in self:
            search_dict = {}
            for model in affected_models:
                model_obj = self.env[model]
                try:
                    model_obj.retention_id
                    name = 'retention_id'
                except AttributeError:
                    try:
                        model_obj.retention_ids
                        name = 'retention_ids'
                    except AttributeError:
                        continue
                searched = self.env[model].search([
                    (name, '=', record.id)
                ])
                if searched:
                    search_dict[model] = {
                        'description': searched._description,
                        'field_name': name,
                        'field_desc': searched._fields.get(name).string,
                    }

            if search_dict:
                msg = _('The operation cannot be completed:')
                msg += '\n'
                msg += _(
                    '- Create/update: a mandatory field is not set.\n'
                    '- Delete: another model requires the record being '
                    'deleted. If possible, archive it instead.'
                )
                msg += '\n\n'
                for key in search_dict.keys():
                    msg += '{} {} ({}), {} {} ({})\n'.format(
                        _('Model:'), search_dict[key]['description'], key,
                        _('Field:'), search_dict[key]['field_desc'],
                        search_dict[key]['field_name'],
                    )
                raise ValidationError(msg)
