from datetime import datetime

import pytz

from odoo import _

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
        from_datetime = datetime.strptime(
            pms_notification_search.fromDateTime, "%Y-%m-%d %H:%M:%S"
        )
        timezone = pytz.timezone(self.env.user.tz or "UTC")
        from_datetime = timezone.localize(from_datetime)
        from_datetime_utc = from_datetime.astimezone(pytz.utc)
        new_reservations = self.env["pms.reservation"].search(
            [
                ("create_date", ">=", from_datetime_utc),
                ("pms_property_id.id", "=", pms_notification_search.pmsPropertyId),
                ("to_assign", "=", True),
                ("create_uid.id", "!=", self.env.user.id),
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
                    dateTime=pytz.UTC.localize(folio.create_date)
                    .astimezone(timezone)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    userId=folio.create_uid.id,
                    mensaje=_("%s: Nueva reserva de %s por %s")
                    % (
                        folio.name,
                        folio.partner_name,
                        folio.agency_id.name
                        if folio.agency_id
                        else folio.sale_channel_origin_id.name,
                    ),
                )
            )
        return notifications
