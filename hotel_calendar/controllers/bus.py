# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.http import request
from odoo.addons.bus.controllers.main import BusController

HOTEL_BUS_CHANNEL_ID = 'hpublic'


# More info...
# https://github.com/odoo/odoo/commit/092cf33f93830daf5e704b964724bdf8586da8d9
class Controller(BusController):
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            # registry, cr, uid, context = request.registry, request.cr, \
            #                              request.session.uid, request.context
            channels = channels + [(
                request.db,
                'hotel.reservation',
                HOTEL_BUS_CHANNEL_ID
            )]
        return super(Controller, self)._poll(dbname, channels, last, options)
