# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ChannelWubookPmsAvailabilityBinding(models.Model):
    _name = "channel.wubook.pms.availability"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.availability": "odoo_id"}

    external_id = fields.Char()

    odoo_id = fields.Many2one(
        comodel_name="pms.availability",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    sale_avail = fields.Integer(
        store=True,
        compute="_compute_sale_avail",
        inverse="_inverse_sale_avail",
    )

    @api.depends(
        "odoo_id.real_avail",
        "odoo_id.avail_rule_ids",
        "odoo_id.avail_rule_ids.plan_avail",
        "odoo_id.room_type_id.channel_wubook_bind_ids.default_availability",
    )
    def _compute_sale_avail(self):
        for record in self:
            rules = record.avail_rule_ids.filtered(
                lambda r: record.backend_id
                in r.availability_plan_id.channel_wubook_bind_ids.mapped("backend_id")
            )
            if not rules:
                with self.backend_id.work_on("channel.wubook.pms.room.type") as work:
                    binder = work.component(usage="binder")
                min_avail = min(
                    record.real_avail,
                    binder.wrap_record(record.room_type_id).default_availability,
                )
                if record.sale_avail != min_avail:
                    # Odoo Poltergeist: This should be 'record.sale_avail ='
                    # but doing so the write method of record is never
                    # executed and the listener never triggered.
                    # Misteriously the data is actually saved to the database
                    record.write({"sale_avail": min_avail})
            else:
                for field in ["quota", "max_avail"]:
                    inconsistence = len(set(rules.mapped(field))) > 1
                    if not inconsistence:
                        sale_avail = rules[0].plan_avail
                    else:
                        # context to ensure that the user is notified
                        rule_id = self._context.get("force_rule_id")
                        force_rule = self.env["pms.availability.plan.rule"].browse(
                            rule_id
                        )
                        if force_rule:
                            # TODO: move this logic to plan rule
                            rules[field] = force_rule[field]
                            sale_avail = force_rule.plan_avail
                        else:
                            raise ValidationError(
                                _(
                                    "More than one rule found, you need to specify the rule in the context"
                                )
                            )
                    if record.sale_avail != sale_avail:
                        # Odoo Poltergeist: same as before
                        record.write({"sale_avail": sale_avail})

    def _inverse_sale_avail(self):
        for record in self:
            if record.sale_avail > record.real_avail:
                # TODO: exportar a wubook el real_avail, corregir wubook
                continue
            rules = record.avail_rule_ids.filtered(
                lambda r: record.backend_id
                in r.availability_plan_id.channel_wubook_bind_ids.mapped("backend_id")
            )
            plans = self.env["pms.availability.plan"].search(
                [
                    ("channel_wubook_bind_ids.backend_id", "in", self.backend_id.ids),
                ]
            )
            for plan in plans:
                if plan not in rules.availability_plan_id:
                    plan.write(
                        {
                            "rule_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "room_type_id": record.room_type_id.id,
                                        "date": record.date,
                                        "pms_property_id": record.pms_property_id.id,
                                        "quota": record.sale_avail,
                                    },
                                )
                            ]
                        }
                    )
                else:
                    rules.filtered(
                        lambda x: x.quota != record.sale_avail
                    ).quota = record.sale_avail

    @api.model
    def export_data(self, backend_id, date_from, date_to, room_type_ids):
        """ Prepare the batch export records to Backend """
        domain = [("pms_property_id", "=", backend_id.pms_property_id.id)]
        if date_from and date_to:
            domain += [("date", ">=", date_from), ("date", "<=", date_to)]
        if room_type_ids:
            domain += [("room_type_id", "in", room_type_ids.ids)]
        return self.export_batch(backend_record=backend_id, domain=domain)
