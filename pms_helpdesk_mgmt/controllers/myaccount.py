from odoo.http import request
from odoo.addons.helpdesk_mgmt.controllers.myaccount import CustomerPortalHelpdesk
from odoo.osv.expression import AND, OR
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from collections import OrderedDict
from operator import itemgetter
from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.tools import groupby as groupbyelem


class CustomCustomerPortalHelpdesk(CustomerPortalHelpdesk):
    @http.route(
        ["/my/tickets", "/my/tickets/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_tickets(self, **kw):
        response = super(CustomCustomerPortalHelpdesk, self).portal_my_tickets(**kw)
        page = response.qcontext.get('page', 1)
        HelpdeskTicket = request.env["helpdesk.ticket"].sudo() 
        
        # Llamamos al método del padre para obtener los valores de la vista
        values = super(CustomCustomerPortalHelpdesk, self)._prepare_portal_layout_values()
        if not HelpdeskTicket.check_access_rights("read", raise_exception=False):
            return request.redirect("/my")

        domain = response.qcontext.get('domain', [])
        order = response.qcontext.get('order', '')
        sortby = response.qcontext.get('sortby', {})
        groupby = response.qcontext.get('groupby', '')
        
        active_property_ids = request.env.user.get_active_property_ids() 
        if active_property_ids:
            domain.append(("pms_property_id", "in", active_property_ids))
        
        HelpdeskTicket = request.env["helpdesk.ticket"].sudo() 
        ticket_count = HelpdeskTicket.search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={
                "date_begin": response.qcontext.get('date_begin', {}),
                "date_end": response.qcontext.get('date_end', {}),
                "sortby": sortby,
                "filterby": response.qcontext.get('filterby', ''),
                "groupby": groupby,
                "search": response.qcontext.get('search', ''),
                "search_in": response.qcontext.get('search_in', ''),
            },
            total=ticket_count,
            page=page,
            step=self._items_per_page,
        )
        tickets = HelpdeskTicket.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        request.session["my_tickets_history"] = tickets.ids[:100]

        group = response.qcontext.get('group', None)
        grouped_tickets = [tickets] if not group else [
            request.env["helpdesk.ticket"].concat(*g)
            for k, g in groupbyelem(tickets, itemgetter(group))
        ]
        values.update(
            {
                "date": response.qcontext.get('date_begin', {}),
                "date_end": response.qcontext.get('date_end', {}),
                "grouped_tickets": grouped_tickets,
                "page_name": "ticket",
                "default_url": "/my/tickets",
                "pager": pager,
                "searchbar_sortings": response.qcontext.get('searchbar_sortings', []),
                "searchbar_groupby": response.qcontext.get('searchbar_groupby', []),
                "searchbar_inputs": response.qcontext.get('searchbar_inputs', []),
                "search_in": response.qcontext.get('search_in', ''),
                "search": response.qcontext.get('search', ''),
                "sortby": sortby,
                "groupby": groupby,
                "searchbar_filters": OrderedDict(sorted(response.qcontext.get('searchbar_filters', {}).items())),
                "filterby": response.qcontext.get('filterby', ''),
            }
        )
        return request.render("helpdesk_mgmt.portal_my_tickets", values)


