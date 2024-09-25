from operator import itemgetter

from odoo import http
from odoo.http import request
from odoo.tools import groupby as groupbyelem

from odoo.addons.helpdesk_mgmt.controllers.myaccount import CustomerPortalHelpdesk
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CustomCustomerPortalHelpdesk(CustomerPortalHelpdesk):
    def _prepare_home_portal_values(self, counters):
        values = super(CustomCustomerPortalHelpdesk, self)._prepare_home_portal_values(
            counters
        )

        if "ticket_count" in counters:
            helpdesk_model = request.env["helpdesk.ticket"].sudo()
            active_property_ids = request.env.user.get_active_property_ids()
            domain = []
            if active_property_ids:
                domain.append(("pms_property_id", "in", active_property_ids))

            ticket_count = (
                helpdesk_model.search_count(domain)
                if helpdesk_model.check_access_rights("read", raise_exception=False)
                else 0
            )
            values["ticket_count"] = ticket_count

        return values

    @http.route(
        ["/my/tickets", "/my/tickets/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_tickets(self, page=1, **kw):
        response = super(CustomCustomerPortalHelpdesk, self).portal_my_tickets(
            page=page, **kw
        )
        domain = response.qcontext.get("domain", [])
        response.qcontext.get("sortby")
        response.qcontext.get("groupby")
        order = response.qcontext.get("order")

        active_property_ids = request.env.user.get_active_property_ids()
        if active_property_ids:
            domain.append(("pms_property_id", "in", active_property_ids))

        HelpdeskTicket = request.env["helpdesk.ticket"].sudo()
        ticket_count = HelpdeskTicket.search_count(domain)

        pager = portal_pager(
            url="/my/tickets",
            url_args={},
            total=ticket_count,
            page=page,
            step=self._items_per_page,
        )

        tickets = HelpdeskTicket.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_tickets_history"] = tickets.ids[:100]

        group = response.qcontext.get("group", None)
        if group:
            grouped_tickets = [
                HelpdeskTicket.concat(*g)
                for k, g in groupbyelem(tickets, itemgetter(group))
            ]
        else:
            grouped_tickets = [tickets] if tickets else []

        response.qcontext.update(
            {
                "grouped_tickets": grouped_tickets,
                "pager": pager,
                "ticket_count": ticket_count,
            }
        )
        return request.render(
            "pms_helpdesk_mgmt.portal_my_tickets_inherited", response.qcontext
        )

    @http.route(
        ["/my/ticket/<int:ticket_id>"], type="http", auth="public", website=True
    )
    def portal_my_ticket(self, ticket_id, access_token=None, **kw):
        HelpdeskTicket = request.env["helpdesk.ticket"].sudo()

        if access_token:
            ticket_sudo = HelpdeskTicket.search(
                [("id", "=", ticket_id), ("access_token", "=", access_token)]
            )
        else:
            ticket_sudo = HelpdeskTicket.search([("id", "=", ticket_id)])

        if not ticket_sudo:
            return request.redirect("/my")

        for attachment in ticket_sudo.attachment_ids:
            attachment.generate_access_token()

        values = self._ticket_get_page_view_values(ticket_sudo, access_token, **kw)
        return request.render("pms_helpdesk_mgmt.portal_helpdesk_ticket_page", values)

    def _ticket_get_page_view_values(self, ticket, access_token, **kwargs):
        closed_stages = (
            request.env["helpdesk.ticket.stage"].sudo().search([("closed", "=", True)])
        )

        values = {
            "closed_stages": closed_stages,
            "page_name": "ticket",
            "ticket": ticket,
            "user": request.env.user,
        }

        return self._get_page_view_values(
            ticket, access_token, values, "my_tickets_history", False, **kwargs
        )
