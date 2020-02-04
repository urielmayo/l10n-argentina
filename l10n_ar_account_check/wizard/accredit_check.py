from openerp import models, api, fields

class WizardAccreditCheck(models.TransientModel):
    _name = 'wizard.accredit.check'
    _description = 'Acredits a check'

    accreditation_date = fields.Date('Accreditation Date',default=fields.Datetime.now)
    #fecha de acreditacion
    
    @api.multi
    def accredit_checks(self):
        date = self.accreditation_date
        ctx = self.env.context
        act_ids = ctx.get("active_ids")
        model = self.env['account.issued.check']
        records = model.browse(act_ids)
        records.accredit_checks(date)

class account_issued_check(models.Model):
    _inherit = 'account.issued.check'

    def accredit_checks(self,date):
        #TODO: create the corresponding moves
        for check in self:
            if check.state != "waiting":
                raise exceptions.ValidationError(_("Check %s can't be accredited!") % check.number)
        for check in self:
            company = self.env.user.company_id
            check_conf_obj = self.env['account.check.config']
            def_check_account = check_conf_obj.search([('company_id', '=', company.id)]).deferred_account_id
            def_check_journal = check_conf_obj.search([('company_id', '=', company.id)]).deferred_journal_id
            if not def_check_journal:
                raise except_orm(_("Error!"),_("There is no Journal configured for deferred checks."))

            period_obj = self.env['account.period']
            current_period = period_obj.search([('date_start', '<=', date), ('date_stop', '>=', date)])

            move_line_obj = self.env['account.move.line']
            move_obj = self.env['account.move']
            name_ref = 'Clearance Check ' + check.number
            move_vals = {   'ref': name_ref,
                            'journal_id': def_check_journal.id,
                            'date':date,
                            'period_id':current_period.id,
                        }
            move_id = move_obj.create(move_vals)

            check.write({'clearance_move_id': move_id.id})

            # Creamos la linea contable que iguala el pago del cheque
            check_move_line_vals = {    'journal_id': def_check_journal.id,
                                        'period_id': current_period.id,
                                        'date': date,
                                        'name': name_ref,
                                        'account_id': def_check_account.id,
                                        'debit': check.amount,
                                        'move_id': move_id.id,
                                   }

            clearance_move_line = move_line_obj.create(check_move_line_vals)

            # Creamos la linea contable que refiere a la acreditacion por parte del banco
            bank_move_line_vals = {     'journal_id': def_check_journal.id,
                                        'period_id': current_period.id,
                                        'date': date,
                                        'name': name_ref,
                                        'account_id': check.checkbook_id.bank_account_id.account_id.id,
                                        'credit': check.amount,
                                        'move_id': move_id.id,
                                   }

            move_line_obj.create(bank_move_line_vals)

            move_lines_to_reconcile = []
            payment_move_line = move_line_obj.search([('issued_check_id', '=', check.id)])
            move_lines_to_reconcile.append(payment_move_line.id)
            move_lines_to_reconcile.append(clearance_move_line.id)
            reconcile_recordset = move_line_obj.browse(move_lines_to_reconcile)
            reconcile_recordset.reconcile()

        return self.write({"state": "issued"})