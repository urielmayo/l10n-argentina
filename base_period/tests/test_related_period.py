import pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
import calendar
from datetime import datetime, timedelta
from freezegun import freeze_time

class TestRelatedPeriod:

    def _prepare_fiscal_year(self):
        vals = {
            'name': 'FY1',
            'code': 'FY1',
            'date_from': '2019-01-01',
            'date_to': '2019-12-31',
            'state': 'draft',
        }
        return vals


    def create_invoice(self, INV, ENV):
        partner = ENV.ref('base.res_partner_12')
        product = ENV.ref('product.product_product_5')
        act = ENV['account.account.type'].search([], limit=1)
        account = ENV['account.account'].create(dict(
            name="Tax Received",
            code="X121",
            user_type_id=act.id,
            reconcile=True,
        ))
        inv = INV.create({
            'date_invoice': '2019-06-20',
            'partner_id': partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': 'TEst',
                    'quantity': 1,
                    'price_unit': 12,
                    'account_id': account.id,
                })
            ]
        })
        return inv

    def test_close_journal_from_journal(self, DP, FY, ENV):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        fiscalyear.button_create_period()

        date = datetime.strptime('2019-06-20', "%Y-%m-%d")
        period = DP._get_period(date)

        wz_obj = ENV['close.account.journal.wizard']
        journal = ENV['account.journal'].search([], limit=1)
        active_journals = ENV['account.journal'].search([])
        ctx = {
            'active_ids': journal.ids
        }
        wz = wz_obj.with_context(ctx).create({
            'period_id': period.id
        })
        #Test Close Journal
        wz.button_close()
        if len(journal) != len(active_journals):
            assert period.period_state == 'partial',\
                    "Period must be in partial state"
        else:
            assert period.period_state == 'closed', \
                    "Period must be closed"
        assert journal.id in period.journal_ids.ids, \
                "The journal are not related to period"
        wz.with_context(active_ids=journal.ids).button_open()
        assert period.period_state == 'open'
        assert not period.journal_ids.ids

        #Inverse Operation -> Close all journals
        period.write({
            'journal_ids': [(6, 0, active_journals.ids)]
        })
        assert period.period_state == 'closed'
        assert len(period.journal_ids) == len(active_journals)
        wz.with_context(active_ids=journal.ids).button_open()
        assert journal.id not in period.journal_ids.ids


    def close_journals(self, journals, ENV):
        wz = ENV['close.account.journal.wizard']


    def test_invoice(self, FY, INV, ENV):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        fiscalyear.button_create_period()
        inv = self.create_invoice(INV, ENV)
        assert inv.period_id
        assert inv.period_id.date_from.month == 6
        assert inv.period_id.date_to.month == 6
        inv.action_invoice_open()
        with pytest.raises(ValidationError,
                match=r".*You can not unlink a period with.*"):
            inv.period_id.unlink()

        assert inv.move_id.period_id == inv.period_id, "Invalid period in move"
        assert all(inv.move_id.line_ids.mapped(
            lambda x: x.period_id.id == inv.period_id.id)),\
                    "Invalid period in move lines"

        #Cerramos todos los diarios
        journals = ENV['account.journal'].search([])
        inv.period_id.write({
            'journal_ids': [(6, 0, journals.ids)]
        })
        with pytest.raises(ValidationError,
                match=r".*delete an account move line*"):
            inv.move_id.line_ids.unlink()

        with pytest.raises(ValidationError,
                match=r".*delete an account move on*"):
            inv.move_id.unlink()

        with pytest.raises(ValidationError,
                match=r".*edit an account move line on*"):
            inv.move_id.line_ids.write({
                'name': 'No Edit'
            })

        with pytest.raises(ValidationError,
                match=r".*edit an account move on*"):
            inv.move_id.write({
                'name': 'No Edit'
            })

    def get_move_vals(self, ENV):
        partner = ENV.ref('base.res_partner_12')
        product = ENV.ref('product.product_product_5')
        move_vals = {
            'ref': 'INV/2020/0002/02',
            'journal_id': 1,
            'name': 'INV/2020/0002/02',
            'date': '2019-06-20'
        }
        return move_vals

    def get_move_line_cr_vals(self, ENV):
        partner = ENV.ref('base.res_partner_12')
        product = ENV.ref('product.product_product_5')
        act = ENV['account.account.type'].search([], limit=1)
        account = ENV['account.account'].create(dict(
            name="Tax Received",
            code="X121",
            user_type_id=act.id,
            reconcile=True,
        ))
        move_line_vals = {
            'account_id': account.id,
            'partner_id': partner.id,
            'credit': 100,
        }
        return move_line_vals

    def get_move_line_db_vals(self, ENV):
        partner = ENV.ref('base.res_partner_12')
        product = ENV.ref('product.product_product_5')
        account = partner.property_account_receivable_id
        move_line_vals = {
            'account_id': account.id,
            'partner_id': partner.id,
            'debit': 100,
        }
        return move_line_vals


    def test_move(self, FY, ENV, MV):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        fiscalyear.button_create_period()

        move_vals = self.get_move_vals(ENV)
        move = MV.create(move_vals)
        period = move.period_id
        assert period.date_from.month == 6
        move.unlink()

        #Create in closed period
        active_journals = ENV['account.journal'].search([])
        period.write({
            'journal_ids': [(6, 0, active_journals.ids)]
        })

        with pytest.raises(ValidationError,
                match=r".*reate an account move on a closed period*"):
            move = MV.create(move_vals)

    def test_move_line(self, FY, ENV, MV, MVL):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        fiscalyear.button_create_period()

        move_vals = self.get_move_vals(ENV)
        move = MV.create(move_vals)

        lcr_vals = self.get_move_line_cr_vals(ENV)
        ldb_vals = self.get_move_line_db_vals(ENV)
        #Add Move Lines
        ccr_vals = lcr_vals.copy()
        move.write({
            'line_ids': [(0, 0, ccr_vals), (0, 0, ldb_vals)]
        })
