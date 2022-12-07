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
    _check_pms_properties_auto = True

    pms_board_service_id = fields.Many2one(
        string="Board Service",
        help="Board Service corresponding to this Board Service Room Type",
        required=True,
        index=True,
        comodel_name="pms.board.service",
        ondelete="cascade",
        check_pms_properties=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element;"
        " if not set, all property can access",
        required=False,
        ondelete="restrict",
        comodel_name="pms.property",
        check_pms_properties=True,
        store=True,
    )
    pms_room_type_id = fields.Many2one(
        string="Room Type",
        help="Room Type for which this Board Service is available",
        required=True,
        index=True,
        comodel_name="pms.room.type",
        ondelete="cascade",
        check_pms_properties=True,
    )
    board_service_line_ids = fields.One2many(
        string="Board Service Lines",
        help="Services included in this Board Service",
        comodel_name="pms.board.service.room.type.line",
        inverse_name="pms_board_service_room_type_id",
        required=True,
    )
    amount = fields.Float(
        string="Amount",
        help="Price for this Board Service. "
        "It corresponds to the sum of his board service lines",
        store=True,
        digits=("Product Price"),
        compute="_compute_board_amount",
    )
    by_default = fields.Boolean(
        string="Apply by Default",
        help="Indicates if this board service is applied by default in the room type",
    )

    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({"amount": total})

    def name_get(self):
        res = []
        for record in self:
            name = "{} - {}".format(
                record.pms_board_service_id.name, record.pms_room_type_id.name
            )
            res.append((record.id, name))
        return res

    @api.constrains("by_default")
    def constrains_duplicated_board_default(self):
        for record in self:
            default_boards = (
                record.pms_room_type_id.board_service_room_type_ids.filtered(
                    "by_default"
                )
            )
            # TODO Check properties (with different propertys is allowed)
            if any(
                default_boards.filtered(
                    lambda l: l.id != record.id
                    and l.pms_property_id == record.pms_property_id
                )
            ):
                raise UserError(_("""Only can set one default board service"""))

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
        # properties = False
        if "pms_board_service_id" in vals and "board_service_line_ids" not in vals:
            vals.update(
                self.prepare_board_service_reservation_ids(vals["pms_board_service_id"])
            )
        return super(PmsBoardServiceRoomType, self).create(vals)

    def write(self, vals):
        if "pms_board_service_id" in vals and "board_service_line_ids" not in vals:
            vals.update(
                self.prepare_board_service_reservation_ids(vals["pms_board_service_id"])
            )
        return super(PmsBoardServiceRoomType, self).write(vals)

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
