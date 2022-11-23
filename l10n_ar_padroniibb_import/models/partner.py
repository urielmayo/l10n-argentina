##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _compute_sit_iibb(self, padron_tax):
        # TODO Is this the correct thing to do?
        if padron_tax.multilateral:
            multilateral_record = self.env.ref(
                'l10n_ar_point_of_sale.iibb_situation_multilateral')
            sit_iibb = multilateral_record
        else:
            local_record = self.env.ref(
                'l10n_ar_point_of_sale.iibb_situation_local')
            sit_iibb = local_record
        return sit_iibb.id

    @api.model
    def _compute_allowed_padron_tax_commands(self, old_commands, new_commands):
        allowed_to_keep_comms = []
        to_remove_new_comm = []
        padron_tax_ids = [x[1] for x in new_commands]
        for command in old_commands:
            if command[1] not in padron_tax_ids:
                allowed_to_keep_comms.append(command)
            if command[0] == 1 and command[1] in padron_tax_ids:
                vals = command[2].copy()
                vals.pop('percent', False)
                vals.pop('perception_id', False)
                allowed_to_keep_comms.append((1, command[1], vals))
                to_remove_new_comm.append(command[1])
        for command in new_commands:
            if command[1] not in to_remove_new_comm:
                allowed_to_keep_comms.append(command)
        return allowed_to_keep_comms



    @api.model
    def _check_padron_perception_agip(self, vat):
        padron_agip_obj = self.env['padron.agip_percentages']
        perception_obj = self.env['perception.perception']
        per_ids = padron_agip_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_agip()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_perception_agip_rp(self, vat):
        padron_agip_obj = self.env['padron.agip_percentages.rp']
        perception_obj = self.env['perception.perception']
        per_ids = padron_agip_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_agip_rp()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_perception_arba(self, vat):
        padron_arba_per_obj = self.env['padron.arba_perception']
        perception_obj = self.env['perception.perception']
        per_ids = padron_arba_per_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_arba()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'from_padron': True,
                'sit_iibb': sit_iibb,
            }
        return res

    @api.model
    def _check_padron_perception_santa_fe(self, vat):
        padron_santa_fe_obj = self.env['padron.santa_fe_percentages']
        perception_obj = self.env['perception.perception']
        per_ids = padron_santa_fe_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_santa_fe()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_perception_jujuy(self, vat):
        padron_jujuy_obj = self.env['padron.jujuy_percentages']
        perception_obj = self.env['perception.perception']
        per_ids = padron_jujuy_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_jujuy()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_perception_cordoba(self, vat):
        padron_cordoba_obj = self.env['padron.cordoba_perception']
        perception_obj = self.env['perception.perception']
        per_ids = padron_cordoba_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_cordoba()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_perception_tucuman_acreditan(self, vat):
        padron_tucuman_obj = self.env['padron.tucuman_acreditan']
        perception_obj = self.env['perception.perception']
        per_ids = padron_tucuman_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_tucuman()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res
    @api.model
    def _check_padron_perception_tucuman_coeficiente(self, vat):
        padron_tucuman_obj = self.env['padron.tucuman_coeficiente']
        perception_obj = self.env['perception.perception']
        per_ids = padron_tucuman_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_tucuman()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.coeficiente,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_perception_formosa(self, vat):
        padron_formosa_obj = self.env['padron.formosa']
        perception_obj = self.env['perception.perception']
        per_ids = padron_formosa_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if per_ids:
            percep_ids = perception_obj._get_perception_from_formosa()
            if not percep_ids:
                return res
            padron_percep = per_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_percep)
            res = {
                'perception_id': percep_ids[0].id,
                'percent': padron_percep.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res



    @api.model
    def _check_padron_retention_agip(self, vat):
        padron_agip_obj = self.env['padron.agip_percentages']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_agip_obj.search([('vat', '=', vat)])
        res = {}
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_agip()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_retention,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_retention_agip_rp(self, vat):
        padron_agip_obj = self.env['padron.agip_percentages.rp']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_agip_obj.search([('vat', '=', vat)])
        res = {}
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_agip_rp()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_retention,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_retention_arba(self, vat):
        padron_arba_ret_obj = self.env['padron.arba_retention']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_arba_ret_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_arba()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_retention,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_retention_santa_fe(self, vat):
        padron_santa_fe_ret_obj = self.env['padron.santa_fe_percentages']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_santa_fe_ret_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_santa_fe()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_retention,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_retention_jujuy(self, vat):
        padron_jujuy_ret_obj = self.env['padron.jujuy_percentages']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_jujuy_ret_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_jujuy()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_retention,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res
    @api.model
    def _check_padron_retention_tucuman_acreditan(self, vat):
        padron_tucuman_ret_obj = self.env['padron.tucuman_acreditan']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_tucuman_ret_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_tucuman()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_perception,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res

    @api.model
    def _check_padron_retention_tucuman_coeficiente(self, vat):
        padron_tucuman_ret_obj = self.env['padron.tucuman_coeficiente']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_tucuman_ret_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_tucuman()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.coeficiente,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res
        
    @api.model
    def _check_padron_retention_formosa(self, vat):
        padron_formosa_ret_obj = self.env['padron.formosa']
        retention_obj = self.env['retention.retention']
        ret_ids = padron_formosa_ret_obj.search([('vat', '=', vat)])
        res = {}
        # TODO: Chequear vigencia
        if ret_ids:
            retent_ids = retention_obj._get_retention_from_formosa()
            if not retent_ids:
                return res
            padron_retent = ret_ids[0]
            sit_iibb = self._compute_sit_iibb(padron_retent)
            res = {
                'retention_id': retent_ids[0].id,
                'percent': padron_retent.percentage_retention,
                'sit_iibb': sit_iibb,
                'from_padron': True,
            }
        return res


    @api.model
    def create(self, vals):
        # Percepciones
        if 'customer' in vals and vals['customer']:
            if 'vat' in vals and vals['vat']:
                vat = vals['vat']
                perceptions_list = []
                perc_arba = self._check_padron_perception_arba(vat)
                if perc_arba:
                    perceptions_list.append((0, 0, perc_arba))

                perc_agip = self._check_padron_perception_agip(vat)
                if perc_agip:
                    perceptions_list.append((0, 0, perc_agip))

                perc_agip_rp = self._check_padron_perception_agip_rp(vat)
                if perc_agip_rp:
                    perceptions_list.append((0, 0, perc_agip_rp))

                perc_santa_fe = self._check_padron_perception_santa_fe(vat)
                if perc_santa_fe:
                    perceptions_list.append((0, 0, perc_santa_fe))

                perc_jujuy = self._check_padron_perception_jujuy(vat)
                if perc_jujuy:
                    perceptions_list.append((0, 0, perc_jujuy))

                perc_cordoba = self._check_padron_perception_cordoba(vat)
                if perc_cordoba:
                    perceptions_list.append((0, 0, perc_cordoba))

                perc_tucuman_ac = self._check_padron_perception_tucuman_acreditan(vat)
                if perc_tucuman_ac:
                    perceptions_list.append((0, 0, perc_tucuman_ac))

                perc_tucuman_co = self._check_padron_perception_tucuman_coeficiente(vat)
                if perc_tucuman_co:
                    perceptions_list.append((0, 0, perc_tucuman_co))

                perc_formosa = self._check_padron_perception_formosa(vat)
                if perc_formosa:
                    perceptions_list.append((0, 0, perc_formosa))

                vals['perception_ids'] = perceptions_list


        # Retenciones
        if 'supplier' in vals and vals['supplier']:
            if 'vat' in vals and vals['vat']:
                vat = vals['vat']
                retentions_list = []
                ret_arba = self._check_padron_retention_arba(vat)
                if ret_arba:
                    retentions_list.append((0, 0, ret_arba))

                ret_agip = self._check_padron_retention_agip(vat)
                if ret_agip:
                    retentions_list.append((0, 0, ret_agip))

                ret_agip_rp = self._check_padron_retention_agip_rp(vat)
                if ret_agip_rp:
                    retentions_list.append((0, 0, ret_agip_rp))

                ret_santa_fe = self._check_padron_retention_santa_fe(vat)
                if ret_santa_fe:
                    retentions_list.append((0, 0, ret_santa_fe))

                ret_jujuy = self._check_padron_retention_jujuy(vat)
                if ret_jujuy:
                    retentions_list.append((0, 0, ret_jujuy))

                ret_tucuman_ac = self._check_padron_retention_tucuman_acreditan(vat)
                if ret_tucuman_ac:
                    retentions_list.append((0, 0, ret_tucuman_ac))

                ret_tucuman_co = self._check_padron_retention_tucuman_coeficiente(vat)
                if ret_tucuman_co:
                    retentions_list.append((0, 0, ret_tucuman_co))

                ret_formosa = self._check_padron_retention_formosa(vat)
                if ret_formosa:
                    retentions_list.append((0, 0, ret_formosa))

                vals['retention_ids'] = retentions_list

        return super(res_partner, self).create(vals)

    @api.multi
    def _update_retention_partner(self, retention):
        self.ensure_one()
        partner_retention_obj = self.env['res.partner.retention']
        res = {}
        retention_id = retention['retention_id']

        partner_retention_ids = partner_retention_obj.search([
            ('partner_id', '=', self.id),
            ('retention_id', '=', retention_id),
            ('activity_id', '=', False)])

        if len(partner_retention_ids) > 1:
            raise ValidationError(
                _("Retention Error!\n") +
                _("Partner already has the retention more than one"))

        if not partner_retention_ids:
            res['retention_ids'] = [(0, 0, retention)]
        else:
            ret_id = partner_retention_ids[0]
            res['retention_ids'] = [(1, ret_id.id, retention)]

        return res

    @api.multi
    def _update_perception_partner(self, perception):
        self.ensure_one()
        partner_perception_obj = self.env['res.partner.perception']
        res = {}
        perception_id = perception['perception_id']

        partner_perception_ids = partner_perception_obj.search([
            ('partner_id', '=', self.id),
            ('perception_id', '=', perception_id)])

        if len(partner_perception_ids) > 1:
            raise ValidationError(
                _("Perception Error!\n") +
                _("Partner already has the perception more than once"))

        if not partner_perception_ids:
            res['perception_ids'] = [(0, 0, perception)]
        else:
            per_id = partner_perception_ids[0]
            res['perception_ids'] = [(1, per_id.id, perception)]
        return res

    @api.multi
    def write(self, vals):
        for partner in self:
            vat_changed = False
            if 'vat' in vals and vals['vat']:
                vat = vals['vat']
                old_vat = partner.read(['vat'])[0]['vat']
                if vat != old_vat:
                    vat_changed = True
            else:
                vat = partner.read(['vat'])[0]['vat']

            if 'customer' in vals and vals['customer']:
                customer = vals['customer']
            else:
                customer = partner.read(['customer'])[0]['customer']

            if 'supplier' in vals and vals['supplier']:
                supplier = vals['supplier']
            else:
                supplier = partner.read(['supplier'])[0]['supplier']

            # TODO: Hay como un problema entre este metodo
            # y la actualizacion masiva
            # Tenemos que corregirlo de alguna manera,
            # por ahora el workaround es que si se escribe las perception_ids
            # no se hace el chequeo en el padron
            # porque suponemos que viene de la actualizacion masiva
            if vat:
                if customer:

                    perception_ids_lst = []
                    perc_arba = partner._check_padron_perception_arba(vat)
                    if perc_arba:
                        res_arba = partner._update_perception_partner(
                            perc_arba)
                        perception_ids_lst.append(
                            res_arba['perception_ids'][0])

                    perc_agip = partner._check_padron_perception_agip(vat)
                    if perc_agip:
                        res_agip = partner._update_perception_partner(
                            perc_agip)
                        perception_ids_lst.append(
                            res_agip['perception_ids'][0])

                    perc_agip_rp = partner._check_padron_perception_agip_rp(vat)
                    if perc_agip_rp:
                        res_agip_rp = partner._update_perception_partner(
                            perc_agip_rp)
                        perception_ids_lst.append(
                            res_agip_rp['perception_ids'][0])

                    perc_santa_fe = partner._check_padron_perception_santa_fe(vat)
                    if perc_santa_fe:
                        res_santa_fe = partner._update_perception_partner(
                            perc_santa_fe)
                        perception_ids_lst.append(
                            res_santa_fe['perception_ids'][0])

                    perc_jujuy = partner._check_padron_perception_jujuy(vat)
                    if perc_jujuy:
                        res_jujuy = partner._update_perception_partner(
                            perc_jujuy)
                        perception_ids_lst.append(
                            res_jujuy['perception_ids'][0])

                    perc_cordoba = partner._check_padron_perception_cordoba(vat)
                    if perc_cordoba:
                        res_cordoba = partner._update_perception_partner(
                            perc_cordoba)
                        perception_ids_lst.append(
                            res_cordoba['perception_ids'][0])

                    perc_tucuman_ac = partner._check_padron_perception_tucuman_acreditan(vat)
                    if perc_tucuman_ac:
                        res_tucuman_ac = partner._update_perception_partner(
                            perc_tucuman_ac)
                        perception_ids_lst.append(
                            res_tucuman_ac['perception_ids'][0])

                    perc_tucuman_co = partner._check_padron_perception_tucuman_coeficiente(vat)
                    if perc_tucuman_co:
                        res_tucuman_co = partner._update_perception_partner(
                            perc_tucuman_co)
                        perception_ids_lst.append(
                            res_tucuman_co['perception_ids'][0])

                    perc_formosa = partner._check_padron_perception_formosa(vat)
                    if perc_formosa:
                        res_formosa = partner._update_perception_partner(
                            perc_formosa)
                        perception_ids_lst.append(
                            res_formosa['perception_ids'][0])

                    if 'perception_ids' in vals:
                        real_comms = self._compute_allowed_padron_tax_commands(
                            vals['perception_ids'], perception_ids_lst)
                    else:
                        real_comms = perception_ids_lst
                    if vat_changed:
                        old_perceps = partner.read(
                            ['perception_ids'])[0]['perception_ids']
                        old_comms = [(2, x, False) for x in old_perceps]
                        keep_percep_comms = []
                        for comm in perception_ids_lst:
                            if comm[1] not in old_perceps:
                                keep_percep_comms.append(comm)
                        real_comms = keep_percep_comms + old_comms
                    vals.update({
                        'perception_ids': real_comms,
                    })

                if supplier:

                    retention_ids_lst = []
                    ret_arba = partner._check_padron_retention_arba(vat)
                    if ret_arba:
                        res_arba = partner._update_retention_partner(ret_arba)
                        retention_ids_lst.append(res_arba['retention_ids'][0])

                    ret_agip = partner._check_padron_retention_agip(vat)
                    if ret_agip:
                        res_agip = partner._update_retention_partner(ret_agip)
                        retention_ids_lst.append(res_agip['retention_ids'][0])

                    ret_agip_rp = partner._check_padron_retention_agip_rp(vat)
                    if ret_agip_rp:
                        res_agip_rp = partner._update_retention_partner(ret_agip_rp)
                        retention_ids_lst.append(res_agip_rp['retention_ids'][0])

                    ret_santa_fe = partner._check_padron_retention_santa_fe(vat)
                    if ret_santa_fe:
                        res_santa_fe = partner._update_retention_partner(ret_santa_fe)
                        retention_ids_lst.append(res_santa_fe['retention_ids'][0])

                    ret_jujuy = partner._check_padron_retention_jujuy(vat)
                    if ret_jujuy:
                        res_jujuy = partner._update_retention_partner(ret_jujuy)
                        retention_ids_lst.append(res_jujuy['retention_ids'][0])

                    ret_tucuman_ac = partner._check_padron_retention_tucuman_acreditan(vat)
                    if ret_tucuman_ac:
                        res_tucuman_ac = partner._update_retention_partner(ret_tucuman_ac)
                        retention_ids_lst.append(res_tucuman_ac['retention_ids'][0])

                    ret_tucuman_co = partner._check_padron_retention_tucuman_coeficiente(vat)
                    if ret_tucuman_co:
                        res_tucuman_co = partner._update_retention_partner(ret_tucuman_co)
                        retention_ids_lst.append(res_tucuman_co['retention_ids'][0])

                    ret_formosa = partner._check_padron_retention_formosa(vat)
                    if ret_formosa:
                        res_formosa = partner._update_retention_partner(ret_formosa)
                        retention_ids_lst.append(res_formosa['retention_ids'][0])

                    if 'retention_ids' in vals:
                        real_comms = self._compute_allowed_padron_tax_commands(
                            vals['retention_ids'], retention_ids_lst)
                    else:
                        real_comms = []
                    if vat_changed:
                        old_retent = partner.read(
                            ['retention_ids'])[0]['retention_ids']
                        old_comms = [(2, x, False) for x in old_retent]
                        keep_retent_comms = []
                        for comm in retention_ids_lst:
                            if comm[1] not in old_retent:
                                keep_retent_comms.append(comm)
                        real_comms = keep_retent_comms + old_comms
                    vals.update({
                        'retention_ids': real_comms,
                    })
        return super(res_partner, self).write(vals)


class res_partner_perception(models.Model):
    _name = "res.partner.perception"
    _inherit = "res.partner.perception"

    from_padron = fields.Boolean(string="From Padron")


class res_partner_retention(models.Model):
    _name = "res.partner.retention"
    _inherit = "res.partner.retention"

    from_padron = fields.Boolean(string="From Padron")
