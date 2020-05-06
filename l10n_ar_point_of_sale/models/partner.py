##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountFiscalPosition(models.Model):
    _name = "account.fiscal.position"
    _inherit = "account.fiscal.position"
    _description = ""

    denomination_id = fields.Many2one(
        'invoice.denomination',
        string='Denomination',
        required=True,
    )
    denom_supplier_id = fields.Many2one(
        'invoice.denomination',
        string='Supplier Denomination',
        required=True,
    )
    local = fields.Boolean(
        string='Local Fiscal Rules',
        default=True,
        help='Check this if it corresponds to apply local fiscal rules, '
        'like invoice number validation, etc.',
    )

    @api.constrains('name')
    def _check_duplicated_name(self):
        for fpos in self:
            srpname = str(fpos.name).strip()
            regs = self.search([
                '|',
                ('name', 'ilike', srpname),
                ('name', 'ilike', fpos.name),
                ('id', '!=', fpos.id),
            ])
            if regs:
                raise ValidationError(
                    _("The fiscal position is duplicated"))


    @api.multi
    def unlink(self):
        affected_models = [
            'sale.order',
            'purchase.order',
            'account.invoice',
        ]
        affected_models = self._hook_affected_models(affected_models)
        self._check_affected_models(affected_models)

        return super().unlink()

    @api.multi
    def _hook_affected_models(self, affected_models):
        return affected_models

    @api.multi
    def _check_affected_models(self, affected_models):
        for record in self:
            search_dict = {}
            for model in affected_models:
                searched = self.env[model].search([
                    ('fiscal_position_id', '=', record.id)
                ])
                if searched:
                    search_dict[model] = searched

            if search_dict:
                raise ValidationError(
                    _("Error\n You can not unlink a fiscal position with "
                      "associates records.\n Found this ones:\n%s\n"
                      " For fiscal position %s [ %s ]. ") %
                    (("\n").join(
                        [repr(x.sorted()) for x in search_dict.values()]),
                     record.name, record))

