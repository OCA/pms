# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsBoardService(models.Model):
    _name = "pms.board.service"
    _description = "Board Services"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Board Service Name",
        help="Board Service Name",
        required=True,
        index=True,
        size=64,
        translate=True,
    )
    default_code = fields.Char(
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
        ondelete="restrict",
        comodel_name="pms.property",
        relation="pms_board_service_pms_property_rel",
        column1="board_service_id",
        column2="pms_property_id",
        check_pms_properties=True,
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
    def get_unique_by_property_code(self, pms_property_id, default_code=None):
        """
        :param pms_property_id: property ID
        :param default_code: board service code (optional)
        :return: - recordset of
                    - all the pms.board.service of the pms_property_id
                      if default_code not defined
                    - one or 0 pms.board.service if default_code defined
                 - ValidationError if more than one default_code found by
                   the same pms_property_id
        """
        # TODO: similiar code as room.type -> unify
        domain = []
        if default_code:
            domain += ["&", ("default_code", "=", default_code)]
        domain += [
            "|",
            ("pms_property_ids", "in", pms_property_id),
            ("pms_property_ids", "=", False),
        ]
        records = self.search(domain)
        res, res_priority = {}, {}
        for rec in records:
            res_priority.setdefault(rec.default_code, -1)
            priority = rec.pms_property_ids and 1 or 0
            if priority > res_priority[rec.default_code]:
                res.setdefault(rec.default_code, rec.id)
                res[rec.default_code], res_priority[rec.default_code] = rec.id, priority
            elif priority == res_priority[rec.default_code]:
                raise ValidationError(
                    _(
                        "Integrity error: There's multiple board services "
                        "with the same code %s and properties"
                    )
                    % rec.default_code
                )
        return self.browse(list(res.values()))

    @api.constrains("default_code", "pms_property_ids")
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
                        ("default_code", "=", rec.default_code),
                        ("pms_property_ids", "=", False),
                    ]
                ):
                    raise ValidationError(msg)
            else:
                for pms_property in rec.pms_property_ids:
                    other = rec.get_unique_by_property_code(
                        pms_property.id, rec.default_code
                    )
                    if other and other != rec:
                        raise ValidationError(msg)
