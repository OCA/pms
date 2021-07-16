# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsAvailabilityMapperImport(Component):
    _name = "channel.wubook.pms.availability.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.availability"

    direct = [
        ("avail", "sale_avail"),
    ]
