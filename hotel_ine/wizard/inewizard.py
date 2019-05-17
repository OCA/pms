# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
import base64
import datetime
import calendar
import xml.etree.cElementTree as ET
from openerp.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


def _get_default_date(option):
    now = datetime.datetime.now()
    month = int(now.month)-1
    year = int(now.year)
    if month <= 0:
        month = 12
        year -= year
    start_date = datetime.datetime(year, month, 1)
    end_date = calendar.monthrange(year, month)[1] - 1
    month_end_date = start_date + datetime.timedelta(days=end_date)
    if option == "start":
        return start_date
    return month_end_date


class Wizard(models.TransientModel):
    _name = 'ine.wizard'

    @api.onchange('ine_start')
    def onchange_ine_start(self):
        if self.ine_start > self.ine_end:
            self.ine_start = self.ine_end

    txt_filename = fields.Char()
    txt_binary = fields.Binary()
    ine_start = fields.Date("Fecha inicio", default=_get_default_date('start'))
    ine_end = fields.Date("Fecha final", default=_get_default_date('end'))

    adr_screen = fields.Char()
    rev_screen = fields.Char()


# Debug Stop -------------------
# import wdb; wdb.set_trace()
# Debug Stop -------------------
