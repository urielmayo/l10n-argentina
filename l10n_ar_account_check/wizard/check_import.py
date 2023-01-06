
import base64
import logging
import os
import re
import xlrd
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import config

data_dir = config.get("data_dir")
data_dir = os.path.isdir(data_dir) and data_dir or os.path.dirname(__file__)

_logger = logging.getLogger(__name__)


class ThirdCheckImport(models.TransientModel):
    _name = 'account.check.import'
    _description = 'Third Check Import'

    bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account',
                                      domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)],
                                      required=True)
    filename = fields.Char('Filename')
    file = fields.Binary('File', filename='filename', required=True)

    bank_id = fields.Many2one('res.bank', string='Bank', readonly=True)
    check_format = fields.Selection([('physical', 'Physical'), ('virtual', 'Virtual'), ('echeq', 'Echeq')],
                                    string='Check Format', compute='_compute_check_format', readonly=True, store=True)

    @api.depends('bank_account_id')
    def _compute_check_format(self):
        if self.bank_account_id:
            self.bank_id = self.bank_account_id.bank_id.id
            if 'bbva' in self.bank_id.name.lower():
                self.check_format = 'physical'
            elif 'macro' in self.bank_id.name.lower():
                self.check_format = 'echeq'
            else:
                self.check_format = ''

    def save_file(self, name, value):
        name, extension = os.path.splitext(name)

        base_path = os.path.join(data_dir, "third_check_import", )
        if not os.path.isdir(base_path):
            os.mkdir(base_path)

        path = os.path.join(base_path, name)
        with open(path, 'wb+') as new_file:
            new_file.write(base64.decodebytes(value))

        _logger.debug("Saved file in: %s", path)
        return path

    def _read_cell(self, sheet, row, cell):
        cell_type = sheet.cell_type(row, cell)
        cell_value = sheet.cell_value(row, cell)

        if cell_type in [1, 2]:  # 3: Excel date/time, 2: select, 1: text, 0: empty
            return cell_value
        elif cell_type == 3:
            value = xlrd.xldate.xldate_as_datetime(cell_value, datemode=0)
            return value
        elif cell_type == 0:
            return None

        raise UserError(_('Formato de archivo inválido'))

    def _search_bank(self, bank_code):
        bank = self.env['res.bank'].search([('bic', 'like', int(bank_code))])
        if not bank:
            _logger.warning('No bank - skipping check...')
            return False
        else:
            _logger.warning('Bank found')
            return bank

    def _search_check(self, number, bank):
        _logger.warning('Searching existing check...')
        ch = self.env['account.third.check'].search([
            ('number', '=', number),
            ('bank_id', '=', bank.id)
        ])
        return ch

    def _preparing_check_vals(self, bank_import, bank, sheet, curr_row):
        bank_account = False
        if bank_import == 'bbva':
            check_format = 'physical'
            receipt_date = self._read_cell(sheet, curr_row, 0)
            payment_date = self._read_cell(sheet, curr_row, 1)
            deposit_slip = self._read_cell(sheet, curr_row, 2)
            number = self._read_cell(sheet, curr_row, 3)
            amount = self._read_cell(sheet, curr_row, 4)
            deposit_bank = self._read_cell(sheet, curr_row, 9)  # res.partner.bank
            partner_vat = self._read_cell(sheet, curr_row, 12)  # signatory_vat
            partner_name = self._read_cell(sheet, curr_row, 13)
            # bank_name = self._read_cell(sheet, curr_row, 15)  # banco girador
            bank_branch = self._read_cell(sheet, curr_row, 16)
            zip = self._read_cell(sheet, curr_row, 18)

            # bank_account
            _logger.warning('Searching bank account...')
            dep_bank = re.sub("[CA/$-]|\s", '', deposit_bank)
            _logger.warning(dep_bank)
            bank_accounts = self.env['res.partner.bank'].search([])
            bank_account = bank_accounts.filtered(lambda x: (dep_bank[:3] in x.acc_number)
                                                            or (dep_bank[-4:-1] in x.acc_number))  # -_-
            if bank_account:
                _logger.warning('Bank account found')
            else:
                _logger.warning('Bank account not found')
                bank_account = False

            # dates
            payment_date = datetime.strptime(payment_date, "%d/%m/%Y").date()
            receipt_date = datetime.strptime(receipt_date, "%d/%m/%Y").date()
            issue_date = receipt_date  # hardcode

        if bank_import == 'macro':
            check_format = 'echeq'
            issue_date = self._read_cell(sheet, curr_row, 0)
            payment_date = self._read_cell(sheet, curr_row, 1)
            number = self._read_cell(sheet, curr_row, 2)
            # name1 = self._read_cell(sheet, curr_row, 4)
            amount = self._read_cell(sheet, curr_row, 5)
            # vat1 = self._read_cell(sheet, curr_row, 6)
            partner_name = self._read_cell(sheet, curr_row, 8)
            partner_vat = self._read_cell(sheet, curr_row, 9)
            # bank_name = self._read_cell(sheet, curr_row, 12)
            deposit_slip = False
            zip = False
            bank_branch = False

            # dates
            payment_date = payment_date.date()
            issue_date = issue_date.date()
            receipt_date = issue_date  # hardcode

        # search source_partner_id
        partner = self.env['res.partner'].search([
            ('|'),
            ('vat', '=', str(int(partner_vat))),
            ('name', '=', partner_name)
        ])
        if partner:
            _logger.warning('Partner found')
        else:
            _logger.warning('Partner not found')
            partner = False

        vals = {
            'number': str(int(number)),
            'amount': float(amount),
            'receipt_date': receipt_date,
            'issue_date': issue_date,
            'payment_date': payment_date,
            'bank_id': bank.id,
            'check_format': check_format,
            'deposit_slip': str(int(deposit_slip)) if deposit_slip else False,
            # 'check_issuing_type': 'own',  # ?
            'deposit_bank_id': bank_account.id if bank_account else False,
            'signatory_vat': str(int(partner_vat)) if partner_vat else False,
            'source_partner_id': partner[0].id if partner else False,  # hardcode[0]
            'bank_branch': bank_branch if bank_branch else False,
            'zip': zip if zip else False,
        }
        return vals

    def import_file(self):
        path = self.save_file(self.filename, self.file)
        if path and (self.check_format == 'physical'):
            bank_import = 'bbva'
            first_row = 6
            col_number = 3
        elif path and (self.check_format == 'echeq'):
            bank_import = 'macro'
            first_row = 5
            col_number = 2
        else:
            raise UserError(_('Check import is not available for this bank.'))

        book = xlrd.open_workbook(path)
        sheet = book.sheets()[0]

        def summary(imported, not_imported, repeated):
            res = _('Summary:\nImported checks: %s\nNot imported: %s\nRepeated checks (not imported): %s'
                    % (imported, not_imported, repeated))
            return res

        imported = 0
        not_imported = 0
        repeated = 0

        for curr_row in range(first_row, sheet.nrows):
            _logger.warning(curr_row)
            number = self._read_cell(sheet, curr_row, col_number)
            bank_code = self._read_cell(sheet, curr_row, 14)
            # check if it is a valid row:
            try:
                int(number)
            except:
                _logger.warning('End Of Table')
                break

            # bank
            bank = self._search_bank(bank_code)
            if not bank:
                not_imported += 1
                msg = 'Bank code not found.\n\nCode: %s\nRow: %s\n' % (bank_code, curr_row+1)
                raise UserError(_(msg))

            # check
            ch = self._search_check(number, bank)
            if ch:
                repeated += 1
                _logger.warning('Check number found in the database - skipping...')
                continue
            else:
                vals = self._preparing_check_vals(bank_import, bank, sheet, curr_row)
                try:
                    _logger.warning('Creating new check...')
                    self.env['account.third.check'].create(vals)
                except:
                    not_imported += 1
                    _logger.warning('Value error - skipping...')
                    continue

                _logger.warning('Check successfully imported')
                imported += 1

        self.env.user.notify_info(message=_(summary(imported, not_imported, repeated)),
                                  title='Finished', sticky=True)
