##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields



class AgipRetentionGroup(models.Model):
    _name = 'agip.retention.group'
    _description = 'Group number of Retention'

    name = fields.Char('Group Number', size=2, index=1)
    aliquot = fields.Float("Aliquot", digits=(3, 2))

class AgipRetentionGroupRP(models.Model):
    _name = 'agip.perception.group.rp'
    _inherit = 'agip.retention.group'
    _description = 'Group number of Perception'

class AgipPerceptionGroup(models.Model):
    _name = 'agip.perception.group'
    _description = 'Group number of Perception'

    name = fields.Char('Group Number', size=2, index=1)
    aliquot = fields.Float("Aliquot", digits=(3, 2))

class AgipPerceptionGroupRP(models.Model):
    _name = 'agip.perception.group.rp'
    _inherit = 'agip.perception.group'
    _description = 'Group number of Perception'

class AgipRetentions(models.Model):
    """
    This model represent the agip csv file that defines percentage
    of retentions and perceptions
    """
    _name = 'padron.agip_percentages'
    _description = 'Definition of percentages of taxes by customer'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    vat = fields.Char('Afip code', size=15, index=1)
    percentage_perception = fields.Float('Percentage of perception')
    percentage_retention = fields.Float('Percentage of retention')
    multilateral = fields.Boolean('Is multilateral?')
    name_partner = fields.Text('Company name')
    group_retention_id = fields.Many2one(
        'agip.retention.group', 'Retention Group')
    group_perception_id = fields.Many2one(
        'agip.perception.group', 'Perception Group')

class AgipRetentionsRP(models.Model):
    """
    This model represent the agip csv file that defines percentage
    of retentions and perceptions
    """
    _name = 'padron.agip_percentages.rp'
    _inherit = 'padron.agip_percentages'
    _description = 'Definition of percentages of taxes by customer'

    group_retention_id = fields.Many2one(
        'agip.retention.group.rp', 'Retention Group')
    group_perception_id = fields.Many2one(
        'agip.perception.group.rp', 'Perception Group')


class ArbaPerceptions(models.Model):
    """
    This model represent de ARBA csv file that
    defines percentage of perceptions
    """
    _name = 'padron.arba_perception'
    _description = 'Definition of arba percentages of perception'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    vat = fields.Char('Afip code', size=15, index=1)
    percentage = fields.Float('Percentage of perception')
    multilateral = fields.Boolean('Is multilateral?')


class ArbaRetentions(models.Model):
    """
    This model represent de ARBA csv file that
    defines percentage of retention
    """
    _name = 'padron.arba_retention'
    _description = 'Definition of arba percentages of retention'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    vat = fields.Char('Afip code', size=15, index=1)
    percentage = fields.Float('Percentage of retention')
    multilateral = fields.Boolean('Is multilateral?')

class SantaFePerceptions(models.Model):
    """
    This model represent the santa fe csv file that defines percentage
    of retentions and perceptions
    """
    _name = 'padron.santa_fe_percentages'
    _description = 'Definition of percentages of taxes by customer'

    vat = fields.Char('Santa Fe code', size=15, index=1)
    percentage = fields.Float('Alicuota')
    multilateral = fields.Boolean('Is multilateral?')


class JujuyRetentions(models.Model):
    """
    This model represent the agip csv file that defines percentage
    of retentions and perceptions
    """
    _name = 'padron.jujuy_percentages'
    _description = 'Definition of percentages of taxes by customer'

    vat = fields.Char('Jujuy code', size=15, index=1)
    from_date = fields.Date('From date')
    percentage_perception = fields.Float('Percentage of perception')
    percentage_retention = fields.Float('Percentage of retention')
    multilateral = fields.Boolean('Is multilateral?')

class TucumanPercentages(models.Model):

    _name = 'padron.tucuman_acreditan'
    _description = 'Definition of percentages of taxes by customer'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    vat = fields.Char('Afip code', size=15, index=1)
    u1 = fields.Char('E')
    percentage_perception = fields.Float('Percentage of perception')
    sit_iibb = fields.Boolean('Is multilateral?')
    coeficiente = fields.Float("Coeficiente")

class TucumanCoefiecient(models.Model):

    _name = 'padron.tucuman_coeficiente'
    _description = 'Definition of percentages of taxes by customer'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    vat = fields.Char('Afip code', size=15, index=1)
    u1 = fields.Char('E')
    percentage_perception = fields.Float('Percentage of perception')
    sit_iibb = fields.Boolean('Is multilateral?')
    coeficiente = fields.Float("Coeficiente")

class CordobaPerceptions(models.Model):
    """
    This model represent de ARBA csv file that
    defines percentage of perceptions
    """
    _name = 'padron.cordoba_perception'
    _description = 'Definition of arba percentages of perception'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    vat = fields.Char('Afip code', size=15, index=1)
    percentage_perception = fields.Float('Percentage of perception')
    multilateral = fields.Boolean('Is multilateral?')


class res_country_state(models.Model):
    _name = "res.country.state"
    _inherit = "res.country.state"

    jurisdiction_code = fields.Char(string="Jurisdiction Code", size=15)
