##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosAr(models.Model):

    _name = "pos.ar"
    _description = "Point of Sale for Argentina"

    name = fields.Char(string='Number', required=True, size=5)
    number = fields.Integer(
        string='Number',
        compute="_calc_number",
    )
    desc = fields.Char(string='Description', required=False, size=100)
    priority = fields.Integer(string='Priority', required=True, size=6)
    shop_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
    )
    denomination_ids = fields.Many2many(
        comodel_name='invoice.denomination',
        relation='posar_denomination_rel',
        column1='pos_ar_id',
        column2='denomination_id',
        string='Denominations',
    )
    show_in_reports = fields.Boolean('Show in reports?', default=True)
    activity_start_date = fields.Date(
        string="Activity Start Date",
        required=True,
    )
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id,
        required=True,
    )
    image = fields.Binary("Image", attachment=True)

    @api.multi
    def name_get(self):
        res = []
        for pos in self:
            if pos.desc:
                name = '{} ({})'.format(pos.name, pos.desc)
            else:
                name = pos.name

            res.append((pos.id, name))

        return res

    @api.depends("name")
    def _calc_number(self):
        for pos in self:
            try:
                number = int(pos.name)
            except ValueError:
                number = 0

            pos.number = number

    @api.constrains('name')
    def _check_pos_name(self):
        """Checks that names are digits between [1, 99999]."""

        # Matches all-digits name from 1 to 99999
        for pos in self:
            if not pos.name or not pos.name.isdigit():
                raise ValidationError(
                        _("Error! The PoS Name should be a Number"))

            if not(0 < int(pos.name) <= 99999):
                err = _("Error!\nThe PoS Name should be a Number Between 1 and 99999!")
                raise ValidationError(err)

            #Only 4 or 5 characters
            if not (4 <= len(pos.name) <= 5):
                raise ValidationError(_("The PoS Name should be a 4-5 digit number!"))

            #check duplicated
            regs = self.search([
                ('name', '=', pos.name),
                ('id', '!=', pos.id),
            ])
            if regs:
                raise ValidationError(_("Error! The PoS is duplicated"))

    @api.multi
    def unlink(self):
        affected_models = [
            'account.invoice',
        ]
        affected_models = self._hook_affected_models(affected_models)
        self._check_affected_models(affected_models)

        return super().unlink()

    @api.multi
    def _hook_affected_models(self, affected_models):
        return affected_models

    @api.multi
    def _check_affected_models(self, affected_models):
        for record in self:
            search_dict = {}
            for model in affected_models:
                searched = self.env[model].search([
                    ('pos_ar_id', '=', record.id)
                ])
                if searched:
                    search_dict[model] = searched

            if search_dict:
                raise ValidationError(
                    _("Error\n You can not unlink a point of sale with "
                      "associates records.\n Found this ones:\n%s\n"
                      " For point of sale %s [ %s ]. ") %
                    (("\n").join(
                        [repr(x.sorted()) for x in search_dict.values()]),
                     record.name, record))
