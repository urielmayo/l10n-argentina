##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DatePeriod(models.Model):
    _name = 'date.period'
    _description = 'Date Period (L10N AR)'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", size=7, required=True)
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
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
        compute="_compute_period_state",
        default='open',
        copy=False,
        store=True,
        track_visibility='onchange',
    )
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='date_period_journal_rel',
        column1='close_period_id',
        column2='journal_id',
        string='Journals',
    )

    @api.depends('journal_ids')
    def _compute_period_state(self):
        # Count all active journals
        active_journal_qry = """
        SELECT COUNT(*) FROM account_journal WHERE active = false
        """
        self.env.cr.execute(active_journal_qry)
        total_active_journal = self.env.cr.fetchone()[0]

        period_journal_qry = """
        SELECT COUNT(*)
        FROM date_period_journal_rel AS rel
        LEFT JOIN account_journal AS aj
            ON rel.journal_id = aj.id
        WHERE aj.active = false
            AND rel.close_period_id = %s
        """

        for dp in self:
            self.env.cr.execute(period_journal_qry, (dp.id,))
            related_journal_qty = self.env.cr.fetchone()[0]
            if related_journal_qty:
                if related_journal_qty == total_active_journal:
                    dp.period_state = 'closed'
                else:
                    dp.period_state = 'partial'
            else:
                dp.period_state = 'open'

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

    def _prepare_period_data(self, period_date):
        period_code = period_date.strftime("%m/%Y")
        first_day = period_date + relativedelta(day=1)
        last_day = period_date + relativedelta(
            day=1,
            months=+1,
            days=-1,
        )

        return {
            'name': period_code,
            'code': period_code,
            'date_from': first_day,
            'date_to': last_day,
        }

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

    def create_period(self, p_date):
        for month_nbr in range(1, 13):
            period_date = p_date + relativedelta(month=month_nbr)
            period = self.search_period_on_date(period_date)
            if not period:
                period_data = self._prepare_period_data(
                    period_date,
                )
                period = self.create(period_data)

            # Return the period for the date that was passed as argument
            if p_date.month == month_nbr:
                intended_period = period

        return intended_period

    def _get_period(self, period_date):
        """Search for period on date ``period_date``. If we don't find it we create it."""

        # Search for period, if we don't find it we create it
        period = self.search_period_on_date(period_date)
        if not period:
            period = self.create_period(period_date)

        return period
