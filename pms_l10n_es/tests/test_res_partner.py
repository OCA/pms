from .common import TestPms


class TestResPartner(TestPms):
    def setUp(self):
        super().setUp()

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
                "residence_country_id": country_spain.id,
                "nationality_id": country_spain.id,
                "residence_state_id": state_madrid.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        # ASSERT
        self.assertEqual(
            self.partner_1.ine_code,
            self.partner_1.residence_state_id.ine_code,
            "The ine code for Spanish partners must match the ine"
            " code of the state to which they belong",
        )
