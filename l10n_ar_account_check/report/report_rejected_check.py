# -*- coding: utf-8 -*-

from odoo import models

def write_header(workbook):
    header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'size': 9})
    header_format.set_text_wrap()
    header_format.set_pattern(18)
    header_format.set_bg_color('#FFCCCC')

    sheet = workbook.add_worksheet('report')
    header = ['Fecha de rechazo', 'Número de cheque', 'Cliente', 'Monto', 'Documento de origen', 'Motivo de rechazo',
              'Propietario', 'Crítico', 'Observaciones']
    sheet.write_row(0, 0, header, header_format)
    return sheet

def write_lines(workbook, lines):
    money_format = workbook.add_format({'num_format': '$#,##0', 'size': 9})
    font_format = workbook.add_format({'size': 9, 'align': 'right'})
    sheet = workbook.worksheets()[0]

    for i, check in enumerate(lines):
        reason_name = '-'
        if check.reason_id:
            reason_name = check.reason_id.code or ''
            reason_name += ' - ' + check.reason_id.name
        if check.check_issuing_type == 'own':
            owner = 'Propio'
        elif check.check_issuing_type == 'third':
            owner = 'Terceros'
        else:
            owner = '-'
        sheet.write(i+1, 0, check.reject_date.strftime('%d/%m/%Y'), font_format)
        sheet.write(i+1, 1, check.number, font_format)
        sheet.write(i+1, 2, check.source_partner_id.name, font_format)
        sheet.write(i+1, 3, check.amount, money_format)
        sheet.write(i+1, 4, check.source_payment_order_id.number, font_format)
        sheet.write(i+1, 5, reason_name, font_format),
        sheet.write(i+1, 6, owner, font_format),
        sheet.write(i+1, 7, 'Crítico' if check.reason_id.is_critical else '-', font_format),
        sheet.write(i+1, 8, check.note if check.note else '-', font_format)


class RejectedReportXlsx(models.AbstractModel):
    _name = 'report.report_xlsx.report_rejected_third_check'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, record):
        # data
        rejected_checks = self.env['account.third.check'].browse(data['ids'])

        # header
        sheet = write_header(workbook)

        # cell sizes
        sheet.set_row(0, 24)
        sheet.set_column(1, 1, 22)
        sheet.set_column(2, 2, 18)
        sheet.set_column(3, 6, 22)
        sheet.set_column(7, 8, 18)
        sheet.set_column(9, 9, 22)

        # lines
        write_lines(workbook, rejected_checks)
