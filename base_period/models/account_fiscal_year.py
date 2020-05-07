# -*- coding: utf-8 -*-
###############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (Gaston Bertolani)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
###############################################################################

import logging

from odoo import models, api, fields, _
from odoo.osv import expression
from datetime import datetime
from odoo.exceptions import UserError, RedirectWarning
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'
    _description = "Fiscal Year"
    _order = "date_from, id"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string='Fiscal Year', required=True)
    code = fields.Char(string='Code', size=6, required=True)
    period_ids = fields.One2many('date.period', 'fiscalyear_id', 'Periods')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Status', readonly=True,
    copy=False, default='draft')

    @api.constrains('name', 'code')
    def _check_duplicated_name(self):
        for fy in self:
            fys = self.search([
                ('id', '!=', fy.id),
                '|',
                ('code', '=', fy.code),
                ('name', '=', fy.name),
            ])
            if fys:
                raise UserError(
                        _("There is other fiscal year " \
                            "with same code or name"))

    @api.multi
    def button_create_period3(self):
        return self.create_period(interval=3)

    @api.multi
    def button_create_period(self):
        return self.create_period(interval=1)


    def create_period(self, interval=1):
        period_obj = self.env['date.period']
        for fy in self:
            ds = fy.date_from
            period_obj.create({
                'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_from': ds,
                'date_to': ds,
                'special': True,
                'fiscalyear_id': fy.id,
            })
            while ds < fy.date_to:
                de = ds + relativedelta(months=interval, days=-1)

                if de > fy.date_to:
                    de = fy.date_to

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    def find(self, dt=None, exception=True):
        res = self.finds(dt, exception)
        return res

    def finds(self, dt=None, exception=True):
        ctx = self.env.context
        if not dt:
            dt = fields.Date.context_today(self)
        args = [
            ('date_from', '<=' ,dt),
            ('date_to', '>=', dt)
        ]
        if ctx.get('company_id', False):
            company_id = ctx['company_id']
        else:
            company_id = self.env.user.company_id.id
        args.append(('company_id', '=', company_id))
        fiscalyears = self.search(args)
        if not fiscalyears:
            if exception:
                action = self.env.ref('account.actions_account_fiscal_year')
                msg = _("There is no period defined for this date: "\
                        "%s.\nPlease go to Configuration/Periods and "\
                        "configure a fiscal year.") % dt
                raise RedirectWarning(msg, action.id,
                        _('Go to the configuration panel'))
            else:
                return False
        return fiscalyears

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [
                ('code', operator, name),
                ('name', operator, name)
            ]
        else:
            domain = [
                '|',
                ('code', operator, name),
                ('name', operator, name)
            ]
        fiscalyears = self.search(
                expression.AND([domain, args]), limit=limit)
        return fiscalyears.name_get()
