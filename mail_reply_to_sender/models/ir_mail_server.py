# -*- coding: utf-8 -*-

from odoo import models,api

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def get_mail_values(self, res_ids):
        res = super(MailComposer, self).get_mail_values(res_ids)
        if self.composition_mode == 'comment':
            mail_reply_to = getattr(self, 'reply_to', None)
            if mail_reply_to:
                for f, x in res.items():
                    if 'reply_to' not in x:
                        x['reply_to'] = mail_reply_to
        return res
