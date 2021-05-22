import datetime

from odoo import api, fields, models


class FolioWizard(models.TransientModel):
    _name = "pms.folio.wizard"
    _description = "Booking engine"
    _check_pms_properties_auto = True

    start_date = fields.Date(
        string="From:",
        help="Start date for creation of reservations and folios",
        required=True,
    )
    end_date = fields.Date(
        string="To:",
        help="End date for creation of reservations and folios",
        required=True,
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist applied in folio",
        readonly=False,
        store=True,
        comodel_name="product.pricelist",
        compute="_compute_pricelist_id",
        check_pms_properties=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the folio belongs",
        default=lambda self: self._default_pms_property_id(),
        comodel_name="pms.property",
        check_pms_properties=True,
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Partner Tags",
        ondelete="restrict",
        comodel_name="res.partner.category",
    )
    partner_id = fields.Many2one(
        string="Partner",
        help="Partner who made the reservation",
        comodel_name="res.partner",
        check_pms_properties=True,
    )
    folio_id = fields.Many2one(
        string="Folio",
        help="Folio in which are included new reservations",
        comodel_name="pms.folio",
        check_pms_properties=True,
    )
    availability_results = fields.One2many(
        string="Availability Results",
        help="Availability Results",
        readonly=False,
        store=True,
        comodel_name="pms.folio.availability.wizard",
        inverse_name="folio_wizard_id",
        compute="_compute_availability_results",
        check_pms_properties=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        help="Agency that made the reservation",
        comodel_name="res.partner",
        domain=[("is_agency", "=", True)],
        ondelete="restrict",
    )
    channel_type_id = fields.Many2one(
        string="Direct Sale Channel",
        help="Sales Channel through which the reservation was managed",
        readonly=False,
        store=True,
        comodel_name="pms.sale.channel",
        domain=[("channel_type", "=", "direct")],
        ondelete="restrict",
        compute="_compute_channel_type_id",
    )
    total_price_folio = fields.Float(
        string="Total Price",
        help="Total price of folio with taxes",
        compute="_compute_total_price_folio",
    )
    discount = fields.Float(
        string="Discount",
        help="Discount that be applied in total price",
        default=0,
    )
    can_create_folio = fields.Boolean(
        string="Can create folio", compute="_compute_can_create_folio"
    )

    def _default_pms_property_id(self):
        if self._context.get("default_folio_id"):
            folio = self.env["pms.folio"].browse(self._context.get("default_folio_id"))
            return folio.pms_property_id.id
        else:
            return self.env.user.get_active_property_ids()[0]

    @api.depends("availability_results.value_num_rooms_selected")
    def _compute_can_create_folio(self):
        for record in self:
            record.can_create_folio = any(
                record.availability_results.mapped("value_num_rooms_selected")
            )

    @api.depends("partner_id")
    def _compute_pricelist_id(self):
        for record in self:
            record.pricelist_id = record.partner_id.property_product_pricelist.id

    @api.depends("agency_id")
    def _compute_channel_type_id(self):
        for record in self:
            if record.agency_id:
                record.channel_type_id = record.agency_id.sale_channel_id.id

    @api.depends("availability_results.price_total", "discount")
    def _compute_total_price_folio(self):
        for record in self:
            record.total_price_folio = 0
            for line in record.availability_results:
                record.total_price_folio += line.price_total
            record.total_price_folio = record.total_price_folio * (1 - record.discount)

    @api.depends(
        "start_date",
        "end_date",
        "pricelist_id",
    )
    def _compute_availability_results(self):
        for record in self:
            record.availability_results = False

            if record.start_date and record.end_date and record.pricelist_id:
                if record.end_date == record.start_date:
                    record.end_date = record.end_date + datetime.timedelta(days=1)

                cmds = [(5, 0, 0)]

                for room_type_iterator in self.env["pms.room.type"].search(
                    [
                        "|",
                        ("pms_property_ids", "=", False),
                        ("pms_property_ids", "in", record.pms_property_id.id),
                    ]
                ):
                    num_rooms_available = self.env[
                        "pms.availability.plan"
                    ].get_count_rooms_available(
                        checkin=record.start_date,
                        checkout=record.end_date,
                        room_type_id=room_type_iterator.id,
                        pricelist_id=record.pricelist_id.id,
                        pms_property_id=record.pms_property_id.id,
                    )
                    cmds.append(
                        (
                            0,
                            0,
                            {
                                "folio_wizard_id": record.id,
                                "checkin": record.start_date,
                                "checkout": record.end_date,
                                "room_type_id": room_type_iterator.id,
                                "num_rooms_available": num_rooms_available,
                            },
                        )
                    )
                    # remove old items
                    old_lines = record.availability_results.mapped("id")
                    for old_line in old_lines:
                        cmds.append((2, old_line))

                    record.availability_results = cmds

                    record.availability_results = record.availability_results.sorted(
                        key=lambda s: s.num_rooms_available, reverse=True
                    )

    def create_folio(self):
        for record in self:
            if not record.folio_id:
                folio = self.env["pms.folio"].create(
                    {
                        "pricelist_id": record.pricelist_id.id,
                        "partner_id": record.partner_id.id,
                        "pms_property_id": record.pms_property_id.id,
                        "agency_id": record.agency_id.id,
                        "channel_type_id": record.channel_type_id.id,
                        "segmentation_ids": [(6, 0, record.segmentation_ids.ids)],
                    }
                )
            else:
                folio = record.folio_id
            for line in record.availability_results:
                for _reservations_to_create in range(0, line.value_num_rooms_selected):
                    res = self.env["pms.reservation"].create(
                        {
                            "folio_id": folio.id,
                            "checkin": line.checkin,
                            "checkout": line.checkout,
                            "room_type_id": line.room_type_id.id,
                            "partner_id": record.partner_id.id,
                            "pricelist_id": record.pricelist_id.id,
                            "pms_property_id": folio.pms_property_id.id,
                            "board_service_room_id": line.board_service_room_id.id,
                        }
                    )
                    res.reservation_line_ids.discount = record.discount * 100
            action = self.env.ref("pms.open_pms_folio1_form_tree_all").read()[0]
            action["views"] = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            action["res_id"] = folio.id
            return action
