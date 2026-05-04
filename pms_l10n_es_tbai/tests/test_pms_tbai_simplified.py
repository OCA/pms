from datetime import datetime

from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.l10n_es_edi_tbai.models.xml_utils import NS_MAP
from odoo.addons.l10n_es_edi_tbai.tests.common import TestEsEdiTbaiCommon


@tagged("post_install", "-at_install", "post_install_l10n")
class TestPmsTbaiSimplified(TestEsEdiTbaiCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.various_partner = cls.env.ref("pms.various_pms_partner")
        cls.sii_simplified_partner = cls.env.ref("l10n_es_edi_sii.partner_simplified")
        cls.edi_format = cls.env.ref("l10n_es_edi_tbai.edi_es_tbai")

    def _create_invoice(self, partner):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "invoice_date": datetime.now(),
                "partner_id": partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "price_unit": 100.0,
                            "quantity": 1,
                            "tax_ids": [
                                (6, 0, self._get_tax_by_xml_id("s_iva21b").ids)
                            ],
                        },
                    )
                ],
            }
        )

    def test_pms_various_partner_is_simplified(self):
        """PMS various partner must be detected as simplified invoice."""
        invoice = self._create_invoice(self.various_partner)
        self.assertTrue(invoice._is_l10n_es_tbai_simplified())

    def test_sii_simplified_partner_still_works(self):
        """Original SII simplified partner must still be detected."""
        invoice = self._create_invoice(self.sii_simplified_partner)
        self.assertTrue(invoice._is_l10n_es_tbai_simplified())

    def test_regular_partner_not_simplified(self):
        """A regular partner must not be detected as simplified."""
        invoice = self._create_invoice(self.partner_b)
        self.assertFalse(invoice._is_l10n_es_tbai_simplified())

    def test_xml_no_destinatarios_for_pms_various_partner(self):
        """XML for PMS various partner must not contain Destinatarios
        and must have FacturaSimplificada=S."""
        invoice = self._create_invoice(self.various_partner)
        with freeze_time(self.frozen_today):
            result = self.edi_format._get_l10n_es_tbai_invoice_xml(
                invoice, cancel=False
            )
            xml_doc = result[invoice]["xml_file"]
            xml_doc.remove(xml_doc.find("Signature", namespaces=NS_MAP))
            sujetos = xml_doc.find("Sujetos", namespaces={"T": "urn:ticketbai:emision"})
            destinatarios = sujetos.find(
                "Destinatarios",
                namespaces={"T": "urn:ticketbai:emision"},
            )
            self.assertIsNone(
                destinatarios,
                "Simplified invoice XML must not contain Destinatarios",
            )
            factura_simplificada = xml_doc.find(
                ".//FacturaSimplificada",
            )
            self.assertIsNotNone(factura_simplificada)
            self.assertEqual(factura_simplificada.text, "S")
