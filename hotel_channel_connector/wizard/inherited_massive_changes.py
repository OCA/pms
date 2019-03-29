# Copyright 2018-2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class MassiveChangesWizard(models.TransientModel):
    _inherit = 'hotel.wizard.massive.changes'

    section = fields.Selection(selection_add=[
        ('avail', 'Availability'),
    ])

    # Availability fields
    change_quota = fields.Boolean(default=False)
    quota = fields.Integer('Quota', default=0)
    change_max_avail = fields.Boolean(default=False)
    max_avail = fields.Integer('Max. Avail.', default=0)
    change_no_ota = fields.Boolean(default=False)
    no_ota = fields.Boolean('No OTA', default=False)

    @api.model
    def _get_availability_values(self, ndate, room_type, record):
        vals = {}
        if record.change_quota:
            vals.update({
                'quota': record.quota,
            })
        if record.change_no_ota:
            vals.update({
                'no_ota': record.no_ota,
            })
        if record.change_max_avail:
            vals.update({
                'max_avail': record.max_avail,
            })

        return vals

    @api.model
    def _save_availability(self, ndate, room_types, record):
        hotel_room_type_avail_obj = self.env['hotel.room.type.availability']
        domain = [('date', '=', ndate.strftime(DEFAULT_SERVER_DATE_FORMAT))]

        for room_type in room_types:
            vals = self._get_availability_values(ndate, room_type, record)
            if not any(vals):
                continue

            room_types_avail = hotel_room_type_avail_obj.search(
                domain+[('room_type_id', '=', room_type.id)]
            )
            if any(room_types_avail):
                # Mail module want a singleton
                for vr_avail in room_types_avail:
                    vr_avail.write(vals)
            else:
                vals.update({
                    'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'room_type_id': room_type.id
                })
                hotel_room_type_avail_obj.with_context({
                    'mail_create_nosubscribe': True,
                }).create(vals)

    @api.multi
    def massive_change(self):
        res = super(MassiveChangesWizard, self).massive_change()
        self.env['channel.backend'].cron_push_changes()
        return res

    @api.multi
    def massive_change_close(self):
        res = super(MassiveChangesWizard, self).massive_change_close()
        self.env['channel.backend'].cron_push_changes()
        return res

    @api.model
    def _save(self, ndate, room_types, record):
        super(MassiveChangesWizard, self)._save(ndate, room_types, record)
        if record.section == 'avail':
            self._save_availability(ndate, room_types, record)
