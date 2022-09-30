# -*- coding: utf-8 -*-

from odoo import models

def write_header(workbook):
    header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'size': 9})
    header_format.set_text_wrap()
    header_format.set_pattern(18)
    header_format.set_bg_color('#FFCCCC')

    sheet = workbook.add_worksheet('report')
    header = ['Número de cheque', 'Proveedor', 'Monto', 'Orden de pago', 'Motivo de devolución',
              'Reemplazado', 'Observaciones']
    sheet.write_row(0, 0, header, header_format)
    return sheet

def write_lines(workbook, lines):
    money_format = workbook.add_format({'num_format': '$#,##0', 'size': 9})
    font_format = workbook.add_format({'size': 9, 'align': 'right'})
    sheet = workbook.worksheets()[0]

    for i, check in enumerate(lines):
        sheet.write(i+1, 0, check.number, font_format)
        sheet.write(i+1, 1, check.receiving_partner_id.name, font_format)
        sheet.write(i+1, 2, check.amount, money_format)
        sheet.write(i+1, 3, check.payment_order_id.number, font_format)
        sheet.write(i+1, 4, check.reason_id.code + ' - ' + check.reason_id.name if check.reason_id else '-', font_format)
        sheet.write(i+1, 5, check.replacement_payment_order_id.number if check.replaced else 'No', font_format)
        sheet.write(i+1, 6, check.note if check.note else '-', font_format)


class InvoiceReportXlsx(models.AbstractModel):
    _name = 'report.report_xlsx.report_returned_check'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, record):
        # data
        returned_checks = self.env['account.issued.check'].browse(data['ids'])

        # header
        sheet = write_header(workbook)

        # cell sizes
        sheet.set_row(0, 24)
        sheet.set_column(1, 4, 22)
        sheet.set_column(5, 5, 14)
        sheet.set_column(6, 6, 22)

        # lines
        write_lines(workbook, returned_checks)
