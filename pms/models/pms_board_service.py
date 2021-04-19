# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsBoardService(models.Model):
    _name = "pms.board.service"
    _description = "Board Services"

    name = fields.Char(
        string="Board Service Name",
        help="Board Service Name",
        required=True,
        index=True,
        size=64,
        translate=True,
    )
    code_board = fields.Char(
        string="Board Service Code",
        help="Unique Board Service identification code per property",
        required=True,
    )
    board_service_line_ids = fields.One2many(
        string="Board Service Lines",
        help="Services included in this Board Service",
        comodel_name="pms.board.service.line",
        inverse_name="pms_board_service_id",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="pms_board_service_pms_property_rel",
        column1="board_service_id",
        column2="pms_property_id",
    )
    pms_board_service_room_type_ids = fields.One2many(
        string="Board Services Room Type",
        help="Board Services Room Type corresponding to this Board Service,"
        "One board service for several room types",
        comodel_name="pms.board.service.room.type",
        inverse_name="pms_board_service_id",
    )
    amount = fields.Float(
        string="Amount",
        help="Price for this Board Service. "
        "It corresponds to the sum of his board service lines",
        store=True,
        digits=("Product Price"),
        compute="_compute_board_amount",
    )

    show_detail_report = fields.Boolean(
        string="Show Detail Report",
        help="True if you want that board service detail to be shown on the report",
    )

    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({"amount": total})

    @api.model
    def get_unique_by_property_code(self, pms_property_id, code_board=None):
        """
        :param pms_property_id: property ID
        :param code_board: board service code (optional)
        :return: - recordset of
                    - all the pms.board.service of the pms_property_id
                      if code_board not defined
                    - one or 0 pms.board.service if code_board defined
                 - ValidationError if more than one code_board found by
                   the same pms_property_id
        """
        # TODO: similiar code as room.type -> unify
        domain = []
        if code_board:
            domain += ["&", ("code_board", "=", code_board)]
        domain += [
            "|",
            ("pms_property_ids", "in", pms_property_id),
            ("pms_property_ids", "=", False),
        ]
        records = self.search(domain)
        res, res_priority = {}, {}
        for rec in records:
            res_priority.setdefault(rec.code_board, -1)
            priority = rec.pms_property_ids and 1 or 0
            if priority > res_priority[rec.code_board]:
                res.setdefault(rec.code_board, rec.id)
                res[rec.code_board], res_priority[rec.code_board] = rec.id, priority
            elif priority == res_priority[rec.code_board]:
                raise ValidationError(
                    _(
                        "Integrity error: There's multiple board services "
                        "with the same code %s and properties"
                    )
                    % rec.code_board
                )
        return self.browse(list(res.values()))

    @api.constrains("code_board", "pms_property_ids")
    def _check_code_property_uniqueness(self):
        # TODO: similiar code as room.type -> unify
        msg = _(
            "Already exists another Board Service with the same code and properties"
        )
        for rec in self:
            if not rec.pms_property_ids:
                if self.search(
                    [
                        ("id", "!=", rec.id),
                        ("code_board", "=", rec.code_board),
                        ("pms_property_ids", "=", False),
                    ]
                ):
                    raise ValidationError(msg)
            else:
                for pms_property in rec.pms_property_ids:
                    other = rec.get_unique_by_property_code(
                        pms_property.id, rec.code_board
                    )
                    if other and other != rec:
                        raise ValidationError(msg)
