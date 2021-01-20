import datetime

from odoo import api, fields, models


class FolioWizard(models.TransientModel):
    _name = "pms.folio.wizard"
    _description = (
        "Wizard to check availability by room type and pricelist &"
        " creation of folios with its reservations"
    )
    # Fields declaration
    start_date = fields.Date(
        string="From:",
        required=True,
    )
    end_date = fields.Date(
        string="To:",
        required=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Pricelist",
        compute="_compute_pricelist_id",
        store=True,
        readonly=False,
    )
    partner_id = fields.Many2one(
        "res.partner",
    )
    availability_results = fields.One2many(
        comodel_name="pms.folio.availability.wizard",
        inverse_name="folio_wizard_id",
        compute="_compute_availability_results",
        store=True,
        readonly=False,
    )
    total_price_folio = fields.Float(
        string="Total Price", compute="_compute_total_price_folio"
    )
    discount = fields.Float(
        string="Discount",
        default=0,
    )
    can_create_folio = fields.Boolean(compute="_compute_can_create_folio")

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

                for room_type_iterator in self.env["pms.room.type"].search([]):

                    num_rooms_available_by_date = []
                    room_type_total_price_per_room = 0

                    for date_iterator in [
                        record.start_date + datetime.timedelta(days=x)
                        for x in range(0, (record.end_date - record.start_date).days)
                    ]:
                        rooms_available = self.env[
                            "pms.room.type.availability.plan"
                        ].rooms_available(
                            date_iterator,
                            date_iterator + datetime.timedelta(days=1),
                            room_type_id=room_type_iterator.id,
                            pricelist=record.pricelist_id.id,
                        )

                        num_rooms_available_by_date.append(len(rooms_available))

                        pricelist_item = self.env["product.pricelist.item"].search(
                            [
                                ("pricelist_id", "=", record.pricelist_id.id),
                                ("date_start_overnight", ">=", date_iterator),
                                ("date_end_overnight", "<=", date_iterator),
                                ("applied_on", "=", "1_product"),
                                (
                                    "product_tmpl_id",
                                    "=",
                                    room_type_iterator.product_id.product_tmpl_id.id,
                                ),
                            ]
                        )

                        # if pricelist_item exists for the date and without
                        # min_quantity (min_quantity = 0)
                        if pricelist_item and pricelist_item.min_quantity == 0:
                            pricelist_item.ensure_one()
                            room_type_total_price_per_room += float(
                                pricelist_item.price[2:]
                            )
                        else:
                            # default price from room_type
                            room_type_total_price_per_room += (
                                room_type_iterator.product_id.list_price
                            )

                    # check there are rooms of the type
                    if room_type_iterator.total_rooms_count > 0:

                        # get min availability between start date & end date
                        num_rooms_available = min(num_rooms_available_by_date)

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
                                    "price_per_room": room_type_total_price_per_room
                                    if num_rooms_available
                                    > 0  # not showing price if there's no availability
                                    else 0,
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

    # actions
    def create_folio(self):
        for record in self:
            folio = self.env["pms.folio"].create(
                {
                    "pricelist_id": record.pricelist_id.id,
                    "partner_id": record.partner_id.id,
                }
            )
            for line in record.availability_results:
                for _reservations_to_create in range(0, line.value_num_rooms_selected):
                    res = self.env["pms.reservation"].create(
                        {
                            "folio_id": folio.id,
                            "checkin": line.checkin,
                            "checkout": line.checkout,
                            "room_type_id": line.room_type_id.id,
                            "partner_id": folio.partner_id.id,
                            "pricelist_id": folio.pricelist_id.id,
                        }
                    )
                    res.reservation_line_ids.discount = record.discount * 100
            action = self.env.ref("pms.open_pms_folio1_form_tree_all").read()[0]
            action["views"] = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            action["res_id"] = folio.id
            return action
