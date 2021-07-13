# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


# from odoo.addons.component.core import Component
#
#
# class ChannelWubookPmsPropertyAvailabilityDelayedBatchImporter(Component):
#     _name = "channel.wubook.pms.property.availability.delayed.batch.importer"
#     _inherit = "channel.wubook.delayed.batch.importer"
#
#     _apply_on = "channel.wubook.pms.property.availability"
#
#
# class ChannelWubookPmsPropertyAvailabilityDirectBatchImporter(Component):
#     _name = "channel.wubook.pms.property.availability.direct.batch.importer"
#     _inherit = "channel.wubook.direct.batch.importer"
#
#     _apply_on = "channel.wubook.pms.property.availability"
#
#
# class ChannelWubookPmsPropertyAvailabilityImporter(Component):
#     _name = "channel.wubook.pms.property.availability.importer"
#     _inherit = "channel.wubook.importer"
#
#     _apply_on = "channel.wubook.pms.property.availability"
#
#     def _import_dependencies(self, external_data, external_fields):
#         self._import_dependency(
#             {x["id_room"] for x in external_data.get("items", [])},
#             "channel.wubook.pms.room.type",
#         )
