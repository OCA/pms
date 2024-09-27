# Copyright (C) 2024 Irlui Ramírez <iramirez.spain@gmail.com>
# Copyright (C) 2024 Oso Tranquilo <informatica@gmail.com>
# Copyright (C) 2024 Consultores Hoteleros Integrales <www.aldahotels.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsHelpdeskTicket(models.Model):

    _inherit = "helpdesk.ticket"

    pms_property_id = fields.Many2one(
        string="Property",
        help="The property linked to this ticket.",
        comodel_name="pms.property",
        required=True,
    )
    room_id = fields.Many2one(
        comodel_name="pms.room",
        string="Room",
        domain="[('pms_property_id', '=', pms_property_id)]",
        help="The room associated with this ticket",
        widget="many2one_tags",
    )

    @api.model
    def _get_default_pms_property(self):
        user = self.env.user
        active_property_ids = user.get_active_property_ids()
        if active_property_ids:
            return active_property_ids[0]
        return None

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            allowed_pms_property_ids = self.env.user.get_active_property_ids()
            if (
                self.pms_property_id
                and self.pms_property_id.company_id != self.company_id
            ):
                self.pms_property_id = False

            return {
                "domain": {
                    "pms_property_id": [
                        ("id", "in", allowed_pms_property_ids),
                        ("company_id", "=", self.company_id.id),
                    ]
                }
            }
        else:
            self.pms_property_id = (
                False  # Reinicia la propiedad si no hay compañía seleccionada
            )
            return {"domain": {"pms_property_id": []}}

    @api.onchange("pms_property_id")
    def _onchange_property_id(self):
        if self.pms_property_id:
            rooms = (
                self.env["pms.room"]
                .sudo()
                .search([("pms_property_id", "=", self.pms_property_id.id)])
            )
            room_ids = rooms.ids if rooms else []
            return {"domain": {"room_id": [("id", "in", room_ids)]}}
        else:
            return {"domain": {"room_id": []}}

    def write(self, vals):
        if "partner_id" not in vals or not vals.get("partner_id"):
            vals["partner_id"] = self.env.uid
        return super(PmsHelpdeskTicket, self).write(vals)
