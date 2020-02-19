import pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
import calendar
from datetime import datetime, timedelta
from freezegun import freeze_time

class TestFiscalYear:

    def _prepare_fiscal_year(self):
        vals = {
            'name': 'FY1',
            'code': 'FY1',
            'date_from': '2019-01-01',
            'date_to': '2019-12-31',
            'state': 'draft',
        }
        return vals

    def check_periods(self, fiscalyear, interval):
        periods = fiscalyear.period_ids
        assert len(periods) == interval +1, "Bad creation of periods"
        periods.sorted('date_from')
        op_period = periods[0]
        assert op_period.date_from == '2019-01-01'\
                and op_period.date_to == '2019-01-01',\
                "Invalid opening period"
        ref_month = 0
        cdate = datetime.strftime("%Y-%m-%d", "2019-01-01")
        fdate = fiscalyear.date_to
        for period in periods:
            if not ref_month:
                assert period.special, "Invalid opening period (special)"
            de = cdate + relativedelta(months=ref_month)
            ds = cdate + relativedelta(months=ref_month+interval, days=-1)
            de_str = de.strptime("%Y-%m-%d")
            ds_str = ds.strptime("%Y-%m-%d")
            if ds_str > fdate:
                ds_str = fdate.strptime("%Y-%m-%d")
            assert period.date_from == de_str and\
                    period.date_to == ds_str, "Invalid date of period"
            ref_month += interval
        return True

    def test_create_monthly_period(self, FY):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(vals)
        assert fiscalyear
        fiscalyear.button_create_period()
        assert fiscalyear.period_ids, "There are not periods"
        self.check_periods(fiscalyear, 1)
        return True

    def test_create_period3(self, FY):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(vals)
        assert fiscalyear
        fiscalyear.button_create_period3()
        fiscalyear.button_create_period()
        assert fiscalyear.period_ids, "There are not periods"
        self.check_periods(fiscalyear, 3)
        return True

    def test_find_period(self, FY):
        with pytest.raises(RedirectWarning,
                match=r".*There is no period defined for this date.*"):
            FY.find(dt='2019-03-15')
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(vals)
        ref_fiscalyear = FY.find('2019-03-03')
        assert ref_fiscalyear.id == fiscalyear.id, "Fiscalyear not found"
        bad_fiscalyear = FY.find('2020-03-03', exception=False)
        assert not bad_fiscalyear, "Expected false to find fiscalyear"


