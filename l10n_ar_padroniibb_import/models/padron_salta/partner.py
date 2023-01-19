from odoo import api, models

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _check_padron_perception_salta(self, vat):
        padron_salta_obj = self.env['padron.salta']
        perception_obj = self.env['perception.perception']
        per_ids = padron_salta_obj.search([('vat', '=', vat)])
        res = {}
        if per_ids:
            percep_ids = perception_obj._get_perception_from_salta()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            #TODO sit iibb
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'from_padron': True,
            }
        return res

    @api.model
    def create(self, vals):
        # perception
        if 'customer' in vals and vals['customer']:
            if 'vat' in vals and vals['vat']:
                vat = vals['vat']
                perceptions_list = []
                perc_salta = self._check_padron_perception_salta(vat)
                if perc_salta:
                    perceptions_list.append((0, 0, perc_salta))

                vals['perception_ids'] = perceptions_list

        return super(res_partner, self).create(vals)

    @api.multi
    def write(self, vals):
        for partner in self:
            partner_data = self.get_partner_change_data(vals, partner)
            
            if not partner_data['vat']:
                continue
            if partner_data['customer']:
                perception_ids_lst = []
                perc_salta = partner._check_padron_perception_salta(partner_data['vat'])

                if perc_salta:
                    res_salta = partner._update_perception_partner(
                        perc_salta)
                    perception_ids_lst.append(
                        res_salta['perception_ids'][0])

                vals = self.update_perceptions(vals, partner, partner_data, perception_ids_lst)
        return super(res_partner, self).write(vals)