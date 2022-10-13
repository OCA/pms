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
        output_param=Datamodel("res.city.zip.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_address_data_by_zip(self, res_city_zip):
        ResCityZipInfo = self.env.datamodels["res.city.zip.info"]
        res_zip = self.env["res.city.zip"].search([("name", "=", res_city_zip)])
        if len(res_zip) > 1:
            res_zip = res_zip[0]
        if res_zip:
            return ResCityZipInfo(
                cityId=res_zip.city_id.name,
                stateId=res_zip.state_id.id,
                countryId=res_zip.country_id.id,
            )
        else:
            return ResCityZipInfo()
