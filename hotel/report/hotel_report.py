# -*- coding: utf-8 -*-
# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp import models

# Old SXW engine was removed already in v11. You should update your code with
# current engine tools.
# class FolioReport():
#     def __init__(self, cr, uid, name, context):
#         super(FolioReport, self).__init__(cr, uid, name, context)
#         self.localcontext.update({'time': time,
#                                   'get_data': self.get_data,
#                                   'get_Total': self.getTotal,
#                                   'get_total': self.gettotal,
#                                   })
#         self.temp = 0.0
#
#     def get_data(self, date_start, date_end):
#         folio_obj = self.pool.get('hotel.folio')
#         tids = folio_obj.search(self.cr, self.uid,
#                                 [('checkin_date', '>=', date_start),
#                                  ('checkout_date', '<=', date_end)])
#         res = folio_obj.browse(self.cr, self.uid, tids)
#         return res
#
#     def gettotal(self, total):
#         self.temp = self.temp + float(total)
#         return total
#
#     def getTotal(self):
#         return self.temp
#
#
# class ReportLunchorder(models.AbstractModel):
#     _name = 'report.hotel.report_hotel_folio'
#     _inherit = 'report.report_xlsx.abstract'
#     _template = 'hotel.report_hotel_folio'
#     _wrapped_report_class = FolioReport
