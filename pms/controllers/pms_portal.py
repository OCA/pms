from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.portal.models.portal_mixin import PortalMixin


class PortalFolio(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        partner = request.env.user.partner_id
        values = super()._prepare_home_portal_values(counters)
        Folio = request.env["pms.folio"]
        if "folio_count" in counters:
            values["folio_count"] = (
                Folio.search_count(
                    [
                        ("partner_id", "=", partner.id),
                    ]
                )
                if Folio.check_access_rights("read", raise_exception=False)
                else 0
            )
        return values

    def _folio_get_page_view_values(self, folio, access_token, **kwargs):
        values = {"folio": folio, "token": access_token}
        payment_inputs = (
            request.env["payment.acquirer"]
            .sudo()
            ._get_available_payment_input(
                partner=folio.partner_id, company=folio.company_id
            )
        )
        acquirers = payment_inputs.get("acquirers")
        for acquirer in acquirers:
            if (
                acquirer.pms_property_ids
                and folio.pms_property_id.id not in acquirer.pms_property_ids.ids
            ):
                payment_inputs["acquirers"] -= acquirer
        values.update(payment_inputs)
        is_public_user = request.env.user._is_public()
        if is_public_user:
            payment_inputs.pop("pms", None)
            token_count = (
                request.env["payment.token"]
                .sudo()
                .search_count(
                    [
                        ("acquirer_id.company_id", "=", folio.company_id.id),
                        ("partner_id", "=", folio.partner_id.id),
                        "|",
                        (
                            "acquirer_id.pms_property_ids",
                            "in",
                            folio.pms_property_id.id,
                        ),
                        ("acquirer_id.pms_property_ids", "=", False),
                    ]
                )
            )
            values["existing_token"] = token_count > 0
        values.update(payment_inputs)
        values["partner_id"] = (
            folio.partner_id if is_public_user else request.env.user.partner_id,
        )
        return self._get_page_view_values(
            folio, access_token, values, "my_folios_history", False, **kwargs
        )

    @http.route(
        "/folio/pay/<int:folio_id>/form_tx", type="json", auth="public", website=True
    )
    def folio_pay_form(
        self, acquirer_id, folio_id, save_token=False, access_token=None, **kwargs
    ):
        folio_sudo = request.env["pms.folio"].sudo().browse(folio_id)
        if not folio_sudo:
            return False

        try:
            acquirer_id = int(acquirer_id)
        except Exception:
            return False

        if request.env.user._is_public():
            save_token = False  # we avoid to create a token for the public user

        success_url = kwargs.get(
            "success_url",
            "%s?%s" % (folio_sudo.access_url, access_token if access_token else ""),
        )
        custom_amount = False
        if "custom_amount" in kwargs:
            custom_amount = float(kwargs["custom_amount"])

        vals = {
            "acquirer_id": acquirer_id,
            "return_url": success_url,
        }

        if save_token:
            vals["type"] = "form_save"
        transaction = folio_sudo._create_payment_transaction(vals)
        PaymentProcessing.add_payment_transaction(transaction)
        if not transaction:
            return False
        tx_ids_list = set(request.session.get("__payment_tx_ids__", [])) | set(
            transaction.ids
        )
        request.session["__payment_tx_ids__"] = list(tx_ids_list)
        return transaction.render_folio_button(
            folio_sudo,
            submit_txt=_("Pay & Confirm"),
            render_values={
                "type": "form_save" if save_token else "form",
                "alias_usage": _(
                    "If we store your payment information on our server, "
                    "subscription payments will be made automatically."
                ),
            },
            amount=custom_amount,
        )

    @http.route(
        ["/my/folios", "/my/folios/page/<int:page>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_folios(
        self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw
    ):
        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        PmsFolio = request.env["pms.folio"]
        values["folios"] = PmsFolio.search(
            [
                ("partner_id", "child_of", partner.id),
            ]
        )
        domain = [
            ("partner_id", "child_of", partner.id),
        ]
        searchbar_sortings = {
            "date": {"label": _("Order Date"), "folio": "date_order desc"},
            "name": {"label": _("Reference"), "folio": "name"},
            "stage": {"label": _("Stage"), "folio": "state"},
        }
        if not sortby:
            sortby = "date"
        sort_order = searchbar_sortings[sortby]["folio"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]
        folio_count = PmsFolio.search_count(domain)
        pager = portal_pager(
            url="/my/folios",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=folio_count,
            page=page,
            step=self._items_per_page,
        )
        folios = PmsFolio.search(
            domain, order=sort_order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_folios_history"] = folios.ids[:100]
        values.update(
            {
                "date": date_begin,
                "folios": folios.sudo(),
                "page_name": "folios",
                "pager": pager,
                "default_url": "/my/folios",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("pms.portal_my_folio", values)

    @http.route(["/my/folios/<int:folio_id>"], type="http", auth="public", website=True)
    def portal_my_folio_detail(
        self, folio_id, access_token=None, report_type=None, download=False, **kw
    ):
        try:
            folio_sudo = self._document_check_access(
                "pms.folio",
                folio_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=folio_sudo,
                report_type=report_type,
                report_ref="pms.action_report_folio",
                download=download,
            )
        values = self._folio_get_page_view_values(folio_sudo, access_token, **kw)
        if "custom_amount" in kw:
            values["custom_amount"] = float(kw["custom_amount"])
        return request.render("pms.folio_portal_template", values)


class PortalReservation(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        partner = request.env.user.partner_id
        values = super()._prepare_home_portal_values(counters)
        Reservation = request.env["pms.reservation"]
        if "reservation_count" in counters:
            values["reservation_count"] = (
                Reservation.search_count(
                    [
                        ("partner_id", "=", partner.id),
                    ]
                )
                if Reservation.check_access_rights("read", raise_exception=False)
                else 0
            )
        return values

    def _reservation_get_page_view_values(self, reservation, access_token, **kwargs):
        values = {"reservation": reservation, "token": access_token}
        return self._get_page_view_values(
            reservation,
            access_token,
            values,
            "my_reservations_history",
            False,
            **kwargs
        )

    @http.route(
        ["/my/reservations", "/my/reservations/page/<int:page>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_reservations(self, page=1, date_begin=None, date_end=None):
        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        Reservation = request.env["pms.reservation"]
        values["reservations"] = Reservation.search(
            [
                ("partner_id", "child_of", partner.id),
            ]
        )
        domain = [
            ("partner_id", "child_of", partner.id),
        ]
        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]
        reservation_count = Reservation.search_count(domain)
        pager = portal_pager(
            url="/my/reservations",
            url_args={"date_begin": date_begin, "date_end": date_end},
            total=reservation_count,
            page=page,
            step=self._items_per_page,
        )
        reservations = Reservation.search(
            domain, limit=self._items_per_page, offset=pager["offset"]
        )
        folios_dict = {}
        for reservation in reservations:
            folio = reservation.folio_id
            folios_dict[folio] = ""

        request.session["my_reservations_history"] = reservations.ids[:100]
        values.update(
            {
                "date": date_begin,
                "reservations": reservations.sudo(),
                "page_name": "reservations",
                "pager": pager,
                "default_url": "/my/reservations",
                "folios_dict": folios_dict,
                "partner": partner,
            }
        )
        return request.render("pms.portal_my_reservation", values)

    @http.route(
        ["/my/reservations/<int:reservation_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_reservation_detail(self, reservation_id, access_token=None, **kw):
        try:
            reservation_sudo = self._document_check_access(
                "pms.reservation",
                reservation_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._reservation_get_page_view_values(
            reservation_sudo, access_token, **kw
        )
        return request.render("pms.portal_my_reservation_detail", values)


class PortalPrecheckin(CustomerPortal):
    def _precheckin_get_page_view_values(
        self, checkin_partner_id, access_token, **kwargs
    ):
        checkin_partner = request.env["pms.checkin.partner"].browse(checkin_partner_id)
        values = {"checkin_partner_id": checkin_partner, "token": access_token}
        return self._get_page_view_values(
            checkin_partner,
            access_token,
            values,
            "my_precheckins_history",
            False,
            **kwargs
        )

    @http.route(
        ["/my/folios/<int:folio_id>/precheckin"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_precheckin(
        self,
        folio_id,
        access_token=None,
    ):
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        values = self._prepare_portal_layout_values()
        try:
            folio_sudo = self._document_check_access(
                "pms.folio",
                folio_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.render("pms.portal_not_checkin", values)
        available_checkins = folio_sudo.checkin_partner_ids.filtered(
            lambda c: c.state in ["dummy", "draft"]
        )
        checkin_partner = (
            available_checkins[0]
            if available_checkins
            else folio_sudo.checkin_partner_ids[0]
        )
        values.update(
            {
                "error": {},
                "country_ids": country_ids,
                "state_ids": state_ids,
                "doc_type_ids": doc_type_ids,
                "folio": folio_sudo,
                "checkin_partner_id": checkin_partner,
            }
        )
        if checkin_partner.state not in ["dummy", "draft"]:
            return request.render("pms.portal_not_checkin", values)
        return request.render("pms.portal_my_reservation_precheckin", values)

    @http.route(
        ["/my/folios/<int:folio_id>/reservations"],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_precheckin_folio(self, folio_id, access_token=None, **kw):
        values = self._prepare_portal_layout_values()
        try:
            folio_sudo = self._document_check_access(
                "pms.folio",
                folio_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values.update({"no_breadcrumbs": True, "folio": folio_sudo})
        return request.render("pms.portal_my_prechekin_folio", values)

    @http.route(
        ["/my/folios/<int:folio_id>/reservations/<int:reservation_id>/checkins"],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_precheckin_reservation(
        self, folio_id, reservation_id, access_token=None, **kw
    ):
        folio = request.env["pms.folio"].sudo().browse(folio_id)
        reservation = request.env["pms.reservation"].sudo().browse(reservation_id)
        values = {}
        values.update({"folio": folio})
        values.update(
            {
                "no_breadcrumbs": True,
                "folio_access_token": access_token,
                "reservation": reservation,
            }
        )
        return request.render("pms.portal_my_prechekin_reservation", values)

    @http.route(
        [
            "/my/folios/<int:folio_id>"
            "/reservations/<int:reservation_id>"
            "/checkins/<int:checkin_partner_id>"
        ],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_precheckin(
        self, folio_id, reservation_id, checkin_partner_id, access_token=None, **kw
    ):
        folio = request.env["pms.folio"].sudo().browse(folio_id)
        reservation = request.env["pms.reservation"].sudo().browse(reservation_id)
        try:
            checkin_sudo = self._document_check_access(
                "pms.checkin.partner",
                checkin_partner_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.render("pms.portal_not_checkin", kw)
        values = {}
        zip_ids = request.env["res.city.zip"].search([])
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        city_ids = request.env["res.city"].search([])
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        access_token = checkin_sudo.access_token
        if not checkin_sudo.access_token:
            access_token = PortalMixin._portal_ensure_token(checkin_sudo)
        values.update(
            self._precheckin_get_page_view_values(checkin_sudo.id, access_token)
        )
        values.update(
            {
                "folio_access_token": kw.get("folio_access_token"),
                "no_breadcrumbs": True,
                "folio": folio,
                "reservation": reservation,
                "checkin_partner": checkin_sudo,
                "zip_ids": zip_ids,
                "country_ids": country_ids,
                "state_ids": state_ids,
                "city_ids": city_ids,
                "doc_type_ids": doc_type_ids,
            }
        )
        if checkin_sudo.state not in ["dummy", "draft"]:
            return request.render("pms.portal_not_checkin", values)

        return request.render("pms.portal_my_precheckin_detail", values)

    @http.route(
        [
            "/my/folios/<int:folio_id>"
            "/reservations/<int:reservation_id>"
            "/checkins/<int:checkin_partner_id>/submit"
        ],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_precheckin_submit(
        self, folio_id, reservation_id, checkin_partner_id, **kw
    ):
        checkin_partner = (
            request.env["pms.checkin.partner"].sudo().browse(checkin_partner_id)
        )

        values = kw
        values.update(
            {
                "checkin_partner": checkin_partner,
            }
        )
        folio_access_token = values.get("folio_access_token")
        request.env["pms.checkin.partner"]._save_data_from_portal(kw)
        folio = request.env["pms.folio"].sudo().browse(folio_id)
        reservation = request.env["pms.reservation"].sudo().browse(reservation_id)
        values.update(
            {
                "no_breadcrumbs": True,
                "folio": folio,
                "reservation": reservation,
            }
        )

        if folio_access_token:
            return request.render("pms.portal_my_prechekin_reservation", values)
        else:
            return request.render("pms.portal_my_precheckin_end", values)

    @http.route(
        ["/my/folios/<int:folio_id>/invitations"],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_precheckin_invitation(self, folio_id, access_token=None, **kw):
        try:
            folio_sudo = self._document_check_access(
                "pms.folio",
                folio_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        web_url = (
            request.env["ir.config_parameter"]
            .sudo()
            .search([("key", "=", "web.base.url")])
        )
        values = self._folio_get_page_view_values(folio_sudo, access_token, **kw)
        values.update({"no_breadcrumbs": True, "error": {}, "web_url": web_url.value})
        return request.render("pms.portal_my_folio_invitations", values)

    @http.route(
        ["/my/precheckin/send_invitation"],
        auth="public",
        type="json",
        website=True,
        csrf=False,
    )
    def portal_precheckin_folio_send_invitation(self, **kw):
        if kw.get("folio_id"):
            folio = request.env["pms.folio"].browse(int(kw.get("folio_id")))
            kw.update({"folio": folio})
        checkin_partner = (
            request.env["pms.checkin.partner"]
            .sudo()
            .browse(int(kw["checkin_partner_id"]))
        )
        firstname = kw["firstname"]
        email = kw["email"]
        if firstname and email:
            checkin_partner.write({"firstname": firstname, "email": email})
            checkin_partner.send_portal_invitation_email(firstname, email)


class PortalAccount(PortalAccount):
    @http.route(
        ["/my/invoices/proforma/<int:invoice_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_proforma_my_invoice_detail(
        self, invoice_id, access_token=None, report_type=None, download=False, **kw
    ):
        try:
            invoice_sudo = self._document_check_access(
                "account.move", invoice_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=invoice_sudo,
                report_type=report_type,
                report_ref="pms.action_report_pms_pro_forma_invoice",
                download=download,
            )

        invoice_sudo = invoice_sudo.with_context(proforma=True)
        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        acquirers = values.get("acquirers")
        if acquirers:
            country_id = (
                values.get("partner_id") and values.get("partner_id")[0].country_id.id
            )
            values["acq_extra_fees"] = acquirers.get_acquirer_extra_fees(
                invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id
            )
        return request.render("pms.pms_proforma_invoice_template", values)

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        """
        Override to add the pms property filter
        """
        values = super(PortalAccount, self)._invoice_get_page_view_values(
            invoice, access_token, **kwargs
        )
        acquirers = values.get("acquirers")
        if acquirers:
            for acquirer in acquirers:
                if (
                    acquirer.pms_property_ids
                    and invoice.pms_property_id.id not in acquirer.pms_property_ids.ids
                ):
                    values["acquirers"] -= acquirer
        payment_tokens = values.get("payment_tokens")
        if payment_tokens:
            for pms in payment_tokens:
                if pms.acquirer_id not in values["acquirers"].ids:
                    values["pms"] -= pms
        return values
