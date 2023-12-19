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
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("res.city.zip.search.param", is_list=False),
        output_param=Datamodel("res.city.zip.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_address_data(self, zip_search_param):
        result_res_zip = []
        if not zip_search_param.address:
            return result_res_zip
        ResCityZipInfo = self.env.datamodels["res.city.zip.info"]
        res_zip = self.env["res.city.zip"].search(
            [("display_name", "ilike", zip_search_param.address)], limit=10
        )

        if res_zip:
            for address in res_zip:
                result_res_zip.append(
                    ResCityZipInfo(
                        resZipId=address.id,
                        cityId=address.city_id.name if address.city_id else None,
                        stateId=address.state_id.id if address.state_id else None,
                        stateName=address.state_id.name if address.state_id else None,
                        countryId=address.country_id.id if address.country_id else None,
                        zipCode=address.name if address.name else None,
                    )
                )
        return result_res_zip

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
