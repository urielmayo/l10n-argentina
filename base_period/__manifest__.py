##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

{
    "name": "Base Period",
    "category": "L10N AR",
    "version": "12.0.1.0.0",
    "author": "Eynes/E-MIPS",
    "license": "AGPL-3",
    "description": "Add a monthly period for accounting purposes, "
    "computed from the documents date.",
    "depends": [
        "account",
        "stock",
    ],
    "data": [
        "views/date_period_view.xml",
        "views/account_invoice_view.xml",
        "views/account_move_view.xml",
        "views/stock_inventory_view.xml",
        "views/menuitems.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
