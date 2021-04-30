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
    _check_pms_properties_auto = True

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
    room_type_id = fields.Many2one(
        comodel_name="pms.room.type",
        check_pms_properties=True,
    )

    num_rooms_available = fields.Integer(
        string="Available rooms",
        compute="_compute_num_rooms_available",
        store="true",
    )
    num_rooms_selected = fields.Many2one(
        comodel_name="pms.num.rooms.selection",
        inverse_name="folio_wizard_id",
        string="Selected rooms",
        compute="_compute_num_rooms_selected",
        store=True,
        readonly=False,
        domain="[('value', '<=', num_rooms_available), "
        "('room_type_id', '=', room_type_id)]",
    )
    value_num_rooms_selected = fields.Integer(
        compute="_compute_value_num_rooms_selected",
        store=True,
        readonly=False,
    )
    price_per_room = fields.Float(
        string="Price per room",
        compute="_compute_price_per_room",
    )
    price_total = fields.Float(string="Total price", compute="_compute_price_total")
    pms_property_id = fields.Many2one(
        related="folio_wizard_id.pms_property_id",
        string="Property",
    )
    board_service_room_id = fields.Many2one(
        string="Board Service",
        help="Board Service included in the room",
        comodel_name="pms.board.service.room.type",
        domain="[('pms_room_type_id','=',room_type_id)]",
        tracking=True,
    )

    @api.depends("room_type_id", "checkin", "checkout")
    def _compute_num_rooms_available(self):
        for record in self:
            record.num_rooms_available = self.env[
                "pms.availability.plan"
            ].get_count_rooms_available(
                record.checkin,
                record.checkout,
                room_type_id=record.room_type_id.id,
                pricelist_id=record.folio_wizard_id.pricelist_id.id,
                pms_property_id=record.folio_wizard_id.pms_property_id.id,
            )

    @api.depends("num_rooms_available")
    def _compute_num_rooms_selected(self):
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
            record.num_rooms_selected = self.env["pms.num.rooms.selection"].search(
                [("value", "=", 0), ("room_type_id", "=", record.room_type_id.id)]
            )

    @api.depends("num_rooms_selected")
    def _compute_value_num_rooms_selected(self):
        for record in self:
            if record.num_rooms_selected and record.num_rooms_selected.value:
                record.value_num_rooms_selected = record.num_rooms_selected.value
            elif not record.value_num_rooms_selected:
                record.value_num_rooms_selected = 0

    @api.depends("room_type_id", "board_service_room_id", "checkin", "checkout")
    def _compute_price_per_room(self):
        for record in self:
            room_type_total_price_per_room = 0

            for date_iterator in [
                record.checkin + datetime.timedelta(days=x)
                for x in range(0, (record.checkout - record.checkin).days)
            ]:

                partner = record.folio_wizard_id.partner_id
                product = record.room_type_id.product_id
                product = product.with_context(
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=1,
                    date=fields.Date.today(),
                    consumption_date=date_iterator,
                    pricelist=record.folio_wizard_id.pricelist_id.id,
                    uom=product.uom_id.id,
                    property=record.folio_wizard_id.pms_property_id.id,
                )
                room_type_total_price_per_room += product.price

            if record.board_service_room_id:
                nights = (record.checkout - record.checkin).days
                room_type_total_price_per_room += (
                    record.board_service_room_id.amount * nights
                )

            record.price_per_room = room_type_total_price_per_room

    @api.depends("price_per_room", "value_num_rooms_selected")
    def _compute_price_total(self):
        for record in self:
            record.price_total = record.price_per_room * record.value_num_rooms_selected
