# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'hotel.folio' and \
                self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            folio = self.env['hotel.folio'].browse([
                self._context['default_res_id']
            ])
            if folio:
                cmds = [(1, lid, {'to_send': False}) for lid in folio.room_lines.ids]
                if any(cmds):
                    folio.room_lines = cmds
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
