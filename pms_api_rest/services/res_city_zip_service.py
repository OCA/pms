from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class ResCityZipService(Component):
    _inherit = "base.rest.service"
    _name = "res.city.zip.service"
    _usage = "zips"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<string:res_city_zip>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("res.city.zip.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_address_data_by_zip(self, res_city_zip):
        result_zip_data = []
        ResCityZipInfo = self.env.datamodels["res.city.zip.info"]
        for zip_code in self.env["res.city.zip"].search([("name", "=", res_city_zip)]):
            result_zip_data.append(
                ResCityZipInfo(
                    cityId=zip_code.city_id.name,
                    stateId=zip_code.state_id.name,
                    countryId=zip_code.country_id.name,
                )
            )
        return result_zip_data
