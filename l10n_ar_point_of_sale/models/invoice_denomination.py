##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import fields, models


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
