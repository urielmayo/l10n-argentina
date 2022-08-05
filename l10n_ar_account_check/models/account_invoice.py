
import json
from odoo import api, models, fields
from odoo.tools import date_utils, float_is_zero


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def compute_reverse_widget(self, reverse_dict):
        if self.reverse_widget and json.loads(self.reverse_widget):
            actual_dict = json.loads(self.reverse_widget)
            actual_dict['content'].append(reverse_dict['content'])
            dump_dict = actual_dict
        else:
            dump_dict = reverse_dict
        self.reverse_widget = json.dumps(dump_dict, default=date_utils.json_default)

    reverse_widget = fields.Text()
