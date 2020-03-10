import pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
import calendar
from datetime import datetime, timedelta
from freezegun import freeze_time

class TestDatePeriod:

    def get_current_date(self):
        cnow = datetime.strptime("2019-03-01", "%Y-%m-%d")
        current_date = cnow.replace(hour=0, minute=0, second=0)
        return current_date


    def get_dates(self, month=False, to_str=False):
        current_date = self.get_current_date()
        c_year = current_date.year
        c_month = current_date.month
        if month:
            c_month = month
        dates = calendar.monthrange(c_year, c_month)
        date_to = datetime(c_year, c_month, dates[1], 0, 0)
        date_from = datetime(c_year, c_month, 1, 0, 0)
        return date_from, date_to

    def get_start_end(self, date):
        c_year = date.year
        c_month = date.month
        dates = calendar.monthrange(c_year, c_month)
        date_to = datetime(c_year, c_month, dates[1], 0, 0)
        date_from = datetime(c_year, c_month, 1, 0, 0)
        return date_from, date_to


    def to_str(self, date):
        str_date = date.strftime("%Y-%m-%d")
        return str_date

    def _prepare_fiscal_year(self):
        vals = {
            'name': 'FY1',
            'code': 'FY1',
            'date_from': '2019-01-01',
            'date_to': '2019-12-31',
            'state': 'draft',
        }
        return vals


    def cases_of_duplication(self, DP, date_from, date_to, fiscalyear):
        with pytest.raises(ValidationError,
                match=r".*Either some periods are overlapping.*"):
            DP.create({
                'code': '03/2019',
                'name': '03/2019',
                'date_from': date_from,
                'date_to': date_to,
                'fiscalyear_id': fiscalyear.id,
            })


    def test_duplicated_periods(self, DP, FY):
        date_from, date_to = self.get_dates()
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        DP.create({
            'code': '03/2019',
            'name': '03/2019',
            'date_from': date_from,
            'date_to': date_to,
            'fiscalyear_id': fiscalyear.id,
        })

        #Demo:
        dt_from0, dt_to0 = self.get_dates() #2019-03-01//2019-03-31
        lst_dt_from0, lst_dt_to0 = self.get_dates(month=2) #2019-02-01//2019-02-2X
        bf_dt_from0, bf_dt_to0 = self.get_dates(month=4) #2019-04-01//2019-04-30

        bt_dt_from0 = dt_from0 + timedelta(days=5) #2019-03-06
        bt_dt_to0 = dt_to0 - timedelta(days=5) #2019-03-26

        #Cases:
        """
        s1s2          e2e1
        ([-------------])

        s2   s1   e2   e1
        [----(----]    )

        s1   s2   e1   e2
        (    [----)----]

        s1   s2   e2   e1
        (    [----]    )

        s2   s1   e1   e2
        [----(----)-----]

        """

        cases = [{
            'date_from': self.to_str(dt_from0), #2019-03-01
            'date_to': self.to_str(dt_to0), #2019-03-31
        },{
            'date_from': self.to_str(lst_dt_to0), #2019-02-01
            'date_to': self.to_str(dt_from0), #2019-03-01
        },{
            'date_from': self.to_str(dt_to0), #2019-03-31
            'date_to': self.to_str(bf_dt_from0), #2019-04-01
        },{
            'date_from': self.to_str(bt_dt_from0), #2019-03-06
            'date_to': self.to_str(bt_dt_to0), #2019-03-26
        },{
            'date_from': self.to_str(lst_dt_to0), #2019-02-01
            'date_to': self.to_str(bt_dt_from0), #2019-03-06
        },{
            'date_from': self.to_str(bt_dt_to0), #2019-03-26
            'date_to': self.to_str(bf_dt_to0), #2019-04-30
        }]

        for case in cases:
            date_from = case['date_from']
            date_to = case['date_to']
            self.cases_of_duplication(DP, date_from, date_to, fiscalyear)

    def test_check_duration(self, DP, FY):
        date_from, date_to = self.get_dates()
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        with pytest.raises(ValidationError,
                match=r".*The duration of the Period.*"):
            DP.create({
                'code': '03/2019',
                'name': '03/2019',
                'date_from': date_to,
                'date_to': date_from,
                'fiscalyear_id': fiscalyear.id,
            })

    def test_search_periods(self, DP, FY):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        fiscalyear.button_create_period()
        date_demo_lst = [
            (1, "2019-03-19"),
            (1, "2019-12-31"),
            (1, "2019-01-01"),
            (0, "2018-12-31"),
            (0, "2020-01-01")
        ]
        for length, sdate in date_demo_lst:
            date = datetime.strptime(sdate, "%Y-%m-%d")
            period = DP.search_period_on_date(date)
            assert len(period) ==  length, "Invalid Period"
            if length:
                date_from, date_to = self.get_start_end(date)
                p_from = period.date_from.strftime("%Y-%m-%d")
                p_to = period.date_to.strftime("%Y-%m-%d")
                assert p_from == date_from.strftime("%Y-%m-%d") and\
                        p_to == date_to.strftime("%Y-%m-%d")
            return True

    def test_get_period(self, DP, FY):
        fiscalyear_vals = self._prepare_fiscal_year()
        fiscalyear = FY.create(fiscalyear_vals)
        fiscalyear.button_create_period()
        date_demo_lst = [
            (1, "2019-03-19"),
            (1, "2019-12-31"),
            (1, "2019-01-01"),
            (0, "2018-12-31"),
            (0, "2020-01-01")
        ]
        for length, sdate in date_demo_lst:
            date = datetime.strptime(sdate, "%Y-%m-%d")
            period = DP._get_period(date)
            assert len(period) ==  length, "Invalid Period"
            if length:
                date_from, date_to = self.get_start_end(date)
                p_from = period.date_from.strftime("%Y-%m-%d")
                p_to = period.date_to.strftime("%Y-%m-%d")
                assert p_from == date_from.strftime("%Y-%m-%d") and\
                        p_to == date_to.strftime("%Y-%m-%d")
            return True

