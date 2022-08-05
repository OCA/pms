# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast
import logging

from odoo import api, fields, models

_log = logging.getLogger(__name__)


class PmsGuestyReservation(models.Model):
    _name = "pms.guesty.reservation"
    _description = "PMS Guesty reservation"
    _rec_name = "uuid"

    @api.depends("uuid", "state")
    def _compute_display_name(self):
        self.display_name = "{} - {}".format(self.state, self.uuid)

    uuid = fields.Char(copy=False, required=True)
    state = fields.Char(copy=False, default="inquiry")

    is_updated = fields.Boolean(default=False)
    json_meta = fields.Text()

    _sql_constraints = [
        (
            "unique_uuid",
            "unique(uuid)",
            "Reservation UUID cannot be duplicated",
        )
    ]

    def _get_json_meta(self):
        try:
            return ast.literal_eval(self.json_meta)
        except Exception as ex:
            _log.warning(ex)
            return {}

    def pull_reservation(self, reservation_info):
        uuid, state = reservation_info["_id"], reservation_info["status"]
        payload = {
            "uuid": uuid,
            "state": state,
            "is_updated": False,
            "json_meta": reservation_info,
        }
        reservation = self.search([("uuid", "=", uuid)], limit=1)
        if not reservation.exists():
            _log.info("reservation does not exists: {}".format(uuid))
            reservation = self.create(payload)
            reservation.save_pms_reservation()
        elif reservation.is_updated:
            _log.info("reservation already exists and were updated: {}".format(uuid))
            reservation.write(payload)
            reservation.save_pms_reservation()
        else:
            _log.info("Event skipped for: {}".format(uuid))
            meta = reservation._get_json_meta()
            last_updatde_at__meta = meta["lastUpdatedAt"]
            last_updated_at__info = reservation_info["lastUpdatedAt"]
            if last_updated_at__info > last_updatde_at__meta:
                self.with_delay(10).pull_reservation(reservation_info)

        return reservation

    def save_pms_reservation(self):
        pms_reservation_id = (
            self.env["pms.reservation"]
            .sudo()
            .guesty_pull_reservation(self._get_json_meta(), "reservation.update")
        )

        _log.info("Guesty Reservation Pulled: {}".format(pms_reservation_id))

        pms_reservation_id.write({"guesty_reservation_id": self.id})
        self.write({"is_updated": True})
        return pms_reservation_id
