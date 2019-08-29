##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import models


class ResCountryState(models.Model):

    _inherit = 'res.country.state'

    # Check for repeated state names, based on the country name; avoiding repeated values
    # (name,zip_code) for each country
    _sql_constraints = [
        (
            'unique_state_name',
            'UNIQUE (country_id, name)',
            'Repeated state name. Please check the states list.'
        )
    ]
