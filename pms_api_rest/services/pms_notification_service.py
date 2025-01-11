from odoo import fields

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


class PmsNotificationService(Component):
    _inherit = "base.rest.service"
    _name = "pms.notification.service"
    _usage = "notifications"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/reservations-to-assign",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.notification.search", is_list=False),
        output_param=Datamodel("pms.notification.info", is_list=False),
        auth="jwt_api_pms",
        cors="*",
    )
    def get_reservations_to_assign_notifications(self, pms_notification_search):
        if not pms_notification_search.pmsPropertyId:
            return 0
        pms_api_check_access(
            user=self.env.user,
            records=self.env["pms.property"]
            .sudo()
            .browse(pms_notification_search.pmsPropertyId),
        )
        num_reservation_ids_to_assign = (
            self.env["pms.reservation"]
            .sudo()
            .search_count(
                [
                    # this domain should be the same as folio service
                    # for unassigned reservations
                    ("pms_property_id", "=", pms_notification_search.pmsPropertyId),
                    ("checkin", ">=", fields.Date.today()),
                    ("to_assign", "=", True),
                    ("state", "in", ("draft", "confirm", "arrival_delayed")),
                    ("reservation_type", "!=", "out"),
                ],
            )
        )
        PmsNotificationInfo = self.env.datamodels["pms.notification.info"]
        return PmsNotificationInfo(
            numReservationsToAssign=num_reservation_ids_to_assign
        )
