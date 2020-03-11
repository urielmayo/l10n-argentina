##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        required=True,
    )

    @api.model
    def create(self, vals):
        period_model = self.env['date.period']
        date = vals.get('date', False)
        if not date:
            date = fields.Date.context_today(self)
        period_date = fields.Date.from_string(date)
        period = period_model._get_period(period_date)
        if not vals.get('period_id', False):
            vals.update({
                'period_id': period.id
            })
        journal_id = vals.get('journal_id', self._get_default_journal())
        if not journal_id:
            return super(AccountMove, self).create(vals)

        if journal_id in period.journal_ids.ids:
            raise ValidationError(
                _("Can't create an account move on a closed period."))

        return super(AccountMove, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.env.context.get('bypass_close_date_period_check'):
            return super(AccountMoveLine, self).write(vals)

        if self.journal_id.id in self.period_id.journal_ids.ids:
            raise ValidationError(
                _("Can't edit an account move on a closed period."))

        period_model = self.env['date.period']
        date = vals.get('date', self.date)
        if not date:
            return super(AccountMove, self).write(vals)

        period_date = fields.Date.from_string(date)
        period = period_model._get_period(period_date)
        journal_id = vals.get('journal_id', self.journal_id.id)
        if isinstance(journal_id, models.BaseModel):
            journal_id = journal_id.id

        if journal_id in period.journal_ids.ids:
            raise ValidationError(
                _("Can't edit an account move to a closed period."))

        return super(AccountMove, self).write(vals)

    @api.multi
    def unlink(self):
        for move in self:
            if move.journal_id.id in move.period_id.journal_ids.ids:
                raise ValidationError(
                    _("Can't delete an account move on a closed period."))

        return super(AccountMove, self).unlink()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        related="move_id.period_id",
    )

    @api.model
    def create(self, vals):
        move_model = self.env['account.move']
        move_id = vals.get('move_id')
        if not move_id:
            return super(AccountMoveLine, self).create(vals)

        move = move_model.browse(move_id)
        period_model = self.env['date.period']
        period_date = fields.Date.from_string(move.date)
        period = period_model._get_period(period_date)
        if move.journal_id.id in period.journal_ids.ids:
            raise ValidationError(
                _("Can't create an account move line on a closed period."))

        return super(AccountMoveLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.env.context.get('bypass_close_date_period_check'):
            return super(AccountMoveLine, self).write(vals)

        bypass_fields = ['reconciled', 'full_reconcile_id']
        if any(key not in bypass_fields for key in list(vals.keys())):
            for rec in self:
                if rec.move_id.journal_id.id in \
                        rec.move_id.period_id.journal_ids.ids:
                    raise ValidationError(
                        _("Can't edit an account move line on "
                          "a closed period."))

        return super(AccountMoveLine, self).write(vals)

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.move_id.journal_id.id in \
                    rec.move_id.period_id.journal_ids.ids:
                raise ValidationError(
                    _("Can't delete an account move line on a closed period."))

        return super(AccountMoveLine, self).unlink()
