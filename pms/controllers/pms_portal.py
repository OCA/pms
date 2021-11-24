import re

from odoo import _, fields, http, tools
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


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
        payment_inputs = request.env["payment.acquirer"]._get_available_payment_input(
            partner=folio.partner_id, company=folio.company_id
        )
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
        return request.render("pms.folio_portal_template", values)

    @http.route(
        ["/my/folios/<int:folio_id>/precheckin"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_folio_precheckin(
        self, folio_id, access_token=None, report_type=None, download=False, **kw
    ):
        values = self._prepare_portal_layout_values()
        try:
            folio_sudo = self._document_check_access(
                "pms.folio",
                folio_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values.update(self._folio_get_page_view_values(folio_sudo, access_token, **kw))
        values.update({"no_breadcrumbs": True, "error": {}})
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        values.update(
            {
                "country_ids": country_ids,
                "state_ids": state_ids,
                "doc_type_ids": doc_type_ids,
            }
        )
        return request.render("pms.portal_my_folio_precheckin", values)


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

    @http.route(
        ["/my/reservations/<int:reservation_id>/precheckin"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_reservation_precheckin(self, reservation_id, access_token=None, **kw):
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
        values.update({"no_breadcrumbs": True, "error": {}})
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        values.update(
            {
                "country_ids": country_ids,
                "state_ids": state_ids,
                "doc_type_ids": doc_type_ids,
            }
        )
        return request.render("pms.portal_my_reservation_precheckin", values)


class PortalPrecheckin(CustomerPortal):
    def _precheckin_get_page_view_values(self, checkin_partner, access_token, **kwargs):
        values = {"checkin_partner": checkin_partner, "token": access_token}
        return self._get_page_view_values(
            checkin_partner,
            access_token,
            values,
            "my_precheckins_history",
            False,
            **kwargs
        )

    @http.route(
        ["/my/precheckin/<int:checkin_partner_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_precheckin_detail(self, checkin_partner_id, access_token=None, **kw):
        try:
            checkin_sudo = self._document_check_access(
                "pms.checkin.partner",
                checkin_partner_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._precheckin_get_page_view_values(checkin_sudo, access_token, **kw)
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        values.update(
            {
                "doc_type_ids": doc_type_ids,
                "country_ids": country_ids,
                "state_ids": state_ids,
                "no_breadcrumbs": True,
                "error": {},
            }
        )
        return request.render("pms.portal_my_precheckin_detail", values)

    @http.route(
        ["/my/precheckin"], type="http", auth="public", website=True, csrf=False
    )
    def portal_precheckin_submit(self, **kw):
        values = dict()
        checkin_partner = request.env["pms.checkin.partner"].browse(int(kw.get("id")))
        values.update(
            {
                "checkin_partner": checkin_partner,
                "error": {},
                "error_message": {},
            }
        )
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        if kw:
            error, error_message = self.form_validate(kw, None)
            values.update(
                {
                    "no_breadcrumbs": True,
                    "error": error,
                    "error_message": error_message,
                    "country_ids": country_ids,
                    "state_ids": state_ids,
                    "doc_type_ids": doc_type_ids,
                }
            )
            if error:
                return request.render("pms.portal_my_precheckin_detail", values)
            else:
                try:
                    values = kw
                    if values.get("document_type"):
                        doc_type = (
                            request.env["res.partner.id_category"]
                            .sudo()
                            .search([("name", "=", values.get("document_type"))])
                        )
                        values.update(
                            {
                                "document_type": doc_type.id,
                            }
                        )
                    request.env["pms.checkin.partner"].sudo()._save_data_from_portal(
                        values
                    )
                    doc_type_ids = (
                        request.env["res.partner.id_category"].sudo().search([])
                    )
                    values.update(
                        {
                            "doc_type_ids": doc_type_ids,
                        }
                    )
                    country_ids = request.env["res.country"].search([])
                    state_ids = request.env["res.country.state"].search([])
                    values.update(
                        {
                            "country_ids": country_ids,
                            "state_ids": state_ids,
                        }
                    )
                    values.update(
                        {
                            "success": True,
                            "checkin_partner": checkin_partner,
                            "no_breadcrumbs": True,
                            "error": {},
                        }
                    )
                    return request.render("pms.portal_my_precheckin_detail", values)
                except (AccessError, MissingError):
                    return request.redirect("/my")

    @http.route(
        ["/my/precheckin/folio_reservation"],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_precheckin_folio_submit(self, **kw):
        errors = {}
        e_messages = {}
        counter = 1
        has_error = False
        checkin_partners = False
        if kw.get("folio_id"):
            folio = request.env["pms.folio"].sudo().browse(int(kw.get("folio_id")))
            checkin_partners = folio.checkin_partner_ids
        elif kw.get("reservation_id"):
            reservation = (
                request.env["pms.reservation"]
                .sudo()
                .browse(int(kw.get("reservation_id")))
            )
            checkin_partners = reservation.checkin_partner_ids
        for checkin in checkin_partners:
            values = {
                "id": kw.get("id-" + str(counter)),
                "firstname": kw.get("firstname-" + str(counter)),
                "lastname": kw.get("lastname-" + str(counter)),
                "lastname2": kw.get("lastname2-" + str(counter)),
                "gender": kw.get("gender-" + str(counter)),
                "birthdate_date": kw.get("birthdate_date-" + str(counter))
                if kw.get("birthdate_date-" + str(counter))
                else False,
                "document_type": kw.get("document_type-" + str(counter)),
                "document_number": kw.get("document_number-" + str(counter)),
                "document_expedition_date": kw.get(
                    "document_expedition_date-" + str(counter)
                )
                if kw.get("document_expedition_date-" + str(counter))
                else False,
                "mobile": kw.get("mobile-" + str(counter)),
                "email": kw.get("email-" + str(counter)),
                "nationality_id": kw.get("nationality_id-" + str(counter)),
                "state": kw.get("state-" + str(counter)),
            }

            if values.get("document_type"):
                doc_type_code = values.get("document_type")
                doc_type = (
                    request.env["res.partner.id_category"]
                    .sudo()
                    .search([("name", "=", doc_type_code)])
                )
                values.update(
                    {
                        "document_type": doc_type.id,
                    }
                )
            error, error_message = self.form_validate(kw, counter)
            errors.update(error)
            e_messages.update(error_message)
            if error_message:
                has_error = True
            else:
                checkin.sudo()._save_data_from_portal(values)
            counter = counter + 1
        values = {"no_breadcrumbs": True}
        doc_type_ids = request.env["res.partner.id_category"].sudo().search([])
        country_ids = request.env["res.country"].search([])
        state_ids = request.env["res.country.state"].search([])
        values.update(
            {
                "doc_type_ids": doc_type_ids,
                "country_ids": country_ids,
                "state_ids": state_ids,
            }
        )
        if has_error:
            filtered_dict_error = {k: v for k, v in errors.items() if v}
            filtered_dict_error_messages = {k: v for k, v in e_messages.items() if v}
            values.update(
                {
                    "error": filtered_dict_error,
                    "error_message": filtered_dict_error_messages,
                }
            )
        else:
            values.update({"success": True, "error": {}})
        if kw.get("folio_id"):
            folio = request.env["pms.folio"].sudo().browse(int(kw.get("folio_id")))
            values.update(
                {
                    "folio": folio,
                }
            )
            return request.render("pms.portal_my_folio_precheckin", values)
        elif kw.get("reservation_id"):
            reservation = request.env["pms.reservation"].browse(
                int(kw.get("reservation_id"))
            )
            values.update(
                {
                    "reservation": reservation,
                }
            )
            return request.render("pms.portal_my_reservation_precheckin", values)

    def form_validate(self, data, counter):
        error, error_message = self.form_document_validate(data, counter)
        keys = data.keys()
        mobile = "mobile" if "mobile" in keys else "mobile-" + str(counter)
        if data[mobile]:
            if not re.match(
                r"^(\d{3}[\-\s]?\d{2}[\-\s]?\d{2}[\-\s]?\d{2}[\-\s]?|"
                r"\d{3}[\-\s]?\d{3}[\-\s]?\d{3})$",
                data[mobile],
            ):
                error[mobile] = "error"
                error_message[mobile] = "Invalid phone"
        birthdate_date = (
            "birthdate_date"
            if "birthdate_date" in keys
            else "birthdate_date-" + str(counter)
        )
        if data[birthdate_date] and data[birthdate_date] > str(fields.Datetime.today()):
            error[birthdate_date] = "error"
            error_message[birthdate_date] = "Birthdate must be less than today"
        email = "email" if "email" in keys else "email-" + str(counter)
        if data[email] and not tools.single_email_re.match(data[email]):
            error[email] = "error"
            error_message[email] = "Email format is wrong"
        firstname = "firstname" if "firstname" in keys else "firstname-" + str(counter)
        lastname = "lastname" if "lastname" in keys else "lastname-" + str(counter)
        lastname2 = "lastname2" if "lastname2" in keys else "lastname2-" + str(counter)
        if not data[firstname] and not data[lastname] and not data[lastname2]:
            error[firstname] = "error"
            error_message[firstname] = "Firstname or any lastname are not included"
        return error, error_message

    def form_document_validate(self, data, counter):
        error = dict()
        error_message = {}
        keys = data.keys()
        document_number = (
            "document_number"
            if "document_number" in keys
            else "document_number-" + str(counter)
        )
        document_type = (
            "document_type"
            if "document_type" in keys
            else "document_type-" + str(counter)
        )
        document_expedition_date = (
            "document_expedition_date"
            if "document_expedition_date" in keys
            else "document_expedition_date-" + str(counter)
        )
        if data[document_expedition_date] and not data[document_number]:
            error[document_expedition_date] = "error"
            error_message[
                document_expedition_date
            ] = "Document Number not entered and Document Type is not selected"
        if data[document_number]:
            if not data[document_type]:
                error[document_type] = "error"
                error_message[document_type] = "Document Type is not selected"
            if data[document_type] == "D":
                if len(data[document_number]) == 9 or len(data[document_number]) == 10:
                    if not re.match(r"^\d{8}[ -]?[a-zA-Z]$", data[document_number]):
                        error[document_number] = "error"
                        error_message[document_number] = "The DNI format is wrong"
                    letters = {
                        0: "T",
                        1: "R",
                        2: "W",
                        3: "A",
                        4: "G",
                        5: "M",
                        6: "Y",
                        7: "F",
                        8: "P",
                        9: "D",
                        10: "X",
                        11: "B",
                        12: "N",
                        13: "J",
                        14: "Z",
                        15: "S",
                        16: "Q",
                        17: "V",
                        18: "H",
                        19: "L",
                        20: "C",
                        21: "K",
                        22: "E",
                    }
                    dni_number = data[document_number][0:8]
                    dni_letter = data[document_number][
                        len(data[document_number]) - 1 : len(data[document_number])
                    ]
                    if letters.get(int(dni_number) % 23) != dni_letter.upper():
                        error[document_number] = "error"
                        error_message[document_number] = "DNI format is invalid"
                else:
                    error[document_number] = "error"
                    error_message[document_number] = "DNI is invalid"
            if data[document_type] == "C" and not re.match(
                r"^\d{8}[ -]?[a-zA-Z]$", data[document_number]
            ):
                error[document_number] = "error"
                error_message[document_number] = "The Driving License format is wrong"
            if data[document_type] == "N" and not re.match(
                r"^[X|Y]{1}[ -]?\d{7,8}[ -]?[a-zA-Z]$", data[document_number]
            ):
                error[document_number] = "error"
                error_message[
                    document_number
                ] = "The Spanish Residence Permit format is wrong"
            if data[document_type] == "X" and not re.match(
                r"^[X|Y]{1}[ -]?\d{7,8}[ -]?[a-zA-Z]$", data[document_number]
            ):
                error[document_number] = "error"
                error_message[
                    document_number
                ] = "The European Residence Permit format is wrong"
        elif data[document_type]:
            error[document_number] = "error"
            error_message[document_number] = "Document Number not entered"
        return error, error_message

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
