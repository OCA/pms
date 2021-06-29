# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError


class ChannelWubookPmsRoomTypeAdapter(Component):
    _name = "channel.wubook.pms.room.type.adapter"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.pms.room.type"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        # https://tdocs.wubook.net/wired/rooms.html#new_room
        params = self._prepare_parameters(
            values,
            [
                "woodoo",
                "name",
                "occupancy",
                "price",
                "availability",
                "shortname",
                "board",
            ],
            [
                "names",
                "descriptions",
                "boards",
                "rtype",
                ("min_price", 0),
                ("max_price", 0),
            ],
        )
        _id = self._exec("new_room", *params)
        return _id

    def read(self, _id, ancillary=None):
        # https://tdocs.wubook.net/wired/rooms.html#fetch_single_room
        values = {"id": _id}
        if ancillary is not None:
            values["ancillary"] = ancillary
        params = self._prepare_parameters(values, ["id"], ["ancillary"])
        values = self._exec("fetch_single_room", *params)
        if not values:
            raise ChannelAdapterError(_("No room type found with id '%s'") % _id)
        if len(values) != 1:
            raise ChannelAdapterError(_("Received more than one room %s") % (values,))
        self._format_values(values)
        return values[0]

    def search_read(self, domain, ancillary=None):
        # https://tdocs.wubook.net/wired/rooms.html#fetch_rooms
        values = {}
        if ancillary is not None:
            values["ancillary"] = ancillary
        params = self._prepare_parameters(values, [], ["ancillary"])
        values = self._exec("fetch_rooms", *params)
        values = self._filter(values, domain)
        self._format_values(values)
        return values

    def search(self, domain, ancillary=None):
        # https://tdocs.wubook.net/wired/rooms.html#fetch_rooms
        values = self.search_read(domain, ancillary=ancillary)
        ids = [x[self._id] for x in values]
        return ids

    # pylint: disable=W8106
    def write(self, _id, values):
        # https://tdocs.wubook.net/wired/rooms.html#mod_room
        params = self._prepare_parameters(
            values,
            ["name", "occupancy", "price", "availability", "shortname", "board"],
            [
                "names",
                "descriptions",
                "boards",
                ("min_price", 0),
                ("max_price", 0),
                "rtype",
                "woodoo",
            ],
        )
        _id = self._exec("mod_room", _id, *params)
        return _id

    def delete(self, _id):
        # https://tdocs.wubook.net/wired/rooms.html#del_room
        res = self._exec("del_room", _id)
        return res

    # MISC
    def images(self, _id):
        # https://tdocs.wubook.net/wired/rooms.html#room_images
        values = self._exec("room_images", _id)
        return values

    def push_update_activation(self, url):
        # https://tdocs.wubook.net/wired/rooms.html#push_update_activation
        self._exec("push_update_activation", url)

    def push_update_url(self):
        # https://tdocs.wubook.net/wired/rooms.html#push_update_url
        url = self._exec("push_update_url")
        return url

    def _format_values(self, values):
        for v in values:
            # boards
            default_board_id = v.pop("board")
            boards = v.pop("boards") or {}
            boards[default_board_id] = {}
            if "nb" in boards:
                boards.pop("nb")
            v["boards"] = []
            for board_id, params in boards.items():
                v["boards"].append(
                    {
                        "id": board_id,
                        "default": board_id == default_board_id and 1 or 0,
                        **params,
                    }
                )
