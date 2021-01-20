import datetime

from odoo import api, fields, models


class NumRoomsSelectionModel(models.TransientModel):
    _name = "pms.num.rooms.selection"
    _rec_name = "value"
    value = fields.Integer()
    room_type_id = fields.Char()
    folio_wizard_id = fields.One2many(
        comodel_name="pms.folio.availability.wizard",
        inverse_name="id",
    )


class AvailabilityWizard(models.TransientModel):
    _name = "pms.folio.availability.wizard"

    # Fields declarations
    folio_wizard_id = fields.Many2one(
        comodel_name="pms.folio.wizard",
    )
    checkin = fields.Date(
        string="From:",
        required=True,
    )
    checkout = fields.Date(
        string="To:",
        required=True,
    )
    room_type_id = fields.Many2one(comodel_name="pms.room.type")

    num_rooms_available = fields.Integer(
        string="Available rooms",
        default=0,
    )
    price_per_room = fields.Float(
        string="Price per room",
        default=0,
    )
    num_rooms_selected = fields.Many2one(
        comodel_name="pms.num.rooms.selection",
        inverse_name="folio_wizard_id",
        string="Selected rooms",
        compute="_compute_dynamic_selection",
        store=True,
        readonly=False,
        domain="[('value', '<=', num_rooms_available), "
        "('room_type_id', '=', room_type_id)]",
    )
    value_num_rooms_selected = fields.Integer(default=0)
    price_total = fields.Float(
        string="Total price", default=0, compute="_compute_price_total"
    )

    @api.depends("num_rooms_selected", "checkin", "checkout")
    def _compute_price_total(self):
        for record in self:
            record.price_total = 0

            # this field refresh is just to update it and take into account @ xml
            record.value_num_rooms_selected = record.num_rooms_selected.value

            num_rooms_available_by_date = []
            room_type_total_price_per_room = 0

            for date_iterator in [
                record.checkin + datetime.timedelta(days=x)
                for x in range(0, (record.checkout - record.checkin).days)
            ]:
                rooms_available = self.env[
                    "pms.room.type.availability.plan"
                ].rooms_available(
                    date_iterator,
                    date_iterator + datetime.timedelta(days=1),
                    room_type_id=record.room_type_id.id,
                    pricelist=record.folio_wizard_id.pricelist_id.id,
                )
                num_rooms_available_by_date.append(len(rooms_available))

                # get pricelist item
                pricelist_item = self.env["product.pricelist.item"].search(
                    [
                        ("pricelist_id", "=", record.folio_wizard_id.pricelist_id.id),
                        ("date_start_overnight", ">=", date_iterator),
                        ("date_end_overnight", "<=", date_iterator),
                        ("applied_on", "=", "1_product"),
                        (
                            "product_tmpl_id",
                            "=",
                            record.room_type_id.product_id.product_tmpl_id.id,
                        ),
                    ]
                )

                # check if applies pricelist item
                if (
                    pricelist_item
                    and record.num_rooms_selected.value >= pricelist_item.min_quantity
                ):
                    pricelist_item.ensure_one()
                    room_type_total_price_per_room += float(pricelist_item.price[2:])
                else:
                    room_type_total_price_per_room += (
                        record.room_type_id.product_id.list_price
                    )

            # get the availability for the entire stay (min of all dates)
            if num_rooms_available_by_date:
                record.num_rooms_available = min(num_rooms_available_by_date)

            # udpate the price per room
            record.price_per_room = room_type_total_price_per_room

            # if there's no rooms available
            if record.num_rooms_available == 0:
                # change the selector num_rooms_availabe to 0
                value_selected = self.env["pms.num.rooms.selection"].search(
                    [
                        ("room_type_id", "=", record.room_type_id.id),
                        ("value", "=", 0),
                    ]
                )
                if value_selected:
                    record.num_rooms_selected = value_selected
                record.value_num_rooms_selected = 0

                # change the price per room to 0
                record.price_per_room = 0

            record.price_total = record.price_per_room * record.num_rooms_selected.value

    def _compute_dynamic_selection(self):
        for record in self:
            for elem_to_insert in range(0, record.num_rooms_available + 1):
                if (
                    self.env["pms.num.rooms.selection"].search_count(
                        [
                            ("value", "=", elem_to_insert),
                            ("room_type_id", "=", record.room_type_id.id),
                        ]
                    )
                    == 0
                ):
                    self.env["pms.num.rooms.selection"].create(
                        {
                            "value": elem_to_insert,
                            "room_type_id": record.room_type_id.id,
                        }
                    )
            default = self.env["pms.num.rooms.selection"].search(
                [("value", "=", 0), ("room_type_id", "=", record.room_type_id.id)]
            )
            record.num_rooms_selected = default
