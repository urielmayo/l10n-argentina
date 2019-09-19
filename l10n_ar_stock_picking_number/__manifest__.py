##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 E-MIPS (http://www.e-mips.com.ar)
#    Copyright (c) 2018 Eynes Ingenieria del software (http://www.eynes.com.ar)
#    Copyright (c) 2018 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Numeracion Remitos Argentina',
    'version': '12.0.1.0.0',
    'summary': 'Numeracion Remitos Argentina',
    'author': "E-MIPS/Eynes",
    'maintainer': 'E-MIPS/Eynes',
    'company': "E-MIPS/Eynes",
    'website': "http://www.proyectoaconcagua.com.ar",
    'depends': ['stock'],
    'category': 'Localization',
    'data': [
        'wizard/cancel_picking_done_view.xml',
        'views/stock_view.xml',
        'data/sequence.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
