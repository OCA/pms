import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsNotificationService(Component):
    _inherit = "base.rest.service"
    _name = "pms.notification.service"
    _usage = "notifications"
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
        input_param=Datamodel("pms.notification.search", is_list=False),
        output_param=Datamodel("pms.notification.info", is_list=True),
        auth="jwt_api_pms",
        cors="*",
    )
    def get_notifications(self, pms_notification_search):
        from_date_time = datetime.datetime.fromtimestamp(
            int(pms_notification_search.fromTimestamp) / 1000
        )
        new_reservations = self.env["pms.reservation"].search(
            [
                ("create_date", ">=", from_date_time),
                ("to_assign", "=", True),
                (
                    "create_uid.id",
                    "!=",
                    self.env.user.id,
                ),
            ],
            limit=10,
            order="create_date desc",
        )
        notifications = []
        PmsNotificationInfo = self.env.datamodels["pms.notification.info"]
        for folio in new_reservations.mapped("folio_id"):
            notifications.append(
                PmsNotificationInfo(
                    pmsPropertyId=folio.pms_property_id.id,
                    folioId=folio.id,
                    timeStamp=int(folio.create_date.strftime("%s%f")) / 1000,
                    folioName=folio.name,
                    partnerName=folio.partner_name,
                    saleChannelName=folio.agency_id.name
                    if folio.agency_id
                    else folio.sale_channel_origin_id.name,
                )
            )
        return notifications
