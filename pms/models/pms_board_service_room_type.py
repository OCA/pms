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

    # Default Methods ang Gets

    def name_get(self):
        result = []
        for res in self:
            if res.pricelist_id:
                name = u"{} ({})".format(
                    res.pms_board_service_id.name,
                    res.pricelist_id.name,
                )
            else:
                name = u"{} ({})".format(res.pms_board_service_id.name, _("Generic"))
            result.append((res.id, name))
        return result

    # Fields declaration
    pms_board_service_id = fields.Many2one(
        "pms.board.service",
        string="Board Service",
        index=True,
        ondelete="cascade",
        required=True,
    )
    pms_room_type_id = fields.Many2one(
        "pms.room.type",
        string="Room Type",
        index=True,
        ondelete="cascade",
        required=True,
    )
    pricelist_id = fields.Many2one(
        "product.pricelist", string="Pricelist", required=False
    )
    board_service_line_ids = fields.One2many(
        "pms.board.service.room.type.line", "pms_board_service_room_type_id"
    )
    pms_property_id = fields.Many2one(
        "pms.property", related="pms_room_type_id.pms_property_id"
    )
    price_type = fields.Selection(
        [("fixed", "Fixed"), ("percent", "Percent")],
        string="Type",
        default="fixed",
        required=True,
    )
    amount = fields.Float(
        "Amount", digits=("Product Price"), compute="_compute_board_amount", store=True
    )

    # Compute and Search methods
    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({"amount": total})

    # Constraints and onchanges
    @api.constrains("pricelist_id")
    def constrains_pricelist_id(self):
        for record in self:
            if self.pricelist_id:
                board_pricelist = self.env["pms.board.service.room.type"].search(
                    [
                        ("pricelist_id", "=", record.pricelist_id.id),
                        ("pms_room_type_id", "=", record.pms_room_type_id.id),
                        ("pms_board_service_id", "=", record.pms_board_service_id.id),
                        ("id", "!=", record.id),
                    ]
                )
                if board_pricelist:
                    raise UserError(
                        _("This Board Service in this Room can't repeat pricelist")
                    )
            else:
                board_pricelist = self.env["pms.board.service.room.type"].search(
                    [
                        ("pricelist_id", "=", False),
                        ("pms_room_type_id", "=", record.pms_room_type_id.id),
                        ("pms_board_service_id", "=", record.pms_board_service_id.id),
                        ("id", "!=", record.id),
                    ]
                )
                if board_pricelist:
                    raise UserError(
                        _(
                            "This Board Service in this Room \
                         can't repeat without pricelist"
                        )
                    )

    # Action methods

    def open_board_lines_form(self):
        action = self.env.ref("pms.action_pms_board_service_room_type_view").read()[0]
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
            ("pms_board_service_id_pms_room_type_id_pricelist_id",),
        )
        if not self._cr.fetchone():
            self._cr.execute(
                "CREATE INDEX pms_board_service_id_pms_room_type_id_pricelist_id \
                ON pms_board_service_room_type_rel \
                (pms_board_service_id, pms_room_type_id, pricelist_id)"
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
