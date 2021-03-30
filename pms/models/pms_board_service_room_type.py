# Copyright 2017  Dario
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsBoardServiceRoomType(models.Model):
    _name = "pms.board.service.room.type"
    _table = "pms_board_service_room_type_rel"
    _rec_name = "pms_board_service_id"
    _log_access = False
    _description = "Board Service included in Room"

    # Fields declaration
    pms_board_service_id = fields.Many2one(
        "pms.board.service",
        string="Board Service",
        index=True,
        ondelete="cascade",
        required=True,
    )
    pms_property_ids = fields.Many2many(
        "pms.property",
        string="Properties",
        required=False,
        ondelete="restrict",
    )
    pms_room_type_id = fields.Many2one(
        "pms.room.type",
        string="Room Type",
        index=True,
        ondelete="cascade",
        required=True,
        domain=[
            "|",
            ("pms_property_ids", "=", False),
            ("pms_property_ids", "in", pms_property_ids),
        ],
    )
    board_service_line_ids = fields.One2many(
        "pms.board.service.room.type.line", "pms_board_service_room_type_id"
    )
    amount = fields.Float(
        "Amount", digits=("Product Price"), compute="_compute_board_amount", store=True
    )
    by_default = fields.Boolean("Apply by Default")

    # Compute and Search methods
    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({"amount": total})

    @api.constrains("by_default")
    def constrains_duplicated_board_defaul(self):
        for record in self:
            default_boards = (
                record.pms_room_type_id.board_service_room_type_ids.filtered(
                    "by_default"
                )
            )
            # TODO Check properties (with different propertys is allowed)
            if any(default_boards.filtered(lambda l: l.id != record.id)):
                raise UserError(_("""Only can set one default board service"""))

    # Action methods

    def open_board_lines_form(self):
        action = (
            self.env.ref("pms.action_pms_board_service_room_type_view").sudo().read()[0]
        )
        action["views"] = [
            (self.env.ref("pms.pms_board_service_room_type_form").id, "form")
        ]
        action["res_id"] = self.id
        action["target"] = "new"
        return action

    # ORM Overrides
    def init(self):
        self._cr.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname = %s",
            ("pms_board_service_id_pms_room_type_id",),
        )
        if not self._cr.fetchone():
            self._cr.execute(
                "CREATE INDEX pms_board_service_id_pms_room_type_id \
                ON pms_board_service_room_type_rel \
                (pms_board_service_id, pms_room_type_id)"
            )

    @api.model
    def create(self, vals):
        if "pms_board_service_id" in vals:
            vals.update(
                self.prepare_board_service_reservation_ids(vals["pms_board_service_id"])
            )
        return super(PmsBoardServiceRoomType, self).create(vals)

    def write(self, vals):
        if "pms_board_service_id" in vals:
            vals.update(
                self.prepare_board_service_reservation_ids(vals["pms_board_service_id"])
            )
        return super(PmsBoardServiceRoomType, self).write(vals)

    # Business methods
    @api.model
    def prepare_board_service_reservation_ids(self, board_service_id):
        """
        Prepare line to price products config
        """
        cmds = [(5, 0, 0)]
        board_service = self.env["pms.board.service"].browse(board_service_id)
        for line in board_service.board_service_line_ids:
            cmds.append(
                (0, False, {"product_id": line.product_id.id, "amount": line.amount})
            )
        return {"board_service_line_ids": cmds}
