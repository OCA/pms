from collections import OrderedDict
from operator import itemgetter

from odoo import _, http
from odoo.http import request
from odoo.osv.expression import AND
from odoo.tools import groupby as groupbyelem

from odoo.addons.helpdesk_mgmt.controllers.myaccount import CustomerPortalHelpdesk


class CustomCustomerPortalHelpdesk(CustomerPortalHelpdesk):
    def _prepare_home_portal_values(self, counters):
        active_property_ids = request.env.user.get_active_property_ids()
        values = super(CustomCustomerPortalHelpdesk, self)._prepare_home_portal_values(
            counters
        )
        helpdesk_model = request.env["helpdesk.ticket"].sudo()
        if "ticket_count" in counters:
            values["ticket_count"] = (
                helpdesk_model.search_count(
                    [
                        ("pms_property_id", "in", active_property_ids),
                    ]
                )
                if helpdesk_model.check_access_rights("read", raise_exception=False)
                else 0
            )
        return values

    @http.route(
        ["/my/tickets", "/my/tickets/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_tickets(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in=None,
        groupby=None,
        **kw
    ):
        response = super(CustomCustomerPortalHelpdesk, self).portal_my_tickets(
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            filterby=filterby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            **kw
        )
        values = response.qcontext

        HelpdeskTicket = request.env["helpdesk.ticket"].sudo()

        active_property_ids = request.env.user.get_active_property_ids()
        property_ids_active_domain = [("pms_property_id", "in", active_property_ids)]

        searchbar_sortings = dict(
            sorted(
                self._ticket_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )

        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        for stage in request.env["helpdesk.ticket.stage"].search([]):
            searchbar_filters[str(stage.id)] = {
                "label": stage.name,
                "domain": [("stage_id", "=", stage.id)],
            }

        searchbar_groupby = self._ticket_get_searchbar_groupby()

        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        if not filterby:
            filterby = "all"
        domain = searchbar_filters.get(filterby, searchbar_filters.get("all"))["domain"]

        if not groupby:
            groupby = "none"

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        if search:
            domain += self._ticket_get_search_domain(search_in, search)

        domain = AND([domain, property_ids_active_domain])
        tickets = HelpdeskTicket.search(domain, order=order)

        request.session["my_tickets_history"] = tickets.ids[:100]

        groupby_mapping = self._ticket_get_groupby_mapping()
        group = groupby_mapping.get(groupby)

        if group:
            grouped_tickets = [
                request.env["helpdesk.ticket"].concat(*g)
                for k, g in groupbyelem(tickets, itemgetter(group))
            ]
        elif tickets:
            grouped_tickets = [tickets]
        else:
            grouped_tickets = []

        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "grouped_tickets": grouped_tickets,
                "page_name": "ticket",
                "default_url": "/my/tickets",
                "searchbar_sortings": searchbar_sortings,
                "searchbar_groupby": searchbar_groupby,
                "searchbar_inputs": self._ticket_get_searchbar_inputs(),
                "search_in": search_in,
                "search": search,
                "sortby": sortby,
                "groupby": groupby,
                "filterby": filterby,
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
            }
        )

        return request.render("pms_helpdesk_mgmt.portal_my_tickets", values)

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
