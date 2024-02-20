# Copyright 2020 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    pre_assigned_room_ids = fields.Many2many(
        comodel_name="pms.room",
        string="Pre Assigned Rooms",
        help="Rooms pre assigned to this employee",
    )

    allowed_pre_assigned_room_ids = fields.Many2many(
        comodel_name="pms.room",
        string="Allowed Pre Assigned Rooms",
        help="Rooms allowed to be pre assigned to this employee",
        compute="_compute_allowed_pre_assigned_room_ids",
    )

    job_name = fields.Char(string="Job Name", compute="_compute_job_name")

    @api.constrains("pre_assigned_room_ids")
    def _check_pre_assigned_room_ids(self):
        for record in self:
            if record.pre_assigned_room_ids:
                for room in record.pre_assigned_room_ids:
                    if room not in record.allowed_pre_assigned_room_ids:
                        raise ValidationError(
                            _("The room should belong to the employee's property.")
                        )

    @api.constrains("pre_assigned_room_ids")
    def _check_job_id(self):
        for record in self:
            if (
                record.job_id
                and record.job_id
                != self.env.ref("pms_housekeeping.housekeeping_job_id")
                and record.pre_assigned_room_ids
            ):
                raise ValidationError(_("The job position should be Housekeeper."))

    @api.depends("job_id")
    def _compute_job_name(self):
        for record in self:
            record.job_name = record.job_id.name

    @api.depends("property_ids")
    def _compute_allowed_pre_assigned_room_ids(self):
        for record in self:
            domain = []
            if record.property_ids:
                domain.append(("pms_property_id", "in", record.property_ids.ids))
            record.allowed_pre_assigned_room_ids = (
                self.env["pms.room"].search(domain).ids
            )
