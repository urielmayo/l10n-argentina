###############################################################################
#
#    Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    "name": "Base VAT Ar",
    "category": "L10N AR",
    "version": "12.0.1.0.0",
    "author": "Eynes/E-MIPS",
    "license": "AGPL-3",
    "description": "This module provides VAT Checking for Argentina.",
    "depends": [
        "base_vat",
    ],
    "data": [
        'data/res_document_type_data.xml',
        'data/dst_cuit_codes_data.xml',
        'views/partner_view.xml',
        'views/res_document_type_view.xml',
        'views/menuitems.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": True,
}
