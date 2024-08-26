# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError


class ChannelWubookPmsBoardServiceAdapter(Component):
    _name = "channel.wubook.pms.board.service.adapter"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.pms.board.service"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        raise ChannelAdapterError(
            _(
                "Create operation is not supported on Board Service by Wubook. Values: %s. "
                "Probably the cause is a wrong mapping of Board Services on Wubook backend type"
                % (values,)
            )
        )

    def read(self, _id):
        values = self.search_read([("id", "=", _id)])
        if not values:
            raise ChannelAdapterError(_("No Board Service found with id '%s'") % _id)
        if len(values) != 1:
            raise ChannelAdapterError(
                _("Received more than one board service %s") % (values,)
            )
        return values[0]

    def search_read(self, domain):
        values = self._gen_values()
        return self._filter(values, domain)

    def search(self, domain):
        values = self.search_read(domain)
        ids = [x[self._id] for x in values]
        return ids

    # pylint: disable=W8106
    def write(self, _id, values):
        raise ChannelAdapterError(
            _(
                "Write operation is not supported on Board Service by Wubook. Id: %i, Values: %s. "
                "Probably the cause is a wrong mapping of Board Services on Wubook backend type"
                % (_id, values)
            )
        )

    def delete(self, _id):
        raise ChannelAdapterError(
            _(
                "Delete operation is not supported on Board Service by Wubook. Id: %i"
                % (_id,)
            )
        )

    def _gen_values(self):
        backend_type = self.backend_record.backend_type_id.child_id
        names = dict(
            backend_type.board_service_ids.fields_get(
                ["wubook_board_service"], ["selection"]
            )["wubook_board_service"]["selection"]
        )
        return [
            {
                "id": x.wubook_board_service,
                "name": names[x.wubook_board_service],
                "shortname": x.board_service_shortname,
            }
            for x in backend_type.board_service_ids
        ]
