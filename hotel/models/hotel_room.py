# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    """ The rooms for lodging can be for sleeping, usually called rooms,
     and also for speeches (conference rooms), parking,
     relax with cafe con leche, spa...
     """
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _order = "sequence, room_type_id, name"

    # Fields declaration
    name = fields.Char('Room Name', required=True)
    hotel_id = fields.Many2one(
        'hotel.property',
        store=True,
        readonly=True,
        related='room_type_id.hotel_id')
    room_type_id = fields.Many2one(
        'hotel.room.type',
        'Hotel Room Type',
        required=True,
        ondelete='restrict')
    shared_room_id = fields.Many2one(
        'hotel.shared.room',
        'Shared Room',
        default=False)
    floor_id = fields.Many2one(
        'hotel.floor',
        'Ubication',
        help='At which floor the room is located.')
    capacity = fields.Integer('Capacity')
    to_be_cleaned = fields.Boolean('To be Cleaned', default=False)
    extra_beds_allowed = fields.Integer('Extra beds allowed',
                                        default='0',
                                        required=True)
    description_sale = fields.Text(
        'Sale Description', translate=True,
        help="A description of the Product that you want to communicate to "
             " your customers. This description will be copied to every Sales "
             " Order, Delivery Order and Customer Invoice/Credit Note")
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=0)

    # Constraints and onchanges
    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity < 1:
                raise ValidationError(_("The capacity of the \
                                        room must be greater than 0."))

    # CRUD methods
    @api.model
    def create(self, vals):
        if vals.get('hotel_id', self.env.user.hotel_id.id) != \
            self.env['hotel.room.type'].browse(
                    vals['room_type_id']).hotel_id.id:
                raise ValidationError(
                    _("A room cannot be created in a room type \
                      of another hotel."))
        return super().create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            if vals.get('hotel_id', record.hotel_id.id) != record.hotel_id.id:
                raise ValidationError(
                    _("A room cannot be changed to another hotel.") + " " +
                    _("%s does not belong to %s.")
                    % (record, record.hotel_id))
            room_type_ids = self.env['hotel.room.type'].search([
                ('hotel_id', '=', record.hotel_id.id)
            ]).ids
            if vals.get('room_type_id', record.room_type_id.id) \
                    not in room_type_ids:
                raise ValidationError(
                    _("A room cannot be changed to a room type of \
                      another hotel or unlinked from a room type."))
        return super().write(vals)

    # Business methods
    @api.multi
    def get_capacity(self, extra_bed=0):
        if not self.shared_room_id:
            return self.capacity + extra_bed
        return self.capacity
