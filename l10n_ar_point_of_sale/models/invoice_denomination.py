##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class InvoiceDenomination(models.Model):

    _name = "invoice.denomination"
    _description = "Denomination for Invoices"

    # Columns
    name = fields.Selection(
        [
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('M', 'M'),
            ('X', 'X'),
            ('OC', 'OC'),  # Other receipts
            ('ANA', 'ANA'),
            ('E', 'E'),
        ],
        string="Denomination",
    )
    desc = fields.Char(string="Description", required=True, size=100)
    vat_discriminated = fields.Boolean(
        string="Vat Discriminated in Invoices",
        default=False,
        help="If True, the vat will be discriminated at invoice report.",
    )
    pos_ar_ids = fields.Many2many(
        comodel_name='pos.ar',
        relation='posar_denomination_rel',
        column1='denomination_id',
        column2='pos_ar_id',
        string='Points of Sale',
        readonly=True,
    )

    @api.constrains('name')
    def _check_duplicate(self):
        for denom in self:
            regs = self.search([
                ('name', '=', denom.name),
                ('id', '!=', denom.id),
            ])
            if regs:
                raise ValidationError(
                        _("You cannot duplicate denominations"))

    @api.multi
    def unlink(self):
        affected_models = [
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
                    ('denomination_id', '=', record.id)
                ])
                if searched:
                    search_dict[model] = searched

            if search_dict:
                raise ValidationError(
                    _("Error\n You can not unlink a denomination with "
                      "associates records.\n Found this ones:\n%s\n"
                      " For denomination %s [ %s ]. ") %
                    (("\n").join(
                        [repr(x.sorted()) for x in search_dict.values()]),
                     record.name, record))

