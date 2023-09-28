# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from psycopg2.extensions import AsIs

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

AUTO_EXPORT_FIELDS = [
    "min_stay",
    "max_stay",
    "closed",
    "min_stay_arrival",
    "max_stay_arrival",
    "closed_arrival",
    "closed_departure",
]


class PmsRoomTypeAvailabilityRule(models.Model):
    _inherit = "pms.availability.plan.rule"

    channel_wubook_bind_ids = fields.One2many(
        comodel_name="channel.wubook.pms.availability.plan.rule",
        inverse_name="odoo_id",
        string="Channel Wubook PMS Bindings",
    )

    def wubook_date_valid(self):
        # Wubook does not allow to update records older than 2 days ago
        return (fields.Date.today() - self.date).days <= 2

    inconsistent_rules = fields.Many2many(
        readonly=True,
        store=False,
        comodel_name="pms.availability.plan.rule",
        compute="_compute_inconsistent_rules",
    )

    inconsistent_rule_count = fields.Integer(
        readonly=True,
        store=False,
        compute_sudo=True,
        compute="_compute_inconsistent_rules",
    )

    @api.depends("quota", "max_avail", "channel_wubook_bind_ids.no_ota")
    def _compute_inconsistent_rules(self):
        for rec in self:
            if rec.channel_wubook_bind_ids:
                inconsistent_rules = self.search(
                    [
                        ("room_type_id", "=", rec.room_type_id.id),
                        ("date", "=", rec.date),
                        (
                            "channel_wubook_bind_ids.backend_id",
                            "in",
                            rec.channel_wubook_bind_ids.backend_id.ids,
                        ),
                        "|",
                        ("quota", "!=", rec.quota),
                        ("max_avail", "!=", rec.max_avail),
                    ]
                )
                inconsistent_rules.filtered(
                    lambda x: x.quota != rec.quota
                ).quota = rec.quota
                inconsistent_rules.filtered(
                    lambda x: x.max_avail != rec.max_avail
                ).max_avail = rec.max_avail
                rec.inconsistent_rules = inconsistent_rules
                other_inconsistent_rules = inconsistent_rules.filtered(
                    lambda x: x.id not in rec.ids
                )
                inconsistent_binding_rules = rec.channel_wubook_bind_ids.mapped(
                    "inconsistent_binding_rules"
                )
                rec.inconsistent_rule_count = len(other_inconsistent_rules) + len(
                    inconsistent_binding_rules
                )
            else:
                rec.inconsistent_rules = False
                rec.inconsistent_rule_count = 0

    def _write(self, vals):
        cr = self._cr
        if any([field in vals for field in AUTO_EXPORT_FIELDS]):
            query = (
                'UPDATE "channel_wubook_pms_availability_plan_rule" SET "actual_write_date"=%s WHERE odoo_id IN %%s'
                % (AsIs("(now() at time zone 'UTC')"))
            )
            for sub_ids in cr.split_for_in_conditions(set(self.ids)):
                cr.execute(query, [sub_ids])
        res = super()._write(vals)
        return res
