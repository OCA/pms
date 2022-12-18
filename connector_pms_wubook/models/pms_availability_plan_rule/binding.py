# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, ValidationError

AUTO_EXPORT_FIELDS = [
    "no_ota",
    "odoo_id",
]


class ChannelWubookPmsAvailabilityPlanRuleBinding(models.Model):
    _name = "channel.wubook.pms.availability.plan.rule"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.availability.plan.rule": "odoo_id"}

    external_id = fields.Char(string="External ID")

    odoo_id = fields.Many2one(
        comodel_name="pms.availability.plan.rule",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    channel_wubook_availability_plan_id = fields.Many2one(
        comodel_name="channel.wubook.pms.availability.plan",
        string="Wubook Plan ID",
        required=True,
        ondelete="cascade",
    )

    no_ota = fields.Boolean(
        string="No OTA",
        default=False,
        help="Set zero availability to the connected OTAs "
        "even when the availability is positive,"
        "except to the Online Reception (booking engine)",
    )

    inconsistent_binding_rules = fields.Many2many(
        readonly=True,
        store=False,
        comodel_name="channel.wubook.pms.availability.plan.rule",
        compute="_compute_inconsistent_binding_rules",
    )

    @api.depends("no_ota")
    def _compute_inconsistent_binding_rules(self):
        for rec in self:
            inconsistent_binding_rules = self.search(
                [
                    ("id", "not in", rec.ids),
                    ("room_type_id", "=", rec.room_type_id.id),
                    ("date", "=", rec.date),
                    ("backend_id", "=", rec.backend_id.id),
                    ("no_ota", "!=", rec.no_ota),
                ]
            )
            inconsistent_binding_rules.no_ota = rec.no_ota
            rec.inconsistent_binding_rules = inconsistent_binding_rules

    @api.constrains("pms_property_id")
    def _check_pms_property_id(self):
        for rec in self:
            if rec.pms_property_id != rec.backend_id.pms_property_id:
                raise ValidationError(
                    _("The property on the rule must match the ones on the bindings")
                )

    @api.model
    def create(self, vals):
        channel_wubook_availability_plan_id = vals.get(
            "channel_wubook_availability_plan_id"
        )
        if channel_wubook_availability_plan_id:
            binding = self.channel_wubook_availability_plan_id.browse(
                channel_wubook_availability_plan_id
            )
            vals["availability_plan_id"] = binding.odoo_id.id
        else:
            # TODO: put this code on mapper???? Is it possible??
            backend = self.backend_id.browse(vals["backend_id"])
            with backend.work_on(
                self.channel_wubook_availability_plan_id._name
            ) as work:
                binder = work.component(usage="binder")
            plan_binding = binder.wrap_record(
                self.odoo_id.browse(vals["odoo_id"]).availability_plan_id
            )
            vals["channel_wubook_availability_plan_id"] = plan_binding.id
        binding = super().create(vals)
        return binding

    def _write(self, vals):
        cr = self._cr
        if any([field in vals for field in AUTO_EXPORT_FIELDS]):
            query = (
                'UPDATE "%s" SET "fields_auto_export_to_sync"=True WHERE id IN %%s'
                % (self._table)
            )
            for sub_ids in cr.split_for_in_conditions(set(self.ids)):
                cr.execute(query, [sub_ids])
                if cr.rowcount != len(sub_ids):
                    raise MissingError(
                        _(
                            "One of the records you are trying to modify has already been deleted (Document type: %s).",
                            self._description,
                        )
                        + "\n\n({} {}, {} {})".format(
                            _("Records:"), sub_ids[:6], _("User:"), self._uid
                        )
                    )
        res = super()._write(vals)
        return res
