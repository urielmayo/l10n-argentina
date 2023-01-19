from odoo import api, models, _
from odoo.exceptions import ValidationError

class PerceptionSalta(models.Model):
    _name = 'perception.perception'
    _inherit = 'perception.perception'
    
    @api.model
    def _get_perception_from_salta(self):
        per = self.search([('from_register', '=', 'salta')])
        if len(per) > 1:
            raise ValidationError(
                _('Perceptions Improperly Configured\n') +
                _('You can not have more than one perception to update ' +
                  'from SALTA. Please review configuration'))
        elif len(per) == 0:
            return False
        else:
            return per