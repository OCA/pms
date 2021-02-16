# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2021  Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomTypeClass(models.Model):
    """Before creating a 'room type_class', you need to consider the following:
    With the term 'room type class' is meant a physical class of
    residential accommodation: for example, a Room, a Bed, an Apartment,
    a Tent, a Caravan...
    """

    _name = "pms.room.type.class"
    _description = "Room Type Class"
    _order = "sequence, name, code_class"

    # Fields declaration
    name = fields.Char("Class Name", required=True, translate=True)
    # Relationship between models
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    room_type_ids = fields.One2many("pms.room.type", "class_id", "Types")
    code_class = fields.Char("Code", required=True)
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence", default=0)

    @api.model
    def get_unique_by_property_code(self, pms_property_id, code_class=None):
        """
        :param pms_property_id: property ID
        :param code_class: room type code (optional)
        :return: - recordset of
                    - all the pms.room.type.class of the pms_property_id
                      if code_class not defined
                    - one or 0 pms.room.type.class if code_class defined
                 - ValidationError if more than one code_class found by
                   the same pms_property_id
        """
        # TODO: similiar code as room.type -> unify
        domain = []
        if code_class:
            domain += ["&", ("code_class", "=", code_class)]
        domain += [
            "|",
            ("pms_property_ids", "in", pms_property_id),
            ("pms_property_ids", "=", False),
        ]
        records = self.search(domain)
        res, res_priority = {}, {}
        for rec in records:
            res_priority.setdefault(rec.code_class, -1)
            priority = rec.pms_property_ids and 1 or 0
            if priority > res_priority[rec.code_class]:
                res.setdefault(rec.code_class, rec.id)
                res[rec.code_class], res_priority[rec.code_class] = rec.id, priority
            elif priority == res_priority[rec.code_class]:
                raise ValidationError(
                    _(
                        "Integrity error: There's multiple room types "
                        "with the same code %s and properties"
                    )
                    % rec.code_class
                )
        return self.browse(list(res.values()))

    @api.constrains("code_class", "pms_property_ids")
    def _check_code_property_uniqueness(self):
        # TODO: similiar code as room.type -> unify
        msg = _(
            "Already exists another room type class with the same code and properties"
        )
        for rec in self:
            if not rec.pms_property_ids:
                if self.search(
                    [
                        ("id", "!=", rec.id),
                        ("code_class", "=", rec.code_class),
                        ("pms_property_ids", "=", False),
                    ]
                ):
                    raise ValidationError(msg)
            else:
                for pms_property in rec.pms_property_ids:
                    other = rec.get_unique_by_property_code(
                        pms_property.id, rec.code_class
                    )
                    if other and other != rec:
                        raise ValidationError(msg)
