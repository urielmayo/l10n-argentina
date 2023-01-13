from odoo import api, models

class PerceptionPerception(models.Model):
    _inherit = 'perception.perception'

    @api.model
    def create_perceptions_from_partner(self, partner, date=False, **kwargs):
        # when partner is not in agip rp padron but has cm05 from CABA
        # so partner doesnt have agip rp perception
        # agip rp perception tax is added into the invoice
        # and the percentage depends on cm05 bool
        
        perc = super(PerceptionPerception, self).create_perceptions_from_partner(partner, date, **kwargs)

        if partner.perception_ids.filtered(lambda r: r.perception_id.from_register == 'agip_rp'):   #if partner have a perception from agip_rp
            return

        caba_cm05 = partner.cm05.filtered(lambda r: r.province_id.jurisdiction_code == '901')   # check if partner have a cm05 of Ciudad Autonoma de Buenos Aires
        if not caba_cm05:
            return

        agip_rp = self.env['perception.perception'].search([('type_tax_use', '=', 'sale'),('from_register', '=', 'agip_rp')])

        if not caba_cm05.inscrito:
            tax = agip_rp.gi_application_ids.filtered(lambda r: r.sit_iibb.name == 'No Inscripto')       
        else:
            tax = agip_rp.gi_application_ids.filtered(lambda r: r.sit_iibb.name != 'No Inscripto')[0]

        if not tax:
            return

        perception_tax_line = {
            'perception': agip_rp.id,
            'activity_id': tax.activity_id.id,
            'excluded_percent': 0,
            'percent': tax.percent,
            'sit_iibb': tax.sit_iibb,
            'from_padron': False,
        }

        res = agip_rp.compute(perception_tax_line, **kwargs)
        if res:
            perc += res
        return perc