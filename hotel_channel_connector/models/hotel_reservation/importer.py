# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo import fields, api, _
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)


class HotelReservationImporter(Component):
    _name = 'channel.hotel.reservation.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.reservation']
    _usage = 'hotel.reservation.importer'
