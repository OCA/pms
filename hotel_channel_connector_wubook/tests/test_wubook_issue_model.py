# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
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
from openerp.exceptions import ValidationError
from .common import TestHotelWubook


class TestWubookIssue(TestHotelWubook):

    def test_mark_readed(self):
        wubook_issue_obj = self.env['wubook.issue']
        issue_a = wubook_issue_obj.create({
            'section': 'wubook',
            'message': 'Testing #1',
        })
        self.assertTrue(issue_a, "Can't create issues")
        issue_a.sudo(self.user_hotel_manager).mark_readed()
        self.assertFalse(issue_a.to_read, "Can't mark issue as readed")

    def test_toggle_to_read(self):
        wubook_issue_obj = self.env['wubook.issue']
        issue_a = wubook_issue_obj.create({
            'section': 'wubook',
            'message': 'Testing #1',
        })
        self.assertTrue(issue_a, "Can't create issues")
        issue_a.sudo(self.user_hotel_manager).toggle_to_read()
        self.assertFalse(issue_a.to_read, "Can't toggle read status")

    def test_mark_as_read(self):
        wubook_issue_obj = self.env['wubook.issue']
        issue_a = wubook_issue_obj.create({
            'section': 'reservation',
            'message': 'Testing #1',
            'wid': 'test',
        })
        self.assertTrue(issue_a, "Can't create issues")
        issue_a.sudo(self.user_hotel_manager).mark_as_read()
