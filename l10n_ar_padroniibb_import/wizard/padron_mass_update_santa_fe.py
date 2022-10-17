##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PadronMassUpdateSantaFe(models.TransientModel):
    _name = 'padron.mass.update.santafe'
    _description = 'Padron Mass Update Santa FE'

    santa_fe = fields.Boolean('Update SANTA FE')

    # Percepcion Santa Fe
    @api.model
    def _update_perception_santa_fe(self, perception):
        cr = self.env.cr
        query = """
        WITH padron AS (
            SELECT
                rp.id p_partner_id,
                par.percentage_perception p_percentage,
            FROM res_partner rp
                JOIN padron_santa_fe_percentages par ON par.vat=rp.vat
            WHERE
                rp.parent_id IS NULL
                AND rp.customer
        ),
        perceptions AS (
            SELECT
                rpr.id r_id,
                rpr.partner_id r_partner_id,
                rpr.percent r_percentage
            FROM res_partner_perception rpr
            WHERE rpr.perception_id=%s
        )
        SELECT * FROM (SELECT padron.*, perceptions.*,
            CASE
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NOT NULL)
                    AND (p_percentage <> r_percentage)
                    THEN 'UPDATE'  -- In padron and sys
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NOT NULL)
                    AND (p_percentage = r_percentage)
                    THEN 'NONE'  -- In padron and sys but same percent
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NULL)
                    THEN 'CREATE'  -- In padron not in sys
                WHEN (p_partner_id IS NULL)
                    AND (r_partner_id IS NOT NULL)
                    THEN 'DELETE'  -- Not in padron but in sys
                ELSE 'ERROR' -- Never should enter here
            END umode
            FROM padron
                FULL JOIN perceptions
                ON perceptions.r_partner_id=padron.p_partner_id) z
        WHERE umode != 'NONE';
        """
        params = (perception.id, )
        cr.execute(query, params)
        for res in cr.fetchall():
            if res[6] == 'UPDATE':  # Change the amount of percentage
                q = """
                UPDATE res_partner_perception SET
                    percent=%(percent)s,
                    from_padron = True
                WHERE id=%(id)s
                """
                q_params = {
                    'percent': res[1],
                    'id': res[3],
                }
                self._cr.execute(q, q_params)
            elif res[6] == 'DELETE':   # Set the percentage to -1
                q = """
                UPDATE res_partner_perception SET
                    percent=%(percent)s,
                    from_padron = True
                WHERE id=%(id)s
                """
                q_params = {
                    'percent': -1,
                    'id': res[3],
                }
                self._cr.execute(q, q_params)
            elif res[6] == 'CREATE':  # Create the res.partner.perception
                q = """
                INSERT INTO res_partner_perception (
                    partner_id,
                    percent,
                    perception_id,
                    from_padron
                ) VALUES (3
                    %(partner_id)s,
                    %(percent)s,
                    %(perception_id)s,
                    True
                )"""
                q_params = {
                    'percent': res[1],
                    'partner_id': res[0],
                    'perception_id': perception.id,
                }
                self._cr.execute(q, q_params)
            else:
                e_title = _('Query Error\n')
                e_msg = _('Unexpected result: %s' % str(res))
                raise ValidationError(e_title + e_msg)
    @api.multi
    def action_update_santa_fe(self):
        perception_obj = self.env['perception.perception']
        if self.santa_fe:
            # Actualizamos Percepciones
            percep_santa_fe = perception_obj._get_perception_from_santa_fe()
            if not percep_santa_fe:
                raise ValidationError(
                    _("Perception Error!\n") +
                    _("There is no perception configured to update " +
                      "from Padron SANTA FE"))
            self._update_perception_santa_fe(percep_santa_fe[0])
        return True

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _compute_sit_iibb_santa_fe(self, padron_tax):
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
    def _compute_allowed_padron_tax_commands_santa_fe(self, old_commands, new_commands):
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
    def create_santa_fe(self, vals):
        # Percepciones
        if 'customer' in vals and vals['customer']:
            if 'vat' in vals and vals['vat']:
                vat = vals['vat']
                perceptions_list = []
                perc_santa_fe = self._check_padron_perception_santa_fe(vat)
                if perc_santa_fe:
                    perceptions_list.append((0, 0, perc_santa_fe))

                vals['perception_ids'] = perceptions_list

    @api.multi
    def write_santa_fe(self, vals):
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
            # TODO: Hay como un problema entre este metodo
            # y la actualizacion masiva
            # Tenemos que corregirlo de alguna manera,
            # por ahora el workaround es que si se escribe las perception_ids
            # no se hace el chequeo en el padron
            # porque suponemos que viene de la actualizacion masiva
            if vat:
                if customer:
                    # Obtenemos la percepcion desde el
                    # padron de percepciones de ARBA
                    perception_ids_lst = []

                    perc_santa_fe = partner._check_padron_perception_santa_fe(vat)
                    if perc_santa_fe:
                        res_santa_fe = partner._update_perception_partner(
                            perc_santa_fe)
                        perception_ids_lst.append(
                            res_santa_fe['perception_ids'][0])

                    if 'perception_ids' in vals:
                        real_comms = self._compute_allowed_padron_tax_commands_santa_fe(
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


        return super(res_partner, self).write(vals)


class res_partner_perception(models.Model):
    _name = "res.partner.perception"
    _inherit = "res.partner.perception"

    from_padron = fields.Boolean(string="From Padron")


class res_partner_retention(models.Model):
    _name = "res.partner.retention"
    _inherit = "res.partner.retention"

    from_padron = fields.Boolean(string="From Padron")
