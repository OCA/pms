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
    _order = "sequence, name, default_code"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Class Name",
        help="Name of the room type class",
        required=True,
        translate=True,
    )
    active = fields.Boolean(
        string="Active",
        help="If unchecked, it will allow you to hide the room type",
        default=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Field used to change the position of the room type classes in tree view.",
        default=0,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="pms_room_type_class_property_rel",
        column1="room_type_class_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    room_type_ids = fields.One2many(
        string="Types",
        help="Room Types that belong to this Room Type Class",
        comodel_name="pms.room.type",
        inverse_name="class_id",
        check_pms_properties=True,
    )
    default_code = fields.Char(
        string="Code",
        help="Room type class identification code",
        required=True,
    )

    @api.model
    def get_unique_by_property_code(self, pms_property_id, default_code=None):
        """
        :param pms_property_id: property ID
        :param default_code: room type code (optional)
        :return: - recordset of
                    - all the pms.room.type.class of the pms_property_id
                      if default_code not defined
                    - one or 0 pms.room.type.class if default_code defined
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
                        "Integrity error: There's multiple room types "
                        "with the same code %s and properties"
                    )
                    % rec.default_code
                )
        return self.browse(list(res.values()))

    @api.constrains("default_code", "pms_property_ids")
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
