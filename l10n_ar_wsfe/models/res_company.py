##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields, api, _
import requests
import re
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    fcred_cbu_emitter = fields.Char(string='CBU (FCE)')
    fcred_minimum_amount = fields.Float(string='Monto Minimo (FCE)', default=195698)
    fcred_transfer = fields.Char(string='SCA/ADC (FCE)?', default='SCA')
    fcred_is_fce_emitter = fields.Boolean(string='FCE Emitter?', default=False)
    fcred_pos_ar_id = fields.Many2one('pos.ar', string='FCE Pos', domain="[('fcred_is_fce_emitter', '=', True)]")


class AfipBigCompany(models.Model):
    _name = 'afip.big.company'

    cuit = fields.Char(string='CUIT')

    @api.model
    def get_from_afip(self):
        """
        Retrieves all the cuits from AFIP endpoint
        """
        REQ = requests.post(
            'https://servicioscf.afip.gob.ar/FCEServicioConsulta/api/fceconsulta.aspx/getGrandesEmpresas')
        raw_response = REQ.text
        list_of_cuit = re.findall('Cuit..([0-9]*)', raw_response)
        return list_of_cuit

    @api.model
    def do_update(self):
        """
        Updates the table of big companies
        """
        ss = self.sudo()
        ss.search([]).unlink()
        big_companies = self.get_from_afip()
        for cuit in big_companies:
            ss.create({'cuit': cuit})
        _logger.info('[afip.big.company] has retrieved the following companies from afip and updated the local table')
        _logger.info(big_companies)
