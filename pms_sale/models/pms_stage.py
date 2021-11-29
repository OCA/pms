# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PMSStage(models.Model):
    _inherit = "pms.stage"

    stage_type = fields.Selection(
        selection_add=[("reservation", "Reservation")],
        ondelete={"reservation": "cascade"},
    )

    def get_color_information(self):
        # get stage ids
        stage_ids = self.search([])
        color_information_dict = []
        for stage in stage_ids:
            color_information_dict.append(
                {
                    "color": stage.custom_color,
                    "field": "stage_id",
                    "opt": "==",
                    "value": stage.name,
                }
            )
        return color_information_dict
