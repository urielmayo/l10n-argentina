##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PadronMassUpdateSalta(models.TransientModel):
    _name = 'padron.mass.update.salta'
    _description = 'Padron Mass Update Salta'

    salta = fields.Boolean('Update SALTA')

    # Retencion formosa
    @api.model
    def _update_perception_salta(self, perception):
        cr = self.env.cr
        cr.commit()
        query = """
        WITH padron AS (
            SELECT
                rp.id p_partner_id,
                par.percentage_perception p_percentage
            FROM res_partner rp
                JOIN padron_salta par ON par.vat=rp.vat
            WHERE
                rp.parent_id IS NULL
                AND rp.customer
        ),
        perceptions AS (
            SELECT
                rpp.id r_id,
                rpp.partner_id r_partner_id,
                rpp.percent per_percentage
            FROM res_partner_perception rpp
            WHERE rpp.perception_id=%s
        )
        SELECT * FROM (SELECT padron.*, perceptions.*,
            CASE
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NOT NULL)
                    AND (p_percentage <> per_percentage)
                    THEN 'UPDATE'  -- In padron and sys
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NOT NULL)
                    AND (p_percentage = per_percentage)
                    THEN 'NONE'  -- In padron and sys but same percent
                WHEN (p_partner_id IS NOT NULL) AND
                    (r_partner_id IS NULL)
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
            if res[5] == 'UPDATE':  # Change the amount of percentage
                q = """
                UPDATE res_partner_perception SET
                    percent=%(percent)s,
                    from_padron = True
                WHERE id=%(id)s
                """
                q_params = {
                    'percent': res[1],
                    'partner_id': res[0],
                    'id': res[2],
                }
                self._cr.execute(q, q_params)
            elif res[5] == 'DELETE':   # Set the percentage to -1
                q = """
                UPDATE res_partner_perception SET
                    percent=%(percent)s,
                    from_padron = True
                WHERE id=%(id)s
                """
                q_params = {
                    'percent': -1,
                    'partner_id': res[0],
                    'id': res[2],
                }
                self._cr.execute(q, q_params)
            elif res[5] == 'CREATE':  # Create the res.partner.perception
                q = """
                INSERT INTO res_partner_perception (
                    partner_id,
                    percent,
                    perception_id,
                    from_padron
                ) VALUES (
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
    def action_update_salta(self):
        perception_obj = self.env['perception.perception']
        
        if self.salta:
            # Actualizamos Percepciones
            percept_salta = perception_obj._get_perception_from_salta()
            if not percept_salta:
                raise ValidationError(
                    _("Perception Error!\n") +
                    _("There is no perception configured to update " +
                      "from Padron SALTA"))
            self._update_perception_salta(percept_salta[0])
        return True

