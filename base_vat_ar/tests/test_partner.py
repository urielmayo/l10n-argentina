import pytest
import random
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.addons.base.models import ir_sequence


class TestStockPicking:

    def create_res_partner(self, RP, name=False, vat=False,
                           document_type_id=False, country_id=False):
        name = random.randint(0, 800) if not name else name
        vat = random.randint(0, 100) if not vat else vat
        return RP.create({
            'name': name,
            'vat': vat,
            'document_type_id': document_type_id,
            'country_id': country_id
        })

    def test_get_website_sale_documents(self, RDT):
        # This method (get_website_sale_documents) return
        # 3 res.document.type: cuit, cuil and dni
        res_document_type = RDT.get_website_sale_documents()
        name = res_document_type.mapped('name')
        assert name == ['CUIT', 'CUIL', 'DNI']

    def test_check_vat_duplicated(self, RP, RDT):
        # We create a res.partner with a document_type who has
        # chekc_duplicated boolean in True
        document_type = RDT.env.ref('base_vat_ar.document_cuit')
        self.create_res_partner(RP, 'rp1', '12345678911', document_type.id)
        with pytest.raises(ValidationError,
                           match=".*is another partner with same VAT.*"):
            self.create_res_partner(RP, 'rp2', '12345678911', document_type.id)
        # Here we add a context because for some reason if in the context
        # there is from_website in true the function skip the partner
        ctx = {'from_website': True}
        RP.with_context(ctx).create({'name': 'rp3', 'vat': '12345678'})

    def test_check_vat_string(self, RP, RDT):
        document_type = RDT.env.ref('base_vat_ar.document_cuit')
        res_partner = self.create_res_partner(
            RP, 'rp1', '12345678911', document_type.id
        )
        # Here we check that if we put '-' or '.' in the vat the
        # function will remove them
        res_partner.write({'vat': '12-13145612-1'})
        assert res_partner.vat == '12131456121'
        res_partner.write({'name': 'rp11'})
        # and this is because the function only replace '-' and '.'
        # and not other characters, so we check that if there is other
        # the function will raise an exception
        with pytest.raises(ValidationError,
                           match=".*Vat only supports numbers.*"):
            res_partner.write({'vat': '12_13145612_1'})

    def test_check_vat(self, env, RP, RDT):
        document_type_cuit = RDT.env.ref('base_vat_ar.document_cuit')
        document_type_dni = RDT.env.ref('base_vat_ar.document_dni')
        res_partner = self.create_res_partner(
            RP, 'rp1', document_type_cuit.id
        )
        res_partner = self.create_res_partner(RP, 'rp1', document_type_cuit.id)
        res_partner.write({'vat': '12345678911'})
        res_partner.write({
            'document_type_id': document_type_dni.id
        })
        match_msg = ".*Vat does not seems to be correct.*"
        with pytest.raises(ValidationError, match=match_msg):
            self.create_res_partner(
                RP, 'rp2', 'ar12345678',
                document_type_cuit.id
            )
        with pytest.raises(ValidationError, match=match_msg):
            self.create_res_partner(
                RP, 'rp2', 'arar123456781',
                document_type_cuit.id
            )
        self.create_res_partner(RP, 'rp3', 'ar24880548227')
        country_id = env.ref('base.ar').id
        self.create_res_partner(
            RP, 'rp4', '24880548227',
            country_id=country_id
        )
        with pytest.raises(ValidationError, match=match_msg):
            self.create_res_partner(
                RP, 'rp5', 'ar123456781',
                document_type_cuit.id,
                country_id=country_id
            )

    def test_check_vat_ar(self, RP, RDT):
        document_type_cuit = RDT.env.ref('base_vat_ar.document_cuit')
        document_type_cuil = RDT.env.ref('base_vat_ar.document_cuil')
        document_type_dni = RDT.env.ref('base_vat_ar.document_dni')
        res_partner = RP.create({'name': 'rp1'})
        res_partner.document_type_id = document_type_cuit.id
        res = res_partner.check_vat_ar('123456789')
        assert not res
        res_partner.document_type_id = document_type_cuil.id
        res = res_partner.check_vat_ar('123456789112')
        assert not res
        res_partner.document_type_id = document_type_dni.id
        res = res_partner.check_vat_ar('123456789')
        assert not res
        res = res_partner.check_vat_ar('123456789')
        assert not res
        res = RP.check_vat_ar('45326840803')
        assert not res
        res = RP.check_vat_ar('10970475183')
        assert not res
        res = RP.check_vat_ar('24880548227')
        assert res

    def test_onchange_document_type(self, RP, RDT):
        document_type = RDT.env.ref('base_vat_ar.document_cuit')
        res_partner = self.create_res_partner(
            RP, 'rp1', '12345678911', document_type.id
        )
        res_partner.onchange_document_type()
        assert not res_partner.dst_cuit_id
