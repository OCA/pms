from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class ResCountryService(Component):
    _inherit = "base.rest.service"
    _name = "res.country.service"
    _usage = "countries"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("res.country.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_countries(self):
        result_countries = []
        ResCountriesInfo = self.env.datamodels["res.country.info"]
        for country in self.env["res.country"].search([]):
            result_countries.append(
                ResCountriesInfo(
                    id=country.id,
                    name=country.name,
                    code=country.code if country.code else None,
                )
            )
        return result_countries

    @restapi.method(
        [
            (
                [
                    "/<int:country_id>/country-states",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("res.country_state.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_states(self, country_id):
        result_country_states = []
        ResCountryStatesInfo = self.env.datamodels["res.country_state.info"]
        for country_states in self.env["res.country.state"].search(
            [("country_id", "=", country_id)]
        ):
            result_country_states.append(
                ResCountryStatesInfo(
                    id=country_states.id,
                    name=country_states.name,
                )
            )
        return result_country_states
