# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ChannelWubookProductPriceBinding(models.Model):
    _name = "channel.wubook.product.pricelist"
    _inherit = "channel.wubook.binding"
    _inherits = {"product.pricelist": "odoo_id"}

    # binding fields
    odoo_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    @api.model
    def import_data(
        self,
        backend_id,
        date_from,
        date_to,
        pricelist_ids,
        room_type_ids,
        delayed=True,
    ):
        """ Prepare the batch import of Pricelists from Channel """
        domain = []
        if date_from and date_to:
            domain += [
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
        # TODO: duplicated code, unify
        if pricelist_ids:
            with backend_id.work_on(self._name) as work:
                binder = work.component(usage="binder")
            external_ids = []
            for pl in pricelist_ids:
                binding = binder.wrap_record(pl)
                if not binding or not binding.external_id:
                    raise NotImplementedError(
                        _(
                            "The pricelist %s has no binding. Import of Odoo records "
                            "without binding is not supported yet"
                        )
                        % pl.name
                    )
                external_ids.append(binding.external_id)
            domain.append(("id", "in", external_ids))
        if room_type_ids:
            with backend_id.work_on("channel.wubook.pms.room.type") as work:
                binder = work.component(usage="binder")
            external_ids = []
            for rt in room_type_ids:
                binding = binder.wrap_record(rt)
                if not binding or not binding.external_id:
                    raise NotImplementedError(
                        _(
                            "The Room type %s has no binding. Import of Odoo records "
                            "without binding is not supported yet"
                        )
                        % rt.name
                    )
                external_ids.append(binding.external_id)
            domain.append(("rooms", "in", external_ids))
        return self.import_batch(
            backend_record=backend_id, domain=domain, delayed=delayed
        )

    @api.model
    def export_data(self, backend_record=None):
        """ Prepare the batch export of Pricelist to Channel """
        return self.export_batch(
            backend_record=backend_record,
            domain=[
                # ("name", "=", "virt1"),
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", backend_record.pms_property_id.ids),
            ],
        )

    def resync_import(self):
        for record in self:
            room_type_items = record.item_ids.filtered(
                lambda x: not x.pms_property_ids
                or self.backend_id.pms_property_id in x.pms_property_ids
            )
            if room_type_items:
                date_from = min(room_type_items.mapped("date_start_consumption"))
                date_to = max(room_type_items.mapped("date_end_consumption"))
                products = room_type_items.mapped("product_id")
                room_types = self.env["pms.room.type"].search(
                    [
                        ("product_id", "in", products.ids),
                    ]
                )
                record.import_data(
                    self.backend_id,
                    date_from,
                    date_to,
                    self.odoo_id,
                    room_types,
                    delayed=False,
                )

    def write(self, values):
        # workaround to surpass an Odoo bug in a delegation inheritance
        # of product.pricelist that does not let to write 'name' field
        # if 'items_ids' is written as well on the same write call.
        # With other fields like 'sequence' it does not crash but it does not
        # save the value entered. For other fields it works but it's unstable.
        item_ids = values.pop("item_ids", None)
        if item_ids:
            super(ChannelWubookProductPriceBinding, self).write({"item_ids": item_ids})
        if values:
            return super(ChannelWubookProductPriceBinding, self).write(values)
