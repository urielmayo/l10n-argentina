# -*- coding: utf-8 -*-

import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReturnedCheckReport(models.Model):
    _name = 'account.returned.check.report'
    _description = 'Returned Check Report'

    reason = fields.Many2one(comodel_name='reason.rejected.check', string='Reason',
                             domain="[('type', '=', 'returned')]")
    date_since = fields.Date(string='Since')
    date_to = fields.Date(string='To')
    check_qty = fields.Integer(string='Found Checks', compute='_compute_returned_check_qty')

    @api.onchange('date_since', 'date_to', 'reason')
    def _compute_returned_check_qty(self):
        for rec in self:
            returned_checks = rec._compute_returned_check_ids()
            rec.check_qty = len(returned_checks) if returned_checks else 0

    def _compute_returned_check_ids(self):
        if self.date_since and self.date_to and self.reason:
            returned_checks = self.env['account.issued.check'].search([
                ('state', '=', 'returned'),
                ('return_date', '>=', self.date_since),
                ('return_date', '<=', self.date_to),
                ('reason', '=', self.reason),
            ])
            return returned_checks

    def print_report(self):
        returned_checks = self._compute_returned_check_ids()
        if returned_checks:
            data = {'ids': returned_checks.ids,
                    'model': 'account.issued.check',
                    'form': self.read()[0],
                    }
            return {
                'data': data,
                'type': 'ir.actions.report',
                'report_name': 'report_xlsx.report_returned_check',
                'report_type': 'xlsx',
                'report_file': 'returned_checks',
                'name': 'Report returned checks',
            }
        raise UserError("Empty report.")
