##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

{
    "name": "Point of Sale",
    "category": "L10N AR",
    "version": "12.0.1.0.0",
    "author": "Eynes/E-MIPS",
    "license": "AGPL-3",
    "description": "Basic Normatives for Argentina's invoicing system",
    "depends": [
        "sale_stock",
        "purchase",
        "account_voucher",
        "base_vat_ar",
    ],
    "data": [
        "views/invoice_denomination_view.xml",
        "views/pos_ar_view.xml",
        "views/account_invoice_view.xml",
        "views/partner_view.xml",
        "views/account_view.xml",
        "views/iibb_situation_view.xml",
        "views/res_users_view.xml",
        "views/menuitems.xml",
        "security/pos_ar_rule.xml",
        "security/ir.model.access.csv",
        "data/partner_data.xml",
        "data/iibb_situation_data.xml",
    ],
    "installable": True,
    "application": True,
}
