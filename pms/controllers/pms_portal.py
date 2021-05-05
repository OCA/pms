import re

from odoo import _, fields, http, tools
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

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
        return self._get_page_view_values(
            folio, access_token, values, "my_folios_history", False, **kwargs
        )

    @http.route(
        ["/my/folios", "/my/folios/page/<int:page>"],
        type="http",
        auth="user",
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

    @http.route(["/my/folios/<int:folio_id>"], type="http", auth="user", website=True)
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
        ["/my/folios/<int:folio_id>/precheckin"], type="http", auth="user", website=True
    )
    def portal_my_folio_precheckin(
        self, folio_id, access_token=None, report_type=None, download=False, **kw
    ):
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "error": {},
                "error_message": [],
            }
        )
        try:
            folio_sudo = self._document_check_access(
                "pms.folio",
                folio_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values.update(self._folio_get_page_view_values(folio_sudo, access_token, **kw))
        values.update({"no_breadcrumbs": True})
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
        auth="user",
        website=True,
    )
    def portal_my_reservations(
        self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw
    ):
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
        auth="user",
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
        # for attachment in reservation_sudo.attachment_ids:
        #     attachment.generate_access_token()
        values = self._reservation_get_page_view_values(
            reservation_sudo, access_token, **kw
        )
        return request.render("pms.portal_my_reservation_detail", values)

    @http.route(
        ["/my/reservations/<int:reservation_id>/precheckin"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_reservation_precheckin(
        self, reservation_id, access_token=None, report_type=None, download=False, **kw
    ):
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
        values.update({"no_breadcrumbs": True})
        return request.render("pms.portal_my_reservation_precheckin", values)


class PortalPrecheckin(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        partner = request.env.user.partner_id
        values = super()._prepare_home_portal_values(counters)
        Reservation = request.env["pms.reservation"].search(
            [("partner_id", "=", partner.id)]
        )
        if "checkin_count" in counters:
            checkin_partner_count = len(Reservation.checkin_partner_ids)
            values["checkin_count"] = (
                checkin_partner_count
                if Reservation.check_access_rights("read", raise_exception=False)
                else 0
            )
        return values

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
        auth="user",
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
        values.update({"no_breadcrumbs": True})
        return request.render("pms.portal_my_precheckin_detail", values)

    @http.route(["/my/precheckin"], type="http", auth="user", website=True, csrf=False)
    def portal_precheckin_submit(self, access_token=None, **kw):

        values = dict()
        values.update(
            {
                "error": {},
                "error_message": [],
            }
        )
        if kw:
            error, error_message = self.form_validate(kw)
            values.update(
                {
                    "error": error,
                    "error_message": error_message,
                }
            )
            if not error:
                values = kw
                checkin_partner = request.env["pms.checkin.partner"].browse(
                    int(kw.get("id"))
                )
                if not values.get("birthdate_date"):
                    values.update({"birthdate_date": False})
                if not values.get("document_expedition_date"):
                    values.update({"document_expedition_date": False})
                lastname = True if values.get("lastname") else False
                firstname = True if values.get("firstname") else False
                lastname2 = True if values.get("lastname2") else False
                if not checkin_partner.partner_id and (
                    lastname or firstname or lastname2
                ):
                    ResPartner = request.env["res.partner"]
                    res_partner = ResPartner.create(values)
                    values.update(
                        {
                            "partner_id": res_partner.id,
                        }
                    )
                elif checkin_partner.partner_id:
                    res_partner = checkin_partner.partner_id
                    res_partner.write(values)
                checkin_partner.write(values)
                values1 = dict()
                values1.update(
                    {
                        "success": True,
                        "checkin_partner": checkin_partner,
                        "no_breadcrumbs": True,
                    }
                )
                return request.render("pms.portal_my_precheckin_detail", values1)
        try:
            checkin_partner = request.env["pms.checkin.partner"].browse(
                int(kw.get("id"))
            )
            values.update(
                {
                    "checkin_partner": checkin_partner,
                    "no_breadcrumbs": True,
                }
            )
            return request.render("pms.portal_my_precheckin_detail", values)
        except (AccessError, MissingError):
            return request.redirect("/my")

    @http.route(
        ["/my/precheckin/folio_reservation"],
        type="http",
        auth="user",
        website=False,
        csrf=True,
    )
    def portal_precheckin_folio_submit(self, **kw):
        counter = 1
        checkin_partners = False
        if kw.get("folio_id"):
            folio = request.env["pms.folio"].browse(int(kw.get("folio_id")))
            checkin_partners = folio.checkin_partner_ids
        elif kw.get("reservation_id"):
            reservation = request.env["pms.reservation"].browse(
                int(kw.get("reservation_id"))
            )
            checkin_partners = reservation.checkin_partner_ids
        for checkin in checkin_partners:
            values = {
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
            }
            lastname = True if kw.get("lastname-" + str(counter)) else False
            firstname = True if kw.get("firstname-" + str(counter)) else False
            lastname2 = True if kw.get("lastname2-" + str(counter)) else False
            if not checkin.partner_id and (lastname or firstname or lastname2):
                ResPartner = request.env["res.partner"]
                res_partner = ResPartner.create(values)
                values.update(
                    {
                        "partner_id": res_partner.id,
                    }
                )
            elif checkin.partner_id:
                res_partner = checkin.partner_id
                res_partner.write(values)
            checkin.write(values)
            counter = counter + 1

    def form_validate(self, data):
        error = dict()
        error_message = []
        if data["document_number"]:
            if data["document_type"] == "D":
                if not re.match(r"^\d{8}[ -]?[a-zA-Z]$", data["document_number"]):
                    error["document_number"] = "error"
                    error_message.append("The DNI format is wrong")
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
                dni_number = data["document_number"][0:8]
                dni_letter = data["document_number"][
                    len(data["document_number"]) - 1 : len(data["document_number"])
                ]
                if letters.get(int(dni_number) % 23) != dni_letter:
                    error["document_number"] = "error"
                    error_message.append("DNI is invalid")

            if data["document_type"] == "C" and not re.match(
                r"^\d{8}[ -]?[a-zA-Z]$", data["document_number"]
            ):
                error["document_number"] = "error"
                error_message.append("The Driving License format is wrong")
            if data["document_type"] == "N" and not re.match(
                r"^[X|Y]{1}[ -]?\d{7,8}[ -]?[a-zA-Z]$", data["document_number"]
            ):
                error["document_number"] = "error"
                error_message.append("The Spanish Residence Permit format is wrong")
            if data["document_type"] == "X" and not re.match(
                r"^[X|Y]{1}[ -]?\d{7,8}[ -]?[a-zA-Z]$", data["document_number"]
            ):
                error["document_number"] = "error"
                error_message.append("The European Residence Permit format is wrong")

        if data["birthdate_date"] and data["birthdate_date"] > str(
            fields.Datetime.today()
        ):
            error["birthdate_date"] = "error"
            error_message.append("Birthdate must be less than today")
        if data["document_expedition_date"] and data["document_expedition_date"] > str(
            fields.Datetime.today()
        ):
            error["document_expedition_date"] = "error"
            error_message.append("Expedition Date must be less than today")

        if data["email"] and not tools.single_email_re.match(data["email"]):
            error["email"] = "error"
            error_message.append("Email format is wrong")

        return error, error_message
