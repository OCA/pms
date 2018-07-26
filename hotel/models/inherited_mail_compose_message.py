# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'hotel.folio' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            folio = self.env['hotel.folio'].browse([
                self._context['default_res_id']
            ])
            if folio:
                cmds = []
                for lid in folio.room_lines._ids:
                    cmds.append((
                        1,
                        lid,
                        {'to_send': False}
                    ))
                if cmds:
                    folio.room_lines = cmds
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
