##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

import logging
import re

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"
    _order = "date_invoice desc, internal_number desc"

    pos_ar_id = fields.Many2one(
        comodel_name='pos.ar',
        string='Point of Sale',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    is_debit_note = fields.Boolean(string='Debit Note', default=False)
    denomination_id = fields.Many2one(
        comodel_name='invoice.denomination',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    internal_number = fields.Char(
        string='Invoice Number',
        size=32,
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Unique number of the invoice, computed automatically when "
        "the invoice is created.",
    )
    amount_exempt = fields.Monetary(
        string='Amount Exempt',
        digits=dp.get_precision('Account'),
        store=True,
        readonly=True,
        compute='_compute_amount',
    )
    amount_no_taxed = fields.Monetary(
        string='No Taxed',
        digits=dp.get_precision('Account'),
        store=True,
        readonly=True,
        compute='_compute_amount',
    )
    amount_taxed = fields.Monetary(
        string='VAT Base',
        digits=dp.get_precision('Account'),
        store=True,
        readonly=True,
        compute='_compute_amount',
    )
    amount_other_taxed = fields.Monetary(
        string='Other Tax Base',
        digits=dp.get_precision('Account'),
        store=True,
        readonly=True,
        compute='_compute_amount',
    )
    local = fields.Boolean(string='Local', default=True)
    dst_cuit_id = fields.Many2one('dst_cuit.codes', 'Country CUIT')

    # DONE
    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('CI'),
            'in_invoice': _('SI'),
            'out_refund': _('CR'),
            'in_refund': _('SR'),
            'out_debit': _('CD'),
            'in_debit': _('SD'),
        }

        result = []
        if self.env.context.get('use_internal_number', False):
            for inv in self:
                inv_type = rtype = inv.type
                number = inv.internal_number or ''
                denom = inv.denomination_id.name or ''
                debit_note = inv.is_debit_note

                # Debit Note check
                if inv_type == 'out_invoice':
                    if debit_note:
                        rtype = 'out_debit'
                    else:
                        rtype = 'out_invoice'
                elif inv_type == 'in_invoice':
                    if debit_note:
                        rtype = 'in_debit'
                    else:
                        rtype = 'in_invoice'

                name = "{} {}{}".format(TYPES[rtype], denom, number)
                result.append((inv.id, name))
        else:
            result = super(AccountInvoice, self).name_get()

        return result

    # DONE
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if self.env.context.get('use_internal_number', False):
            if name:
                recs = self.search(
                    [('internal_number', '=', name)] + args,
                    limit=limit,
                )
            if not recs:
                recs = self.search(
                    [('internal_number', operator, name)] + args,
                    limit=limit,
                )
        else:
            return super().name_search(name, args, operator, limit=limit)

        return recs.name_get()

    @api.model
    def _update_reference(self, ref):
        # Ensure only one
        move_id = self.move_id.id
        self.env.cr.execute(
            'UPDATE account_move SET ref=%s '
            'WHERE id=%s',  # AND (ref is null OR ref = \'\')',
            (ref, move_id),
        )

        self.env.cr.execute(
            'UPDATE account_move_line SET ref=%s '
            'WHERE move_id=%s',  # AND (ref is null OR ref = \'\')',
            (ref, move_id),
        )

        self.env.cr.execute(
            'UPDATE account_analytic_line SET ref=%s '
            'FROM account_move_line '
            'WHERE account_move_line.move_id = %s '
            'AND account_analytic_line.move_id = account_move_line.id',
            (ref, move_id),
        )

        return True

    # DONE
    # Compute fields for invoice's page footer
    @api.depends(
        'invoice_line_ids.price_subtotal',
        'tax_line_ids.amount',
        'tax_line_ids.amount_rounding',
        'currency_id',
        'company_id',
        'date_invoice',
        'type',
    )
    def _compute_amount(self):
        super()._compute_amount()

        def _filter_exempt(line):
            return any(line.invoice_line_tax_ids.mapped("is_exempt"))

        def _filter_untaxed(line):
            return not line.invoice_line_tax_ids

        def _filter_taxed(line):
            taxed = line.invoice_line_tax_ids.mapped(
                lambda x: x.tax_group == 'vat' and not x.is_exempt
            )
            return any(taxed)

        def _filter_other_taxed(line):
            other_taxed = line.invoice_line_tax_ids.mapped(
                lambda x: x.tax_group != 'vat' and not x.is_exempt
            )
            return any(other_taxed)

        for inv in self:
            # Amount exempt
            # inv.amount_exempt = sum(
            #    line.price_subtotal for line in inv.invoice_line_ids
            #    if any(map(lambda x: x.is_exempt, line.invoice_line_tax_ids)),
            # )
            inv.amount_exempt = sum(
                inv.invoice_line_ids.filtered(_filter_exempt).mapped(
                    "price_subtotal")
            )

            # Amount untaxed
            # inv.amount_no_taxed = sum(
            #    line.price_subtotal for line in inv.invoice_line_ids if
            #    not line.invoice_line_tax_ids)
            inv.amount_no_taxed = sum(
                inv.invoice_line_ids.filtered(_filter_untaxed).mapped(
                    "price_subtotal")
            )

            # Amount taxed
            # inv.amount_taxed = sum(
            #    line.price_subtotal for line in inv.invoice_line_ids if
            #    any(map(lambda x: (x.tax_group == 'vat' and not x.is_exempt),
            #            line.invoice_line_tax_ids)))
            inv.amount_taxed = sum(
                inv.invoice_line_ids.filtered(_filter_taxed).mapped(
                    "price_subtotal")
            )

            # Amount for taxes other than VAT
            # inv.amount_other_taxed = sum(
            #    line.price_subtotal for line in inv.invoice_line_ids if
            #    any(map(lambda x: (x.tax_group != 'vat' and not x.is_exempt),
            #            line.invoice_line_tax_ids)))
            inv.amount_other_taxed = sum(
                inv.invoice_line_ids.filtered(_filter_other_taxed).mapped(
                    "price_subtotal")
            )

    # TODO: how do we cancel a paid Credit Note?
    @api.multi
    def action_cancel(self):
        states = (
            'draft',
            'proforma2',
            'proforma',
            'open'
        )
        allowed_states = self.env.context.get("cancel_states", states)
        for inv in self:
            if inv.type == "out_refund" and inv.state not in allowed_states:
                field_vals = self.fields_get(['state'])
                state_tags = [_(tag) for state, tag in
                              field_vals['state']['selection']
                              if state in allowed_states]
                err = _("Credit Note can only be "
                        "cancelled in these states: %s!")
                raise ValidationError(err % ', '.join(state_tags))

        return super(AccountInvoice, self).action_cancel()

    @api.multi
    def _get_dup_domain(self):
        invoice = self
        denomination_id = invoice.denomination_id
        pos_ar_id = invoice.pos_ar_id
        partner_id = invoice.partner_id or False
        if invoice.type in ('out_invoice', 'out_refund'):
            domain = [
                ('denomination_id', '=', denomination_id.id),
                ('pos_ar_id', '=', pos_ar_id.id),
                ('is_debit_note', '=', invoice.is_debit_note),
                ('internal_number', '!=', False),
                ('internal_number', '!=', ''),
                ('internal_number', '=', invoice.internal_number),
                ('type', '=', invoice.type),
            ]
        else:
            domain = [
                ('denomination_id', '=', denomination_id.id),
                ('is_debit_note', '=', invoice.is_debit_note),
                ('partner_id', '=', partner_id.id),
                ('internal_number', '!=', False),
                ('internal_number', '!=', ''),
                ('internal_number', '=', invoice.internal_number),
                ('type', '=', invoice.type),
            ]
        return domain

    # DONE
    @api.constrains('denomination_id', 'pos_ar_id', 'type',
                    'is_debit_note', 'internal_number')
    def _check_duplicate(self):
        for invoice in self:
            if invoice.type in ('in_invoice', 'in_refund'):
                local = invoice.fiscal_position_id.local

                # Si no es local, no hacemos chequeos
                if not local:
                    return

            # Si la factura no tiene seteado el numero de factura,
            # devolvemos True, porque no sabemos si estara
            # duplicada hasta que no le pongan el numero
            if not invoice.internal_number:
                return

            if invoice.type in ('out_invoice', 'out_refund'):
                domain = invoice._get_dup_domain()
                count = invoice.search_count(domain)

                if count > 1:
                    raise ValidationError(
                        _('Error! The Invoice is duplicated.'))
            else:
                domain = invoice._get_dup_domain()
                count = invoice.search_count(domain)

                if count > 1:
                    raise ValidationError(
                        _('Error! The Invoice is duplicated.'))

    # DONE
    @api.multi
    def _check_fiscal_values(self):
        for invoice in self:
            # Si es factura de cliente
            denomination = invoice.denomination_id
            if invoice.type in ('out_invoice', 'out_refund', 'out_debit'):

                if not denomination:
                    raise ValidationError(_('Denomination not set in invoice'))

                if not invoice.pos_ar_id:
                    raise ValidationError(
                        _('You have to select a Point of Sale.'))
                if denomination not in invoice.pos_ar_id.denomination_ids:
                    raise ValidationError(
                        _('Point of sale has ' +
                          'not the same denomination as the invoice.'))

                # Chequeamos que la posicion fiscal
                # y la denomination coincidan
                if invoice.fiscal_position_id.denomination_id != denomination:
                    raise ValidationError(
                        _('The invoice denomination does not ' +
                          'corresponds with this fiscal position.'))

            # Si es factura de proveedor
            else:
                if not denomination:
                    raise ValidationError(_('Denomination not set in invoice'))

                # Chequeamos que la posicion fiscal
                # y la denomination coincidan
                if invoice.fiscal_position_id.denom_supplier_id != \
                        denomination:
                    raise ValidationError(
                        _('The invoice denomination does not ' +
                          'corresponds with this fiscal position.'))

            # Chequeamos que la posicion fiscal de la
            # factura y del cliente tambien coincidan
            if invoice.fiscal_position_id != \
                    invoice.partner_id.property_account_position_id:
                raise ValidationError(
                    _('The invoice fiscal position is not ' +
                      'the same as the partner\'s fiscal position.'))

    # DONE
    @api.multi
    def get_next_invoice_number(self):
        """
        Funcion para obtener el siguiente
        numero de comprobante correspondiente
        en el sistema
        """
        self.ensure_one()
        offset = self.env.context.get('invoice_number_offset', 0)
        # Obtenemos el ultimo numero de comprobante
        # para ese pos y ese tipo de comprobante
        q = """
        SELECT MAX(TO_NUMBER(
            SUBSTRING(internal_number FROM '[0-9]{8}$'), '99999999')
            )
        FROM account_invoice
        WHERE internal_number ~ '(^[0-9]{4}|^[0-9]{5})-[0-9]{8}$'
            AND pos_ar_id = %(pos_id)s
            AND state in %(state)s
            AND type = %(type)s
            AND is_debit_note = %(is_debit_note)s
            AND denomination_id = %(denomination_id)s
        """
        q_vals = {
            'pos_id': self.pos_ar_id.id,
            'state': ('open', 'paid', 'cancel',),
            'type': self.type,
            'is_debit_note': self.is_debit_note,
            'denomination_id': self.denomination_id.id,
        }
        self.env.cr.execute(q, q_vals)
        last_number = self.env.cr.fetchone()

        # Si no devuelve resultados, es porque es el primero
        if not last_number or not last_number[0]:
            next_number = 1
        else:
            next_number = last_number[0] + 1

        return int(next_number + offset)

    # DONE
    @api.multi
    def action_move_create(self):
        if self.local:
            self._check_fiscal_values()
        self.action_number()
        res = super(AccountInvoice, self).action_move_create()
        return res

    # DONE
    @api.multi
    def action_number(self):
        for inv in self:
            invoice_vals = {}
            # si el usuario no ingreso un numero, busco
            # el ultimo y lo incremento , si no hay ultimo va 1.
            # si el usuario hizo un ingreso dejo ese numero
            internal_number = False

            # Si son de Cliente
            if inv.type in ('out_invoice', 'out_refund'):

                pos_ar = inv.pos_ar_id
                next_number = self.get_next_invoice_number()

                # Nos fijamos si el usuario dejo en
                # blanco el campo de numero de factura
                if inv.internal_number:
                    internal_number = inv.internal_number

                # Lo ponemos como en Proveedores, o sea, A0001-00000001
                if not internal_number:
                    internal_number = '%s-%08d' % (pos_ar.name, next_number)

                m = re.match('(^[0-9]{4}|^[0-9]{5})-[0-9]{8}$',
                             internal_number)
                if not m:
                    raise ValidationError(
                        _('The Invoice Number should be the format ' +
                          'XXXX[X]-XXXXXXXX'))

                # Escribimos el internal number
                invoice_vals['internal_number'] = internal_number

            # Si son de Proveedor
            else:
                if not inv.internal_number:
                    raise ValidationError(
                        _('The Invoice Number should be filled'))

                if self.local:
                    m = re.match('(^[0-9]{4}|^[0-9]{5})-[0-9]{8}$',
                                 inv.internal_number)
                    if not m:
                        raise ValidationError(
                            _('The Invoice Number should be the format ' +
                              'XXXX[X]-XXXXXXXX'))

            # Escribimos los campos necesarios de la factura
            inv.write(invoice_vals)
        return True

    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None,
               description=None, journal_id=None):

        # Devuelve los ids de las invoice modificadas
        inv_ids = super(AccountInvoice, self).\
            refund(date_invoice, date, description, journal_id)

        # Busco los puntos de venta de las invoices anteriores
        for inv in inv_ids:
            vals = {
                'pos_ar_id': self.pos_ar_id.id,
                'denomination_id': self.denomination_id.id
            }
            inv.write(vals)

        return inv_ids

    @api.model
    def _get_refund_point_of_sale_fields(self):
        return ['denomination_id', 'pos_ar_id']

    @api.model
    def _get_refund_common_fields(self):
        res = super(AccountInvoice, self)._get_refund_common_fields()
        return self._get_refund_point_of_sale_fields() + res

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        # Extend method to set local, dst_cuit_id and denomination_id fields.
        # Also set domain for pos_ar_id when invoice type is 'out_'
        res = super(AccountInvoice, self)._onchange_partner_id()
        domain = res.get('domain', {})
        if self.partner_id and self.fiscal_position_id:
            if self.type in ['in_invoice', 'in_refund']:
                self.denomination_id = self.fiscal_position_id.\
                    denom_supplier_id
            else:
                self.denomination_id = self.fiscal_position_id.denomination_id
                domain['pos_ar_id'] = [('denomination_ids', 'in',
                                        [self.denomination_id.id])]
                if not self.pos_ar_id:
                    default_pos_id = self.env.user.get_default_pos_id(self)
                    if default_pos_id:
                        self.pos_ar_id = default_pos_id
                    else:
                        sorted_pos = self.denomination_id.pos_ar_ids.sorted(
                            key=lambda x: x.priority)
                        if sorted_pos:
                            self.pos_ar_id = sorted_pos[0]

            self.local = self.fiscal_position_id.local
            self.dst_cuit_id = self.partner_id.dst_cuit_id
        else:
            self.local = True
            self.denomination_id = False
            self.pos_ar_id = False

        return res

    def _prepare_tax_line_vals(self, line, tax):
        vals = super(AccountInvoice, self)._prepare_tax_line_vals(line, tax)
        tax_browse = self.env['account.tax'].browse(tax['id'])
        vals['is_exempt'] = tax_browse.is_exempt
        vals['tax_id'] = tax['id']
        return vals


class AccountInvoiceTax(models.Model):
    _name = "account.invoice.tax"
    _inherit = "account.invoice.tax"

    tax_id = fields.Many2one(
        'account.tax', string='Account Tax', required=True)
    is_exempt = fields.Boolean(
        string='Is Exempt', readonly=True)
