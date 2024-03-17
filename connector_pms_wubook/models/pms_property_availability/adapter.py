# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import uuid

from odoo.addons.component.core import Component


class ChannelWubookPmsPropertyAvailabilityAdapter(Component):
    _name = "channel.wubook.pms.property.availability"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.pms.property.availability"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        items = values["availabilities"]
        if items:
            self._write_items(items)
        return uuid.uuid4().hex

    # pylint: disable=W8106
    def write(self, _id, values):
        items = values["availabilities"]
        if items:
            self._write_items(items)

    # aux
    def _write_items(self, items):
        # https://tdocs.wubook.net/wired/avail.html#update_avail
        dfrom, dto = None, None
        rooms = {}
        for avail in items:
            dfrom = dfrom and min(dfrom, avail["date"]) or avail["date"]
            dto = dto and max(dto, avail["date"]) or avail["date"]
            rooms.setdefault(avail["id_room"], {})[avail["date"]] = {
                "avail": avail["avail"]
            }

        days = {}
        for i in range((dto - dfrom).days + 1):
            date = dfrom + datetime.timedelta(days=i)
            for id_room, val in rooms.items():
                days.setdefault(id_room, []).append(val.get(date, {}))

        values = {
            "dfrom": dfrom.strftime(self._date_format),
            "rooms": [
                {"id": id_room, "days": avail} for id_room, avail in days.items()
            ],
        }
        params = self._prepare_parameters(
            values,
            [
                "dfrom",
                "rooms",
            ],
        )
        self._exec("update_avail", *params)
