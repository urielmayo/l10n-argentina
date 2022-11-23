##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

PADRON = [
    ('arba', 'ARBA'),
    ('agip', 'AGIP'),
    ('agip_rp', 'AGIP_RP'),
    ('santa_fe', 'SANTA_FE'),
    ('jujuy', 'JUJUY'),
    ('cordoba', 'CORDOBA'),
    ('tucuman', 'TUCUMAN'),
    ('formosa', 'FORMOSA'),
]
class PerceptionPerception(models.Model):
    _name = "perception.perception"
    _inherit = "perception.perception"

    from_register = fields.Selection(PADRON, default=PADRON[0][0])

    @api.model
    def _get_perception_from_arba(self):
        ret = self.search([('from_register', '=', 'arba')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from ARBA. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_perception_from_agip(self):
        ret = self.search([('from_register', '=', 'agip')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from AGIP. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret
    @api.model
    def _get_perception_from_agip_rp(self):
        ret = self.search([('from_register', '=', 'agip_rp')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from AGIP. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_perception_from_santa_fe(self):
        ret = self.search([('from_register', '=', 'santa_fe')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from SANTA_FE. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_perception_from_jujuy(self):
        ret = self.search([('from_register', '=', 'jujuy')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from JUJUY. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_perception_from_cordoba(self):
        ret = self.search([('from_register', '=', 'cordoba')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from CORDOBA. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret

    @api.model
    def _get_perception_from_tucuman(self, ):
        ret = self.search([('from_register', '=', 'tucuman')])
        if len(ret) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from Tucumán. Please review configuration'))
        elif len(ret) == 0:
            return False
        else:
            return ret