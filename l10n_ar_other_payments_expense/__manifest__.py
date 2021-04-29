###############################################################################
#
#    Copyright (c) 2021 Eynes (www.eynes.com.ar)
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
    "name": "Other Payments Expense",
    "category": "L10N AR",
    "version": "12.0.1.0.0",
    "author": "Eynes",
    "license": "AGPL-3",
    "description": "Extension of payment module, to be able to register expenses.",  # noqa
    "depends": [
        "l10n_ar_other_payments",
    ],
    "data": [
        # ~ "security/ir.model.access.csv",
        "views/payment_order_view.xml",
    ],
    "installable": True,
    "application": True,
}
