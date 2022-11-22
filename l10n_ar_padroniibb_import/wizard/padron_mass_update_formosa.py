##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PadronMassUpdateFormosa(models.TransientModel):
    _name = 'padron.mass.update.formosa'
    _description = 'Padron Mass Update Formosa'

    formosa = fields.Boolean('Update FORMOSA')

    # Retencion formosa
    @api.model
    def _update_retention_formosa(self, retention):
        cr = self.env.cr
        query = """
        WITH padron AS (
            SELECT
                rp.id p_partner_id,
                par.ac_ret_28_97 p_percentage
            FROM res_partner rp
                JOIN padron_formosa par ON par.vat=rp.vat
            WHERE
                rp.parent_id IS NULL
                AND rp.supplier
        ),
        retentions AS (
            SELECT
                rpr.id r_id,
                rpr.partner_id r_partner_id,
                rpr.percent r_percentage
            FROM res_partner_retention rpr
            WHERE rpr.retention_id=%s
        )
        SELECT * FROM (SELECT padron.*, retentions.*,
            CASE
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NOT NULL)
                    AND (p_percentage <> r_percentage)
                    THEN 'UPDATE'  -- In padron and sys
                WHEN (p_partner_id IS NOT NULL)
                    AND (r_partner_id IS NOT NULL)
                    AND (p_percentage = r_percentage)
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
                FULL JOIN retentions
                ON retentions.r_partner_id=padron.p_partner_id) z
        WHERE umode != 'NONE';
        """

        params = (retention.id, )
        cr.execute(query, params)

        for res in cr.fetchall():
            if res[6] == 'UPDATE':  # Change the amount of percentage
                q = """
                UPDATE res_partner_retention SET
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
                UPDATE res_partner_retention SET
                    percent=%(percent)s,
                    from_padron = True
                WHERE id=%(id)s
                """
                q_params = {
                    'percent': -1,
                    'id': res[3],
                }
                self._cr.execute(q, q_params)
            elif res[6] == 'CREATE':  # Create the res.partner.retention
                q = """
                INSERT INTO res_partner_retention (
                    partner_id,
                    percent,
                    retention_id,
                    from_padron
                ) VALUES (
                    %(partner_id)s,
                    %(percent)s,
                    %(retention_id)s,
                    True
                )"""
                q_params = {
                    'percent': res[1],
                    'partner_id': res[0],
                    'retention_id': retention.id,

                }
                self._cr.execute(q, q_params)
            else:
                e_title = _('Query Error\n')
                e_msg = _('Unexpected result: %s' % str(res))
                raise ValidationError(e_title + e_msg)


    @api.multi
    def action_update_formosa(self):
        retention_obj = self.env['retention.retention']

        if self.formosa:
            # Actualizamos Percepciones

            retent_formosa = retention_obj._get_retention_from_formosa()
            if not retent_formosa:
                raise ValidationError(
                    _("Retention Error!\n") +
                    _("There is no retention configured to update " +
                      "from Padron FORMOSA"))
            self._update_retention_formosa(retent_formosa[0])
        return True

