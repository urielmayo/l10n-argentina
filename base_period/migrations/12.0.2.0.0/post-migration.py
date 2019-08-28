##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from openupgradelib import openupgrade

__name__ = u"Merge base_period with close_date_period addons"


def merge_addons(cr):
    return openupgrade.update_module_names(
        cr,
        [
            ('close_date_period', 'base_period'),
        ],
        merge_modules=True,
    )


def migrate(cr, version):
    return merge_addons(cr)
