from odoo import _, http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


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
            request.env["payment.provider"]
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
        backend_url = (
            f"/web#model={folio_sudo._name}"
            f"&id={folio_sudo.id}"
            f"&action={folio_sudo._get_portal_return_action().id}"
            f"&view_type=form"
        )
        values = {
            "folio": folio_sudo,
            "message": "",
            "report_type": "html",
            "backend_url": backend_url,
            "res_company": folio_sudo.company_id,
        }
        values = self._get_page_view_values(
            folio_sudo, access_token, values, "my_folios_history", False, **kw
        )
        if "custom_amount" in kw:
            values["custom_amount"] = float(kw["custom_amount"])
        return request.render("pms.folio_portal_template", values)


class PaymentPortal(payment_portal.PaymentPortal):
    @http.route("/my/folios/<int:folio_id>/transaction", type="json", auth="public")
    def portal_folio_transaction(self, pms_folio_id, access_token, **kwargs):
        """Create a draft transaction and return its processing values.

        :param int pms_folio_id: The folio to pay, as a `pms.folio` id
        :param str access_token: The access token used to authenticate the request
        :param dict kwargs: Locally unused data passed to `_create_transaction`
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if the invoice id or the access token is invalid
        """
        # Check the order id and the access token
        try:
            folio_sudo = self._document_check_access(
                "pms.folio", pms_folio_id, access_token
            )
        except MissingError as error:
            raise error
        except AccessError as error:
            raise ValidationError(_("The access token is invalid.")) from error

        kwargs.update(
            {
                "reference_prefix": None,
                # Allow the reference to be computed based on the order
                "partner_id": (
                    folio_sudo.partner_id.id
                    if folio_sudo.partner_id
                    else self.env.ref("pms.various_pms_partner").id
                ),
                "pms_folio_id": pms_folio_id,
                # Include the Folio to allow Subscriptions tokenizing the tx
            }
        )
        kwargs.pop(
            "custom_create_values", None
        )  # Don't allow passing arbitrary create values
        tx_sudo = self._create_transaction(
            custom_create_values={"folio_ids": [Command.set([pms_folio_id])]},
            **kwargs,
        )

        return tx_sudo._get_processing_values()

    # Payment overrides

    @http.route()
    def payment_pay(
        self, *args, amount=None, pms_folio_id=None, access_token=None, **kwargs
    ):
        """Override of payment to replace the missing transaction values
        by that of the folio.

        This is necessary for the reconciliation as all transaction values,
        excepted the amount, need to match exactly that of the folio.

        :param str amount: The (possibly partial) amount to pay used
        to check the access token
        :param str pms_folio_id: The folio for which a payment id made,
        as a `pms.folio` id
        :param str access_token: The access token used to authenticate the partner
        :return: The result of the parent method
        :rtype: str
        :raise: ValidationError if the order id is invalid
        """
        # Cast numeric parameters as int or float and void them if their
        # str value is malformed
        amount = self._cast_as_float(amount)
        pms_folio_id = self._cast_as_int(pms_folio_id)
        if pms_folio_id:
            folio_sudo = request.env["pms.folio"].sudo().browse(pms_folio_id).exists()
            if not folio_sudo:
                raise ValidationError(_("The provided parameters are invalid."))

            # Check the access token against the order values.
            # Done after fetching the order as we
            # need the order fields to check the access token.
            if not payment_utils.check_access_token(
                access_token,
                (
                    folio_sudo.partner_id.id
                    if folio_sudo.partner_id
                    else request.env.ref("pms.various_pms_partner").id
                ),
                amount,
                folio_sudo.currency_id.id,
            ):
                raise ValidationError(_("The provided parameters are invalid."))

            kwargs.update(
                {
                    "currency_id": folio_sudo.currency_id.id,
                    "partner_id": (
                        folio_sudo.partner_id.id
                        if folio_sudo.partner_id
                        else request.env.ref("pms.various_pms_partner").id
                    ),
                    "company_id": folio_sudo.company_id.id,
                    "pms_folio_id": pms_folio_id,
                }
            )
        return super().payment_pay(
            *args, amount=amount, access_token=access_token, **kwargs
        )

    def _get_custom_rendering_context_values(self, pms_folio_id=None, **kwargs):
        """Override of payment to add the sale order id in the custom
        rendering context values.

        :param int sale_order_id: The sale order for which a payment
        id made, as a `sale.order` id
        :return: The extended rendering context values
        :rtype: dict
        """
        rendering_context_values = super()._get_custom_rendering_context_values(
            pms_folio_id=pms_folio_id, **kwargs
        )
        if pms_folio_id:
            rendering_context_values["pms_folio_id"] = pms_folio_id

        return rendering_context_values

    def _create_transaction(
        self, *args, pms_folio_id=None, custom_create_values=None, **kwargs
    ):
        """Override of payment to add the sale order id in the custom create values.

        :param int sale_order_id: The sale order for which a payment id made,
        as a `sale.order` id
        :param dict custom_create_values: Additional create values overwriting
        the default ones
        :return: The result of the parent method
        :rtype: recordset of `payment.transaction`
        """
        if pms_folio_id:
            if custom_create_values is None:
                custom_create_values = {}
            # As this override is also called if the flow is initiated
            # from sale or website_sale, we
            # need not to override whatever value these modules could have already set
            if (
                "folio_ids" not in custom_create_values
            ):  # We are in the payment module's flow
                custom_create_values["folio_ids"] = [Command.set([int(pms_folio_id)])]
        return super()._create_transaction(
            *args,
            pms_folio_id=pms_folio_id,
            custom_create_values=custom_create_values,
            **kwargs,
        )


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
            **kwargs,
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
        values = super()._invoice_get_page_view_values(invoice, access_token, **kwargs)
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
