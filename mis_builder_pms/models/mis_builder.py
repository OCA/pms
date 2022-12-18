# Copyright 2022 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class MisReportInstance(models.Model):

    _inherit = "mis.report.instance"

    pms_property_ids = fields.Many2many(
        "pms.property",
        string="PMS Properties",
    )

    def _add_analytic_filters_to_context(self, context):
        super()._add_analytic_filters_to_context(context)
        if self.pms_property_ids:
            context["mis_report_filters"]["pms_property_id"] = {
                "value": self.pms_property_ids.ids,
                "operator": "in",
            }

    @api.model
    def get_filter_descriptions_from_context(self):
        filter_descriptions = super().get_filter_descriptions_from_context()
        filters = self.env.context.get("mis_report_filters", {})
        pms_property_value = filters.get("pms_property_id", {}).get("value")
        if pms_property_value:
            pms_properties = self.env["pms.property"].browse(pms_property_value)
            filter_descriptions.append(
                _("PMS Properties: %s") % ", ".join(pms_properties.mapped("name"))
            )
        return filter_descriptions


class MisReportInstancePeriod(models.Model):

    _inherit = "mis.report.instance.period"

    pms_property_ids = fields.Many2many(
        "pms.property",
        string="PMS Properties",
    )

    def _get_additional_move_line_filter(self):
        aml_domain = super()._get_additional_move_line_filter()
        if self.report_instance_id.pms_property_ids:
            aml_domain.append(
                (
                    "pms_property_id",
                    "in",
                    self.report_instance_id.pms_property_ids.ids,
                )
            )
        if self.pms_property_ids:
            aml_domain.append(
                ("pms_property_id", "in", self.pms_property_ids.ids),
            )
        return aml_domain
