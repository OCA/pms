from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route


class PortalFolio(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        partner = request.env.user.partner_id
        values = super()._prepare_home_portal_values(counters)
        Folio = request.env['pms.folio']
        if 'folio_count' in counters:
            values['folio_count'] = Folio.search_count([
                # ('partner_id', '=', partner.id),
            ]) if Folio.check_access_rights('read', raise_exception=False) else 0
        return values

    @http.route(['/my/folios'], type='http', auth="user", website=True)
    def portal_my_folios(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        values['folios'] = request.env['pms.folio'].sudo().search([])
        return request.render("pms.portal_my_folio", values)

    @http.route(['/my/folios/<int:folio_id>'], type='http', auth="user", website=True)
    def portal_my_folio_detail(self, folio_id, access_token=None, report_type=None, download=False, **kw):
        try:
            folio_sudo = self._document_check_access('pms_folio', folio_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=folio_sudo, report_type=report_type, report_ref='pms.report_folio_document', download=download)
        values = self._invoice_get_page_view_values(folio_sudo, access_token, **kw)
        return request.render("pms.report_folio_document", values)
