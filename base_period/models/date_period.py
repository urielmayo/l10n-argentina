##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF


class DatePeriod(models.Model):
    _name = 'date.period'
    _order = "date_from desc"
    _description = 'Date Period (L10N AR)'


    @api.model
    def _get_company(self):
        return self.env.user.company_id

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", size=7, required=True)
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    special = fields.Boolean(string='Opening/Closing Period',
            help="These periods can overlap.")
    invoice_ids = fields.One2many(
        comodel_name="account.invoice",
        inverse_name="period_id",
        string="Invoice",
    )
    move_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="period_id",
        string="Move",
    )
    move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="period_id",
        string="Move Line",
    )
    inventory_ids = fields.One2many(
        comodel_name="stock.inventory",
        inverse_name="period_id",
        string="Stock Inventory",
    )

    period_state = fields.Selection(
        [
            ('open', 'Open'),
            ('partial', 'Partialy Closed'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='closed',
        copy=False,
        store=True,
        compute="_compute_period_state",
        track_visibility='onchange',
    )

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='date_period_journal_rel',
        column1='close_period_id',
        column2='journal_id',
        string='Journals',
    )

    fiscalyear_id = fields.Many2one(
        'account.fiscal.year',
        string='Fiscal Year',
        required=True,
        select=True
    )

    company_id = fields.Many2one(
        'res.company',
        related='fiscalyear_id.company_id',
        string='Company',
        store=True,
        readonly=True,
        default=lambda self: self._get_company(),
    )

    @api.constrains('date_from', 'date_to')
    def _check_duration(self):
        for period in self:
            if period.date_to < period.date_from:
                raise UserError(
                    _('Error!\nThe duration of the Period(s) is/are invalid.'))
        return True

    @api.constrains('fiscalyear_id', 'special', 'company_id')
    def _check_year_limit(self):

        msg = _("Error!\nThe period is invalid. Either "\
                "some periods are overlapping or the period\'s" \
                "dates are not matching the scope of the fiscal year.")

        for period in self:
            if period.special or not period.fiscalyear_id:
                continue

            year_date_from = period.fiscalyear_id.date_from
            year_date_to = period.fiscalyear_id.date_to
            period_date_from = period.date_from
            period_date_to = period.date_to

            if year_date_to < period_date_to or \
               year_date_to < period_date_from or \
               year_date_from > period_date_from or \
               year_date_from > period_date_to:
                raise UserError(msg)

            pids = self.search([
                ('date_to', '>=', period.date_from),
                ('date_from', '<=', period.date_to),
                ('special', '=', False),
                ('id', '<>', period.id)
            ])
            for pid in pids:
                pid_company = pid.fiscalyear_id.company_id
                period_company = period.fiscalyear_id.company_id
                if period_company.id == pid_company.id:
                    raise UserError(msg)
        return True

    @api.multi
    def unlink(self):
        affected_models = [
            'account.move',
            'account.invoice',
            'stock.inventory',
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
                    ('period_id', '=', record.id)])

                if searched:
                    search_dict[model] = searched

            if search_dict:
                raise ValidationError(
                    _("Error\n You can not unlink a period with "
                      "associates records.\n Found this ones:\n%s\n"
                      " For the period %s [ %s ]. ") %
                    (("\n").join(
                        [repr(x.sorted()) for x in search_dict.values()]),
                     record.name, record))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)

        return recs.name_get()

    def search_period_on_date(self, p_date):
        """Search for date.period on date ``p_date``.

        :param p_date: datetime.date to search for.
        :return: found date.period instance or empty.
        """

        period_date = fields.Date.to_string(p_date)

        domain = [
            ('date_from', '<=', period_date),
            ('date_to', '>=', period_date)
        ]

        return self.search(domain)

    @api.model
    def _get_period(self, period_date):
        ctx = self.env.context
        ddate = period_date.strftime(DSDF)
        domain = [
            ('date_from', '<=', ddate),
            ('date_to', '>=', ddate)
        ]
        company_id = self.env.user.company_id.id
        if 'company_id' in ctx:
            company_id = ctx.get('company_id', False)
        domain.append(('company_id', '=', company_id))

        period = False
        if 'account_period_prefer_normal' in ctx:
            period = self.search(domain + [('special', '=', False)], limit=1)
        if not period:
            period = self.search(domain, limit=1)

        if not period:
            action = self.env.ref('base_period.date_period_action')
            msg = _("There is no period defined for this date: "\
                    "%s.\nPlease go to Configuration/Periods.") % period_date
            raise RedirectWarning(msg, action.id,
                    _('Go to the configuration panel'))
        return period

    @api.multi
    def _check_company_period(self, affected_models):
        for record in self:
            search_dict = {}
            for model in affected_models:
                searched = self.env[model].search([
                    ('period_id', '=', record.id)])
                if searched:
                    search_dict[model] = searched
            if search_dict:
                raise ValidationError(
                    _("Error\n You can not change the company a period with " +
                      "associates records.\n Found this ones:\n%s\n" +
                      " For the period %s [ %s ]. ") %
                    (("\n").join(
                        [repr(x.sorted()) for x in search_dict.values()]),
                     record.name, record))
        return True

    @api.multi
    def write(self, vals):
        if 'company_id' in vals:
            affected_models = [
                'account.move',
                'account.invoice',
                'stock.inventory',
            ]
            affected_models = self._hook_affected_models(affected_models)
            self._check_company_period(affected_models)
        return super(DatePeriod, self).write(vals)

    @api.model
    def get_active_journal(self):
        # Count all active journals
        active_journal_qry = """
            SELECT COUNT(*)
            FROM account_journal
            WHERE active = true
        """
        self.env.cr.execute(active_journal_qry)
        total_active_journal = self.env.cr.fetchone()[0]
        return total_active_journal

    @api.multi
    def get_close_journal(self):
        self.ensure_one()
        if isinstance(self.id, models.NewId):
            return False
        period_journal_qry = """
            SELECT COUNT(*)
            FROM date_period_journal_rel AS rel
            LEFT JOIN account_journal AS aj
                ON rel.journal_id = aj.id
            WHERE aj.active = true
                AND rel.close_period_id = %s
        """
        self.env.cr.execute(period_journal_qry, (self.id,))
        related_journal_qty = self.env.cr.fetchone()[0]
        return related_journal_qty

    @api.multi
    def get_next_state(self):
        self.ensure_one()
        all_journal_qty = self.get_active_journal()
        related_journal_qty = self.get_close_journal()
        if related_journal_qty:
            if related_journal_qty == all_journal_qty:
                period_state = 'closed'
            else:
                period_state = 'partial'
        else:
            period_state = 'open'
            if self.period_state == 'open':
                period_state = 'closed'
        return period_state

    @api.depends('journal_ids')
    def _compute_period_state(self):
        for period in self:
            next_state = period.get_next_state()
            period.period_state = next_state
