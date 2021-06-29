# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid

from odoo.addons.component.core import Component


class ChannelWubookPmsAvailabilityAdapter(Component):
    _name = "channel.wubook.pms.availability.adapter"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.pms.availability"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        self._update_avail(values)
        return uuid.uuid4().hex

    # pylint: disable=W8106
    def write(self, _id, values):
        self._update_avail(values)

    # aux
    def _update_avail(self, values):
        # https://tdocs.wubook.net/wired/avail.html#update_avail
        values = {
            "dfrom": values["date"].strftime(self._date_format),
            "rooms": [{"id": values["id_room"], "days": [{"avail": values["avail"]}]}],
        }
        params = self._prepare_parameters(
            values,
            [
                "dfrom",
                "rooms",
            ],
        )
        # DISABLEDONDEV
        # self._exec("update_avail", *params)
