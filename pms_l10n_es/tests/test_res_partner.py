from .common import TestPms


class TestResPartner(TestPms):
    def setUp(self):
        super().setUp()

    def test_get_vat_falls_back_to_vat(self):
        """Without aeat_identification_type, get_vat() returns the VAT field."""
        partner = self.env["res.partner"].create(
            {"name": "VAT only", "vat": "ESA12345674"}
        )
        self.assertEqual(partner.get_vat(), "ESA12345674")

    def test_get_vat_returns_aeat_identification(self):
        """When aeat_identification_type is set, get_vat() returns
        aeat_identification regardless of vat (consistent with
        l10n_es_aeat _parse_aeat_vat_info priority)."""
        partner = self.env["res.partner"].create(
            {
                "name": "Passport guest",
                "vat": False,
                "aeat_identification_type": "03",
                "aeat_identification": "X1234567",
            }
        )
        self.assertEqual(partner.get_vat(), "X1234567")

    def test_get_vat_aeat_wins_over_vat(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Both filled",
                "vat": "ESA12345674",
                "aeat_identification_type": "06",
                "aeat_identification": "OTHER-ID-1",
            }
        )
        self.assertEqual(partner.get_vat(), "OTHER-ID-1")

    def test_get_vat_empty_when_aeat_type_without_value(self):
        """If aeat_identification_type is set but aeat_identification is empty,
        get_vat() returns "" (does not fall back to vat)."""
        partner = self.env["res.partner"].create(
            {
                "name": "Type without value",
                "vat": "ESA12345674",
                "aeat_identification_type": "05",
                "aeat_identification": False,
            }
        )
        self.assertEqual(partner.get_vat(), "")

    def test_ine_code_foreign_partner(self):
        """
        The ine code for foreigners partners should match the alpha code 3
        """

        # ARRANGE & ACT
        # get record of russia
        self.country_russia = self.env["res.country"].search([("code", "=", "RU")])

        # Create partner 1 (russia)
        self.partner_1 = self.env["res.partner"].create(
            {
                "name": "partner1",
                "country_id": self.country_russia.id,
                "nationality_id": self.country_russia.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        # ASSERT
        self.assertEqual(
            self.partner_1.ine_code,
            self.partner_1.country_id.code_alpha3,
            "The ine code for foreigners should match code_alpha3",
        )

    def test_ine_code_spanish_partner(self):
        """
        The ine code for Spanish partners must match the ine code
        of the state to which they belong
        """

        # ARRANGE & ACT
        # get record of russia
        country_spain = self.env["res.country"].search([("code", "=", "ES")])
        state_madrid = self.env["res.country.state"].search([("name", "=", "Madrid")])

        # Create partner 1 (russia)
        self.partner_1 = self.env["res.partner"].create(
            {
                "name": "partner1",
                "country_id": country_spain.id,
                "nationality_id": country_spain.id,
                "state_id": state_madrid.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        # ASSERT
        self.assertEqual(
            self.partner_1.ine_code,
            self.partner_1.state_id.ine_code,
            "The ine code for Spanish partners must match the ine"
            " code of the state to which they belong",
        )
