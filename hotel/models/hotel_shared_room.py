# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelSharedRoom(models.Model):
    _name = 'hotel.shared.room'
    _description = 'Hotel Shared Room'
    _order = "room_type_id, name"

    name = fields.Char('Room Name', required=True)
    active = fields.Boolean('Active', default=True)
    room_type_id = fields.Many2one(
        'hotel.room.type', 'Hotel Room Type',
        required=True, ondelete='restrict',
        domain=[('shared_room', '=', True)]
        )
    floor_id = fields.Many2one('hotel.floor', 'Ubication',
                               help='At which floor the room is located.',
                               ondelete='restrict',)
    sequence = fields.Integer('Sequence', required=True)
    beds = fields.Integer('Beds')
    bed_ids = fields.One2many('hotel.room',
                              'shared_room_id',
                              readonly=True,
                              ondelete='restrict',)
    description_sale = fields.Text(
        'Sale Description', translate=True,
        help="A description of the Product that you want to communicate to "
             " your customers. This description will be copied to every Sales "
             " Order, Delivery Order and Customer Invoice/Credit Note")

    @api.constrains('beds')
    def _constrain_beds(self):
        self.ensure_one()
        if self.beds < 1:
            raise ValidationError(_("Room beds can't be less than one"))
        if len(self.bed_ids) > self.beds:
            raise ValidationError(_(
                "If you want to eliminate beds in the \
                room you must deactivate the beds from your form"))
        beds = []
        inactive_beds = self.env['hotel.room'].search([
            ('active', '=', False),
            ('shared_room_id', '=', self.id)
        ])
        for i in range(len(self.bed_ids), self.beds):
            if inactive_beds:
                bed = inactive_beds[0]
                bed.update({'active': True})
                inactive_beds -= bed
                continue
            name = u'%s (%s)' % (self.name, i)
            bed_vals = {
                'name': name,
                'max_adult': 1,
                'max_child': 0,
                'capacity': 1,
                'room_type_id': self.room_type_id.id,
                'sequence': self.sequence,
                'floor_id': self.floor_id.id if self.floor_id else False,
                'shared_room_id': self.id,
            }
            beds.append((0, False, bed_vals))
        if beds:
            self.update({
                'bed_ids': beds
            })

    @api.constrains('active')
    def _constrain_active(self):
        self.bed_ids.write({
            'active': self.active,
        })

    @api.constrains('room_type_id')
    def _constrain_room_type_id(self):
        self.bed_ids.write({
            'room_type_id': self.room_type_id.id,
        })

    @api.constrains('floor_id')
    def _constrain_floor_id(self):
        self.bed_ids.write({
            'floor_id': self.floor_id.id,
        })

    @api.constrains('sequence')
    def _constrain_sequence(self):
        self.bed_ids.write({
            'sequence': self.sequence,
        })

    @api.constrains('descrition_sale')
    def _constrain_descrition_sale(self):
        self.bed_ids.write({
            'description_sale': self.descrition_sale,
        })
