from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

BOARD_GUEST_TYPES = [
    ("adults", "Adults"),
    ("children", "Children"),
    ("all", "Adults and children"),
]


class ProductProduct(models.Model):
    _inherit = "product.product"

    room_type_id = fields.Many2one(
        string="Room Type",
        comodel_name="pms.room.type",
        compute="_compute_room_type_id",
    )
    board_guest_type = fields.Selection(
        string="Board Service Guests",
        help="Guests that consume this variant of a board service, "
        "given by its value of the Guest attribute",
        selection=BOARD_GUEST_TYPES,
        compute="_compute_board_guest_type",
    )

    @api.depends("product_template_attribute_value_ids")
    def _compute_board_guest_type(self):
        guest_types = {
            self.env.ref("pms.product_attribute_value_board_guest_adult"): "adults",
            self.env.ref("pms.product_attribute_value_board_guest_child"): "children",
        }
        for record in self:
            values = (
                record.product_template_attribute_value_ids.product_attribute_value_id
            )
            guest_value = values.filtered(lambda v: v in guest_types)
            record.board_guest_type = guest_types.get(guest_value, "all")

    def _compute_room_type_id(self):
        for rec in self:
            room_type = self.env["pms.room.type"].search(
                [
                    ("product_id", "=", rec.id),
                ]
            )
            if room_type:
                if len(room_type) > 1:
                    raise ValidationError(
                        _("More than one room found for the same product")
                    )
                rec.room_type_id = room_type
            else:
                rec.room_type_id = False
