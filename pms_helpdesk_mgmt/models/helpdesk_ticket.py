# Copyright (C) 2024 Irlui Ramírez <iramirez.spain@gmail.com>
# Copyright (C) 2024 Oso Tranquilo <informatica@gmail.com>
# Copyright (C) 2024 Consultores Hoteleros Integrales <www.aldahotels.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsHelpdeskTicket(models.Model):

    _inherit = "helpdesk.ticket"

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        domain="[('company_id', '=', company_id)]",
        help="The property associated with this ticket",
    )
    room_id = fields.Many2one(
        comodel_name="pms.room",
        string="Room",
        domain="[('pms_property_id', '=', pms_property_id)]",
        help="The room associated with this ticket",
        widget="many2one_tags",
    )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            allowed_pms_property_ids = self.env.user.get_active_property_ids()
            return {
                "domain": {"pms_property_id": [("id", "in", allowed_pms_property_ids)]}
            }
        else:
            return {"domain": {"pms_property_id": []}}

    @api.constrains("company_id", "pms_property_id")
    def _check_property_company_consistency(self):
        for record in self:
            if (
                record.pms_property_id
                and record.pms_property_id.company_id != record.company_id
            ):
                raise UserError(
                    _(
                        "The selected property does not belong to the selected company. "
                        "Please select a property that belongs to the correct company."
                    )
                )

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
