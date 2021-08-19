##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from datetime import datetime as dt

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF

class res_partner_retention(models.Model):
    _name = "res.partner.retention"
    _description = "Retention Defined in Partner"
    _rec_name = 'retention_id'

    retention_id = fields.Many2one('retention.retention', 'Retention',
                                   required=True)
    activity_id = fields.Many2one('retention.activity', 'Activity')
    percent = fields.Float('Percent', default=0.00)
    excluded_percent = fields.Float('Percentage of Exclusion')
    ex_date_from = fields.Date('From date')
    ex_date_to = fields.Date('To date')
    exclusion_certificate = fields.Binary(string='Exclusion Certificate')
    exclusion_date_certificate = fields.Date(
        'Exclusion General Resolution Date')
    partner_id = fields.Many2one('res.partner', 'Partner')
    sit_iibb = fields.Many2one(
        comodel_name='iibb.situation', string='Situation of IIBB')
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='retention_id.company_id',
        string='Company',
        store=True,
    )

    _sql_constraints = [
        ('retention_partner_unique',
         'unique(partner_id, retention_id)',
         'There must be only one retention of this type configured for ' +
         'the partner')
    ]

    @api.constrains('excluded_percent')
    def _check_excluded_percent(self):
        for p_ret in self:
            if not (0 <= p_ret.excluded_percent <= 1):
                raise ValidationError(
                    _("The Excluded Percent Should be a value " +
                      "between 0 and 1"))

    @api.onchange('retention_id')
    def retention_id_change(self):
        ret_type = self.retention_id.type
        domain = [('type', '=', ret_type)]
        return {'domain': {'activity_id': domain}}


class ResPartnerAdvanceRetention(models.Model):
    _name = "res.partner.advance.retention"
    _description = "Retention advanced defined in Partner"

    retention_id = fields.Many2one(
        comodel_name='retention.retention',
        string='Retention', required=True)
    concept_id = fields.Many2one(
        comodel_name='retention.concept',
        string="Concept", required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Partner")
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='retention_id.company_id',
        string='Company',
        store=True,
    )


class res_partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    @api.model
    def _get_retentions_domain(self):
        company = self.env.user.company_id
        return [
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id),
        ]

    retention_ids = fields.One2many(
        'res.partner.retention', 'partner_id', 'Retentions Exceptions',
        domain=lambda self: self._get_retentions_domain(),
        help="Here you have to configure retention exceptions for this " +
        "partner with this Fiscal Position")
    advance_retention_ids = fields.One2many(
        comodel_name='res.partner.advance.retention',
        inverse_name='partner_id',
        domain=lambda self: self._get_retentions_domain(),
        string="Advance Payment Concept")

    def _get_retentions_to_apply(self, operation_date):

        # Buscamos las retenciones a aplicar segun la posicion fiscal
        retentions = {}
        for ret in self.property_account_position_id.retention_ids:
            retention = {
                'retention': ret,
                'activity_id': False,
                'excluded_percent': False,
                'percent': -1.0,
                'ex_date_to': False,
                'ex_date_from': False,
                'sit_iibb': False,
                'exclusion_date_certificate': False,
                'from_padron': False,
            }

            retentions[ret.id] = retention

        # Ahora buscamos a ver si tiene alguna excepcion
        partner_retentions = {}
        for p_ret in self.retention_ids:
            excluded_percent = p_ret.excluded_percent
            # ~ ddate = dt.strftime(operation_date, DSDF)
            ddate = dt.strftime(operation_date, "%Y-%m-%d %H:%M:%S")
            # ~ tzd = fields.Datetime.context_timestamp(self, ddate)
            # Chequeamos que la retencion este en un periodo valido
            if excluded_percent:
                if p_ret.ex_date_from and p_ret.ex_date_to:
                    # Exclusion applies if we are into the boundaries
                    if not (p_ret.ex_date_from <= operation_date <= p_ret.ex_date_to):
                        excluded_percent = False
                elif p_ret.ex_date_from:
                    # Exclusion applies only if we are latter than date_from
                    if not (p_ret.ex_date_from <= operation_date):
                        excluded_percent = False
                elif p_ret.ex_date_to:
                    # Exclusion applies only if we are before than ex_date_to
                    if not (operation_date <= p_ret.ex_date_to):
                        excluded_percent = False

            retention = {
                'retention': p_ret.retention_id,
                'activity_id': p_ret.activity_id,
                'excluded_percent': excluded_percent,
                'percent': p_ret.percent,
                'ex_date_to': p_ret.ex_date_to,
                'ex_date_from': p_ret.ex_date_from,
                'sit_iibb': p_ret.sit_iibb,
                'exclusion_date_certificate': p_ret.exclusion_date_certificate,
                'from_padron': p_ret.from_padron,
            }

            partner_retentions[p_ret.retention_id.id] = retention

        # Actualizamos el diccionario de retenciones
        retentions.update(partner_retentions)
        return retentions


class account_fiscal_position(models.Model):
    _inherit = 'account.fiscal.position'

    @api.model
    def _get_retentions_domain(self):
        company = self.env.user.company_id
        return [
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id),
        ]

    retention_ids = fields.Many2many(
        'retention.retention', 'fiscal_position_retention_rel',
        'position_id', 'retention_id', 'Retentions',
        domain=lambda self: self._get_retentions_domain(),
        help="These are the retentions that will be applied to Suppliers " +
        "belonging to this Fiscal Position. Exceptions to this have to be " +
        "loaded at partner form.")
