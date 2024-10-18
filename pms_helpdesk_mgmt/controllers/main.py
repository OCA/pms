# Copyright (C) 2024 Irlui Ramírez <iramirez.spain@gmail.com>
# Copyright (C) 2024 Oso Tranquilo <informatica@gmail.com>
# Copyright (C) 2024 Consultores Hoteleros Integrales <www.aldahotels.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

import odoo.http as http
from odoo.http import request

from odoo.addons.helpdesk_mgmt.controllers.main import HelpdeskTicketController

_logger = logging.getLogger(__name__)


class CustomHelpdeskTicketController(HelpdeskTicketController):
    @http.route("/get_companies", type="json", auth="user")
    def get_companies(self):
        user = request.env.user
        allowed_pms_property_ids = user.get_active_property_ids()
        if allowed_pms_property_ids:
            properties = (
                request.env["pms.property"].sudo().browse(allowed_pms_property_ids)
            )
            companies = properties.mapped("company_id")
        else:
            companies = request.env["res.company"].sudo().search([])

        companies_data = [
            {"id": company.id, "name": company.name} for company in companies
        ]
        return {"companies": companies_data}

    @http.route("/get_properties", type="json", auth="user")
    def get_properties(self, company_id):
        properties = (
            request.env["pms.property"]
            .sudo()
            .search([("company_id", "=", int(company_id))])
        )
        properties_data = [{"id": prop.id, "name": prop.name} for prop in properties]
        return {"properties": properties_data}

    @http.route("/get_rooms", type="json", auth="user")
    def get_rooms(self, property_id):
        rooms = (
            request.env["pms.room"]
            .sudo()
            .search([("pms_property_id", "=", int(property_id))])
        )
        rooms_data = [{"id": room.id, "name": room.name} for room in rooms]
        return {"rooms": rooms_data}

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        response = super().create_new_ticket(**kw)
        user = request.env.user
        user_belongs_to_group = user.has_group(
            "helpdesk_mgmt.group_helpdesk_user_team"
        ) or user.has_group("helpdesk_mgmt.group_helpdesk_manager")
        company = request.env.company
        tag_model = http.request.env["helpdesk.ticket.tag"]
        tags = tag_model.with_company(company.id).search([("active", "=", True)])
        allowed_pms_property_ids = user.get_active_property_ids()
        properties = request.env["pms.property"].sudo().browse(allowed_pms_property_ids)
        companies = properties.mapped("company_id")
        all_room_ids = [
            room_id for property in properties for room_id in property.room_ids.ids
        ]
        room_model = http.request.env["pms.room"]
        rooms = room_model.sudo().search([("id", "in", all_room_ids)])
        response.qcontext.update(
            {
                "user_belongs_to_group": user_belongs_to_group,
                "companies": companies,
                "properties": properties,
                "rooms": rooms,
                "tags": tags,
            }
        )
        return response

    def _prepare_submit_ticket_vals(self, **kw):
        vals = super()._prepare_submit_ticket_vals(**kw)
        selected_company = kw.get("company_id")
        if selected_company is None:
            company = http.request.env.user.company_id
        else:
            company = (
                http.request.env["res.company"].sudo().browse(int(selected_company))
            )
        vals.update(
            {
                "company_id": company.id,
                "pms_property_id": request.params.get("pms_property_id"),
                "room_id": request.params.get("room_id"),
                "tag_ids": [request.params.get("tag_ids")],
            }
        )
        return vals
