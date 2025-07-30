# Copyright 2017  Dario
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsBoardServiceRoomType(models.Model):
    _name = "pms.board.service.room.type"
    _rec_name = "pms_board_service_id"
    _log_access = False
    _description = "Board Service included in Room"
    _check_pms_properties_auto = True

    pms_board_service_id = fields.Many2one(
        comodel_name="pms.board.service",
        string="Board Service",
        required=True,
        index=True,
        ondelete="cascade",
        help="Board Service corresponding to this Board Service Room Type",
        check_pms_properties=True,
    )
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        index=True,
        ondelete="restrict",
        help="Property with access to the element;"
        " if not set, all property can access",
        check_pms_properties=True,
    )
    pms_room_type_id = fields.Many2one(
        comodel_name="pms.room.type",
        string="Room Type",
        required=True,
        index=True,
        ondelete="cascade",
        help="Room Type for which this Board Service is available",
        check_pms_properties=True,
    )
    board_service_line_ids = fields.One2many(
        comodel_name="pms.board.service.room.type.line",
        inverse_name="pms_board_service_room_type_id",
        string="Board Service Lines",
        required=True,
        help="Services included in this Board Service",
    )
    amount = fields.Float(
        compute="_compute_board_amount",
        store=True,
        digits=("Product Price"),
        help="Price for this Board Service. "
        "It corresponds to the sum of his board service lines",
    )
    by_default = fields.Boolean(
        string="Default",
        help="Indicates if this board service is applied by default in the room type",
    )
    pricelist_ids = fields.Many2many(
        comodel_name="product.pricelist",
        string="Pricelists",
        help="Pricelists where this Board Service is available",
    )

    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            record.amount = sum(record.board_service_line_ids.mapped("amount"))

    # def name_get(self):
    #     res = []
    #     for record in self:
    #         name = (
    #             f"{record.pms_board_service_id.name} - {record.pms_room_type_id.name}"
    #         )
    #         res.append((record.id, name))
    #     return res

    @api.constrains("by_default")
    def constrains_duplicated_board_default(self):
        for record in self:
            default_boards = (
                record.pms_room_type_id.board_service_room_type_ids.filtered(
                    "by_default"
                )
            )
            if any(
                default_boards.filtered(
                    lambda board, record=record: board.id != record.id
                    and board.pms_property_id == record.pms_property_id
                    and board.pricelist_ids == record.pricelist_ids
                )
            ):
                raise UserError(_("""Only can set one default board service"""))

    def open_board_lines_form(self):
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "pms.action_pms_board_service_room_type_view"
        )
        result.update(
            {
                "res_id": self.id,
                "target": "new",
            }
        )
        return result

    # def init(self):
    #     self._cr.execute(
    #         "SELECT indexname FROM pg_indexes WHERE indexname = %s",
    #         ("pms_board_service_id_pms_room_type_id",),
    #     )
    #     if not self._cr.fetchone():
    #         self._cr.execute(
    #             "CREATE INDEX pms_board_service_id_pms_room_type_id \
    #             ON pms_board_service_room_type_rel \
    #             (pms_board_service_id, pms_room_type_id)"
    #         )

    @api.model_create_multi
    def create(self, vals_list):
        # properties = False
        for vals in vals_list:
            if "pms_board_service_id" in vals and "board_service_line_ids" not in vals:
                vals.update(
                    self.prepare_board_service_reservation_ids(
                        vals["pms_board_service_id"]
                    )
                )
        return super().create(vals_list)

    def write(self, vals):
        if "pms_board_service_id" in vals and "board_service_line_ids" not in vals:
            vals.update(
                self.prepare_board_service_reservation_ids(vals["pms_board_service_id"])
            )
        return super().write(vals)

    @api.model
    def prepare_board_service_reservation_ids(self, board_service_id):
        """
        Prepare line to price products config
        """
        cmds = [(5, 0, 0)]
        board_service = self.env["pms.board.service"].browse(board_service_id)
        for line in board_service.board_service_line_ids:
            cmds.append(
                (
                    0,
                    False,
                    {
                        "product_id": line.product_id.id,
                        "amount": line.amount,
                        "adults": line.adults,
                        "children": line.children,
                    },
                )
            )
        return {"board_service_line_ids": cmds}
