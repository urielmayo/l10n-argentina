##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

PROVINCE = [
    ('arba', 'ARBA'),
    ('agip', 'AGIP'),
    ('agip_rp', 'AGIP_RP'),
    ('santa_fe', 'SANTA_FE'),
    ('jujuy', 'JUJUY'),
    ('cordoba', 'CORDOBA'),
    ('tucuman', 'TUCUMAN'),
]

class RetentionRetention(models.Model):
    _name = "retention.retention"
    _inherit = "retention.retention"

    from_register = fields.Selection(PROVINCE, default=PROVINCE[0][0])
#    from_register_ARBA = fields.Boolean('From ARBA Register')
#    from_register_AGIP = fields.Boolean('From AGIP Register')
#    from_register_AGIP_RP = fields.Boolean('From AGIP Register')
#    from_register_SANTA_FE = fields.Boolean('From SANTA FE Register')
#    from_register_JUJUY = fields.Boolean('From JUJUY Register')
#    from_register_CORDOBA = fields.Boolean('From CORDOBA Register')
#    from_register_TUCUMAN = fields.Boolean('From TUCUMAN Register')

    @api.model
    def _get_retention_from_arba(self):
        ret = self.search([('from_register', '=', 'arba')])
        if len(ret) > 1:
            raise ValidationError(
                _('Retentions Improperly Configured\n') +
                _('You can not have more than one retention to update ' +
                  'from ARBA. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_retention_from_agip(self):
        ret = self.search([('from_register', '=', 'agip')])
        if len(ret) > 1:
            raise ValidationError(
                _('Retentions Improperly Configured\n') +
                _('You can not have more than one retention to update ' +
                  'from AGIP. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_retention_from_agip_rp(self):
        ret = self.search([('from_register', '=', 'agip_rp')])
        if len(ret) > 1:
            raise ValidationError(
                _('Retentions Improperly Configured\n') +
                _('You can not have more than one retention to update ' +
                  'from AGIP. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_retention_from_santa_fe(self):
        ret = self.search([('from_register', '=', 'santa_fe')])
        if len(ret) > 1:
            raise ValidationError(
                _('Retentions Improperly Configured\n') +
                _('You can not have more than one retention to update ' +
                  'from SANTA FE. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_retention_from_jujuy(self):
        ret = self.search([('from_register', '=', 'jujuy')])
        if len(ret) > 1:
            raise ValidationError(
                _('Retentions Improperly Configured\n') +
                _('You can not have more than one retention to update ' +
                  'from JUJUY. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret


