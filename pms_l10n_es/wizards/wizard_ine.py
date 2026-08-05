import base64
import calendar
import datetime
import math
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# TODO: Review code (code iso ?)
CODE_SPAIN = "ES"

# The INE replaced the ARCE platform with IRIA. Two variants of each survey
# schema coexist: the one published by the INE, which declares no target
# namespace and is the reference one, and the one the IRIA application
# generates for the questionnaire, which is namespace-qualified. The INE
# confirmed that the published schema is the one to follow, and both variants
# have been accepted on upload (the hotel file without namespace and the
# apartments file with it). Files are therefore built after the published
# schema, and the namespace can be set per survey through a config parameter
# for the questionnaires that require the qualified variant.
INE_XML_NAMESPACE_PARAMS = {
    "hotel": ("pms_l10n_es.ine_xml_namespace_hotel", ""),
    "apartments": ("pms_l10n_es.ine_xml_namespace_apartments", ""),
}

INE_APARTMENT_TYPES = ["studio", "apt_2_4", "apt_4_6", "other"]
INE_APARTMENT_XML_SUFFIXES = {
    "studio": "ESTUDIO",
    "apt_2_4": "2-4pax",
    "apt_4_6": "4-6pax",
    "other": "OTROS",
}
INE_APARTMENT_PRICE_TAGS = {
    "studio": "ESTUDIOS",
    "apt_2_4": "APARTAMENTOS_2-4pax",
    "apt_4_6": "APARTAMENTOS_4-6pax",
    "other": "OTROS",
}


class WizardIne(models.TransientModel):
    _name = "pms.ine.wizard"
    _description = "Wizard to generate statistical info."

    pms_property_id = fields.Many2one(
        string="Property",
        comodel_name="pms.property",
        check_pms_properties=True,
        required=True,
    )

    txt_filename = fields.Text()
    txt_binary = fields.Binary(string="File Download")
    txt_message = fields.Char(string="File Preview")

    start_date = fields.Date(
        string="From",
        required=True,
    )
    end_date = fields.Date(
        string="To",
        required=True,
    )

    adr = fields.Float(string="Range ADR")
    revpar = fields.Float(string="Range RevPAR")

    @api.model
    def _ine_get_extra_beds(self, pms_property_id, date):
        """Extra beds occupied on a given date (INE criteria).

        Children occupying an extra bed are excluded because they have no
        check-in partner data.
        """
        extra_beds = 0
        extra_bed_service_lines = self.env["pms.service.line"].search(
            [
                ("pms_property_id", "=", pms_property_id.id),
                ("product_id.is_extra_bed", "=", True),
                ("reservation_id.reservation_type", "=", "normal"),
                ("reservation_id.state", "in", ["confirmed", "onboard", "done"]),
                ("date", "=", date),
            ]
        )
        for ebsl in extra_bed_service_lines:
            reservation_lines = ebsl.reservation_id.reservation_line_ids.filtered(
                lambda x, ebsl=ebsl: x.date == ebsl.date
                and x.room_id.in_ine
                and x.occupies_availability
            )
            if reservation_lines:
                extra_beds += (
                    ebsl.day_qty - reservation_lines.reservation_id.children_occupying
                )
        return extra_beds

    @api.model
    def ine_rooms(self, start_date, end_date, pms_property_id):
        """
        Returns a dictionary:
        {
            date_1: {
                'double_rooms_single_use': number,
                'double_rooms_double_use': number,
                'other_rooms': number,
                'extra_beds': number
            },
            # ... more dates
        }
        """
        # result object
        rooms = dict()

        # iterate days between start_date and end_date
        for p_date in [
            start_date + datetime.timedelta(days=x)
            for x in range(0, (end_date - start_date).days + 1)
        ]:
            # rooms with capacity 2 but only 1 adult using them
            double_rooms_single_use = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("pms_property_id", "=", pms_property_id.id),
                        ("occupies_availability", "=", True),
                        ("reservation_id.reservation_type", "=", "normal"),
                        ("room_id.in_ine", "=", True),
                        ("date", "=", p_date),
                        ("room_id.capacity", "=", 2),
                        (
                            "reservation_id.state",
                            "in",
                            ["confirmed", "onboard", "done"],
                        ),
                    ]
                )
                .filtered(
                    lambda r: len(
                        r.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state
                            not in ["dummy", "draft", "cancel", "precheckin"]
                        )
                    )
                    == 1
                )
                .mapped("room_id")
            )

            # rooms with capacity 2 with 2 adult using them
            double_rooms_double_use = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("pms_property_id", "=", pms_property_id.id),
                        ("occupies_availability", "=", True),
                        ("reservation_id.reservation_type", "=", "normal"),
                        ("room_id.in_ine", "=", True),
                        ("date", "=", p_date),
                        ("room_id.capacity", "=", 2),
                        (
                            "reservation_id.state",
                            "in",
                            ["confirmed", "onboard", "done"],
                        ),
                    ]
                )
                .filtered(
                    lambda r: len(
                        r.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state
                            not in ["dummy", "draft", "cancel", "precheckin"]
                        )
                    )
                    == 2
                )
                .mapped("room_id")
            )

            extra_beds = self._ine_get_extra_beds(pms_property_id, p_date)

            # search all rooms
            all_rooms = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("date", "=", p_date),
                        ("occupies_availability", "=", True),
                        ("reservation_id.reservation_type", "=", "normal"),
                        ("room_id.in_ine", "=", True),
                        ("pms_property_id", "=", pms_property_id.id),
                        (
                            "reservation_id.state",
                            "in",
                            ["confirmed", "onboard", "done"],
                        ),
                    ]
                )
                .filtered(
                    lambda r: len(
                        r.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state
                            not in ["dummy", "draft", "cancel", "precheckin"]
                        )
                    )
                    > 0
                )
                .mapped("room_id")
            )

            # other rooms = all rooms - double rooms
            other_rooms = (
                all_rooms - double_rooms_double_use
            ) - double_rooms_single_use

            # no room movements -> no dict entrys
            if not (
                extra_beds == 0
                and len(other_rooms) == 0
                and len(double_rooms_double_use) == 0
                and len(double_rooms_single_use) == 0
            ):
                # create result dict for each date
                rooms[p_date] = dict()
                rooms[p_date]["double_rooms_single_use"] = len(double_rooms_single_use)
                rooms[p_date]["double_rooms_double_use"] = len(double_rooms_double_use)
                rooms[p_date]["other_rooms"] = len(other_rooms)
                rooms[p_date]["extra_beds"] = extra_beds
        return rooms

    @api.model
    def ine_countries(self, start_date, end_date, pms_property_id):
        """
        Returns a dictionary:
        {
            CODE_SPAIN: {
                state.code_ine: {
                    date: {
                        'arrivals': number,
                        'departures': number,
                        'pernoctations': number,
                    },
                    # ... more dates
                },
                # ... more ine codes from spain
            },
            # ... more countries (except Spain)
            country.code_alpha3: {
                date: {
                    'arrivals': num. of arrivals
                    'departures': num. of departures
                    'pernoctations': num. of pernoctations
                },
                # ... more dates
            },
            # ... more countries (except Spain)
        }
        """

        def ine_add_arrivals_departures_pernoctations(
            date, type_of_entry, read_group_result
        ):
            """
            date = date to add the entry to dic
            type_of_entry =  'arrivals' | 'departures' | 'pernoctations'
            read_group_result = result of read_group by type_of_entry
            """

            for entry in read_group_result:
                if not entry["country_id"]:
                    guests_with_no_residence_country = self.env[
                        "pms.checkin.partner"
                    ].search(entry["__domain"])
                    guests_with_no_residence_country = (
                        str(guests_with_no_residence_country.mapped("name"))
                        .replace("[", "")
                        .replace("]", "")
                    )
                    raise ValidationError(
                        _(
                            "The following guests have no residence country set :%s.",
                            guests_with_no_residence_country,
                        )
                    )
                # get residence_country_id from group set read_group results
                residence_country_id_code = (
                    self.env["res.country"]
                    .search([("id", "=", entry["country_id"][0])])
                    .code
                )
                # all countries except Spain
                if residence_country_id_code != CODE_SPAIN:
                    # get count of each result
                    num = entry["__count"]

                    # update/create dicts for countries & dates and set num. arrivals
                    if not countries.get(residence_country_id_code):
                        countries[residence_country_id_code] = dict()
                    if not countries[residence_country_id_code].get(date):
                        countries[residence_country_id_code][date] = dict()
                    countries[residence_country_id_code][date][type_of_entry] = num
                else:
                    # arrivals grouped by state_id (Spain "provincias")
                    read_by_arrivals_spain = self.env["pms.checkin.partner"].read_group(
                        entry["__domain"],
                        ["state_id"],
                        ["state_id"],
                        lazy=False,
                    )
                    # iterate read_group results from Spain
                    for entry_from_spain in read_by_arrivals_spain:
                        if not entry_from_spain["state_id"]:
                            spanish_guests_with_no_state = self.env[
                                "pms.checkin.partner"
                            ].search(entry_from_spain["__domain"])
                            spanish_guests_with_no_state = (
                                str(spanish_guests_with_no_state.mapped("name"))
                                .replace("[", "")
                                .replace("]", "")
                            )
                            raise ValidationError(
                                _(
                                    "The following spanish guests have no "
                                    "state set :%s.",
                                    spanish_guests_with_no_state,
                                )
                            )
                        residence_state_id = self.env["res.country.state"].browse(
                            entry_from_spain["state_id"][0]
                        )  # .ine_code
                        ine_code = residence_state_id.ine_code

                        if not ine_code:
                            raise ValidationError(
                                _(
                                    "{state_name} does not have the INE Code configured"
                                ).format(state_name=residence_state_id.name)
                            )
                        # get count of each result
                        num_spain = entry_from_spain["__count"]

                        # update/create dicts for states & dates and set num. arrivals
                        if not countries.get(CODE_SPAIN):
                            countries[CODE_SPAIN] = dict()

                        if not countries[CODE_SPAIN].get(ine_code):
                            countries[CODE_SPAIN][ine_code] = dict()

                        if not countries[CODE_SPAIN][ine_code].get(date):
                            countries[CODE_SPAIN][ine_code][date] = dict()
                        countries[CODE_SPAIN][ine_code][date][type_of_entry] = num_spain

        # result object
        countries = dict()

        # iterate days between start_date and end_date
        for p_date in [
            start_date + datetime.timedelta(days=x)
            for x in range(0, (end_date - start_date).days + 1)
        ]:
            # search for checkin partners
            hosts = self.env["pms.checkin.partner"].search(
                [
                    ("reservation_id.pms_property_id", "=", pms_property_id),
                    ("reservation_id.checkin", "<=", p_date),
                    ("reservation_id.checkout", ">=", p_date),
                    ("reservation_id.reservation_type", "=", "normal"),
                    ("state", "not in", ["dummy", "draft", "cancel", "precheckin"]),
                ]
            )
            hosts = hosts.filtered(
                lambda x: all(
                    x.reservation_id.reservation_line_ids.mapped("room_id.in_ine")
                )
            )

            # arrivals
            arrivals = hosts.filtered(
                lambda x, p_date=p_date: x.reservation_id.checkin == p_date
            )

            # arrivals grouped by country_id
            read_by_arrivals = self.env["pms.checkin.partner"].read_group(
                [("id", "in", arrivals.ids)],
                ["country_id"],
                ["country_id"],
                orderby="country_id",
                lazy=False,
            )

            # departures
            departures = hosts.filtered(
                lambda x, p_date=p_date: x.reservation_id.checkout == p_date
            )

            # departures grouped by country_id
            read_by_departures = self.env["pms.checkin.partner"].read_group(
                [("id", "in", departures.ids)],
                ["country_id"],
                ["country_id"],
                orderby="country_id",
                lazy=False,
            )

            # pernoctations
            pernoctations = hosts - departures

            # pernoctations grouped by country_id
            read_by_pernoctations = self.env["pms.checkin.partner"].read_group(
                [("id", "in", pernoctations.ids)],
                ["country_id"],
                ["country_id"],
                orderby="country_id",
                lazy=False,
            )
            ine_add_arrivals_departures_pernoctations(
                p_date, "arrivals", read_by_arrivals
            )
            ine_add_arrivals_departures_pernoctations(
                p_date, "departures", read_by_departures
            )
            ine_add_arrivals_departures_pernoctations(
                p_date, "pernoctations", read_by_pernoctations
            )

        return countries

    def ine_calculate_adr(self, start_date, end_date, domain=False):
        """
        Calculate date range ADR for a property only in INE rooms
        :param start_date: start date
        :param pms_property_id: pms property id
        :param domain: domain to filter reservations (channel, agencies, etc...)
        """
        self.ensure_one()
        domain = [] if not domain else domain
        domain.append(("room_id.in_ine", "=", True))
        adr = self.pms_property_id._get_adr(start_date, end_date, domain)
        self.adr = adr
        return adr

    def ine_calculate_revpar(self, start_date, end_date, domain=False):
        """
        Calculate date range revpar for a property only in INE rooms
        :param start_date: start date
        :param pms_property_id: pms property id
        :param domain: domain to filter reservations (channel, agencies, etc...)
        """
        self.ensure_one()
        domain = [] if not domain else domain
        domain.append(("room_id.in_ine", "=", True))
        revpar = self.pms_property_id._get_revpar(start_date, end_date, domain)
        self.revpar = revpar
        return revpar

    def ine_calculate_occupancy(self, start_date, end_date, domain=False):
        """
        Calculate date range occupancy for a property only in INE rooms
        :param start_date: start date
        :param pms_property_id: pms property id
        :param domain: domain to filter reservations (channel, agencies, etc...)
        """
        self.ensure_one()
        domain = [] if not domain else domain
        total_domain = [
            ("room_id.in_ine", "=", True),
            ("date", ">=", start_date),
            ("date", "<=", end_date),
        ]
        total_reservations = self.env["pms.reservation.line"].search(total_domain)
        domain.extend(total_domain)
        filter_reservations = self.env["pms.reservation.line"].search(domain)
        if len(filter_reservations) > 0:
            filter_percent = len(filter_reservations) * 100 / len(total_reservations)
            # round to 2 decimals, but if the result is > 0 and < 0.01, return 0.01
            filter_percent = (
                math.ceil(filter_percent * 100) / 100
                if filter_percent < 0.01 and filter_percent > 0
                else round(filter_percent, 2)
            )
        else:
            filter_percent = 0
        return filter_percent

    @api.model
    def ine_get_nif_cif(self, cif_nif):
        country_codes = self.env["res.country"].search([]).mapped("code")
        if cif_nif[:2] in country_codes:
            return cif_nif[2:].strip()
        return cif_nif.strip()

    @api.model
    def check_ine_mandatory_fields(self, pms_property_id):
        if not pms_property_id.name:
            raise ValidationError(_("The property name is not established."))

        if not pms_property_id.company_id.vat:
            raise ValidationError(_("The company VAT is not established."))

        if not pms_property_id.company_id.name:
            raise ValidationError(_("The company name is not established."))

        if not pms_property_id.name:
            raise ValidationError(_("The property name is not established."))

        if not pms_property_id.ine_tourism_number:
            raise ValidationError(_("The property tourism number is not established."))

        if not pms_property_id.ine_tourism_number:
            raise ValidationError(_("The property tourism number is not established."))

        if not pms_property_id.street:
            raise ValidationError(_("The property street is not established."))

        if not pms_property_id.zip:
            raise ValidationError(_("The property zip is not established."))

        if not pms_property_id.city:
            raise ValidationError(_("The property city is not established."))

        if not pms_property_id.partner_id.state_id:
            raise ValidationError(_("The property state is not established."))

        if not pms_property_id.phone:
            raise ValidationError(_("The property phone is not established."))

        if len(pms_property_id.phone.replace(" ", "")) < 9:
            raise ValidationError(
                _(
                    "The property phone '%s' is too short: the INE survey "
                    "requires at least 9 digits.",
                    pms_property_id.phone,
                )
            )

        if not pms_property_id.ine_category_id:
            raise ValidationError(_("The property category is not established."))

        province = (
            pms_property_id.partner_id.state_id.ine_tourism_province_name
            or pms_property_id.partner_id.state_id.name
        )
        if len(province) > 25:
            raise ValidationError(
                _(
                    "The province literal '%s' exceeds the 25 characters "
                    "allowed by the INE survey. Set the 'INE Tourism "
                    "Province Name' field on the property state.",
                    province,
                )
            )

        if pms_property_id.ine_category_id.survey_type == "apartments":
            self._check_ine_apartments_mandatory_fields(pms_property_id)

    @api.model
    def _check_ine_apartments_mandatory_fields(self, pms_property_id):
        if not pms_property_id.ine_informant_name:
            raise ValidationError(_("The INE informant name is not established."))
        if not pms_property_id.ine_informant_job:
            raise ValidationError(
                _("The INE informant job position is not established.")
            )
        if not pms_property_id.ine_informant_email:
            raise ValidationError(_("The INE informant email is not established."))

    def _check_ine_period(self):
        """The INE requires the whole month in the XML file.

        The questionnaire the establishment receives asks for a single week
        (hotels) or fortnight (apartments), but the file must always carry
        every day of the reference month.
        """
        last_day = calendar.monthrange(self.start_date.year, self.start_date.month)[1]
        if self.start_date.day != 1 or self.end_date != self.start_date.replace(
            day=last_day
        ):
            raise ValidationError(
                _(
                    "The INE file must contain the whole reference month, "
                    "regardless of the week or fortnight requested in the "
                    "questionnaire. Select from %(first)s to %(last)s.",
                    first=self.start_date.replace(day=1),
                    last=self.start_date.replace(day=last_day),
                )
            )

    def _ine_get_root_attrs(self, survey_type):
        """Return the root element attributes for the survey.

        The default namespace is only declared when the questionnaire
        requires the namespace-qualified schema variant (see
        INE_XML_NAMESPACE_PARAMS).
        """
        param, default = INE_XML_NAMESPACE_PARAMS[survey_type]
        namespace = self.env["ir.config_parameter"].sudo().get_param(param, default)
        return {"xmlns": namespace} if namespace else {}

    @api.model
    def _ine_format_decimal(self, value):
        """Format decimal values with exactly 2 decimals.

        The INE schemas limit decimal fields to 2 fraction digits: emitting
        raw float representations has historically produced rejected files.
        """
        return "%.2f" % (value or 0)

    def _ine_get_province_name(self):
        state = self.pms_property_id.partner_id.state_id
        return state.ine_tourism_province_name or state.name

    def _ine_survey_type(self):
        return self.pms_property_id.ine_category_id.survey_type or "hotel"

    def ine_generate_xml(self):
        self.check_ine_mandatory_fields(self.pms_property_id)
        self._check_ine_period()

        number_of_rooms = sum(
            self.env["pms.room"]
            .search(
                [
                    ("in_ine", "=", True),
                    ("pms_property_id", "=", self.pms_property_id.id),
                ]
            )
            .mapped("capacity")
        )

        if number_of_rooms > self.pms_property_id.ine_seats:
            raise ValidationError(
                _(
                    "The number of seats, excluding extra beds ({num_rooms})"
                    + " exceeds the number of seats "
                    "established in the property ({ine_seats})"
                ).format(
                    num_rooms=str(number_of_rooms),
                    ine_seats=str(self.pms_property_id.ine_seats),
                )
            )

        if self._ine_survey_type() == "apartments":
            survey_tag = self._ine_build_xml_apartments()
        else:
            survey_tag = self._ine_build_xml_hotel()

        xmlstr = '<?xml version="1.0" encoding="UTF-8"?>'
        xmlstr += ET.tostring(survey_tag).decode("utf-8")

        self.txt_binary = base64.b64encode(xmlstr.encode("utf-8"))
        self.txt_filename = (
            "INE_"
            + str(self.start_date.month)
            + "_"
            + str(self.start_date.year)
            + ".xml"
        )

        return {
            "context": self.env.context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "pms.ine.wizard",
            "res_id": self.id,
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def _ine_build_xml_hotel(self):
        # INE XML
        survey_tag = ET.Element("ENCUESTA", self._ine_get_root_attrs("hotel"))

        # INE XML -> PROPERTY
        header_tag = ET.SubElement(survey_tag, "CABECERA")
        date = ET.SubElement(header_tag, "FECHA_REFERENCIA")
        ET.SubElement(date, "MES").text = f"{self.start_date.month:02}"
        ET.SubElement(date, "ANYO").text = str(self.start_date.year)
        ET.SubElement(header_tag, "DIAS_ABIERTO_MES_REFERENCIA").text = (
            "%02d"
            % (calendar.monthrange(self.start_date.year, self.start_date.month)[1])
        )
        ET.SubElement(
            header_tag, "RAZON_SOCIAL"
        ).text = self.pms_property_id.company_id.name
        ET.SubElement(
            header_tag, "NOMBRE_ESTABLECIMIENTO"
        ).text = self.pms_property_id.name

        ET.SubElement(header_tag, "CIF_NIF").text = self.ine_get_nif_cif(
            self.pms_property_id.company_id.vat
        )
        ET.SubElement(
            header_tag, "NUMERO_REGISTRO"
        ).text = self.pms_property_id.ine_tourism_number
        ET.SubElement(header_tag, "DIRECCION").text = self.pms_property_id.street
        ET.SubElement(header_tag, "CODIGO_POSTAL").text = self.pms_property_id.zip
        ET.SubElement(header_tag, "LOCALIDAD").text = self.pms_property_id.city
        ET.SubElement(header_tag, "MUNICIPIO").text = self.pms_property_id.city
        ET.SubElement(header_tag, "PROVINCIA").text = self._ine_get_province_name()
        ET.SubElement(
            header_tag, "TELEFONO_1"
        ).text = self.pms_property_id.phone.replace(" ", "")[0:12]
        ET.SubElement(
            header_tag, "TIPO"
        ).text = self.pms_property_id.ine_category_id.type
        ET.SubElement(
            header_tag, "CATEGORIA"
        ).text = self.pms_property_id.ine_category_id.category
        ET.SubElement(header_tag, "HABITACIONES").text = str(
            self.env["pms.room"].search_count(
                [
                    ("in_ine", "=", True),
                    ("pms_property_id", "=", self.pms_property_id.id),
                ]
            )
        )

        ET.SubElement(header_tag, "PLAZAS_DISPONIBLES_SIN_SUPLETORIAS").text = str(
            self.pms_property_id.ine_seats
        )
        if self.pms_property_id.website:
            ET.SubElement(header_tag, "URL").text = self.pms_property_id.website[0:100]

        # INE XML -> GUESTS
        accommodation_tag = ET.SubElement(survey_tag, "ALOJAMIENTO")
        self._ine_append_guest_movements(accommodation_tag)

        rooms_tag = ET.SubElement(survey_tag, "HABITACIONES")
        rooms = self.ine_rooms(self.start_date, self.end_date, self.pms_property_id)
        # INE XML -> ROOMS
        for key_date, value_rooms in rooms.items():
            rooms_move = ET.SubElement(rooms_tag, "HABITACIONES_MOVIMIENTO")
            ET.SubElement(rooms_move, "HABITACIONES_N_DIA").text = f"{key_date.day:02}"
            ET.SubElement(rooms_move, "PLAZAS_SUPLETORIAS").text = str(
                value_rooms["extra_beds"]
            )
            ET.SubElement(rooms_move, "HABITACIONES_DOBLES_USO_DOBLE").text = str(
                value_rooms["double_rooms_double_use"]
            )
            ET.SubElement(rooms_move, "HABITACIONES_DOBLES_USO_INDIVIDUAL").text = str(
                value_rooms["double_rooms_single_use"]
            )
            ET.SubElement(rooms_move, "HABITACIONES_OTRAS").text = str(
                value_rooms["other_rooms"]
            )
        prices_tag = ET.SubElement(survey_tag, "PRECIOS")

        ET.SubElement(prices_tag, "REVPAR_MENSUAL").text = self._ine_format_decimal(
            self.ine_calculate_revpar(
                self.start_date,
                self.end_date,
            )
        )

        ET.SubElement(prices_tag, "ADR_MENSUAL").text = self._ine_format_decimal(
            self.ine_calculate_adr(
                self.start_date,
                self.end_date,
            )
        )
        basic_domain = [
            ("pms_property_id", "=", self.pms_property_id.id),
            ("occupies_availability", "=", True),
            ("reservation_id.reservation_type", "=", "normal"),
        ]
        total_groups_domains = {
            "tour_operator_offline": basic_domain
            + [
                ("reservation_id.agency_id.sale_channel_id.name", "ilike", "Operator"),
                ("reservation_id.agency_id.sale_channel_id.is_on_line", "=", True),
            ],
            "tour_operator_online": basic_domain
            + [
                ("reservation_id.agency_id.sale_channel_id.name", "ilike", "Operator"),
                ("reservation_id.agency_id.sale_channel_id.is_on_line", "=", False),
            ],
            "companies": basic_domain
            + [
                ("reservation_id.partner_id", "!=", False),
                ("reservation_id.partner_id.is_company", "=", True),
                ("reservation_id.partner_id.is_agency", "=", False),
            ],
            "agencies": basic_domain
            + [
                ("reservation_id.agency_id", "!=", False),
                ("reservation_id.agency_id.sale_channel_id.is_on_line", "=", False),
            ],
            "otas": basic_domain
            + [
                ("reservation_id.agency_id", "!=", False),
                ("reservation_id.agency_id.sale_channel_id.is_on_line", "=", True),
            ],
            "persons": basic_domain
            + [
                "|",
                ("reservation_id.partner_id", "=", False),
                ("reservation_id.partner_id.is_company", "=", False),
            ],
            "groups": basic_domain
            + [("reservation_id.folio_id.number_of_rooms", ">=", 4)],
            "internet": basic_domain
            + [("reservation_id.sale_channel_origin_id.is_on_line", "=", True)],
            "others": basic_domain
            + [
                "|",
                ("reservation_id.sale_channel_origin_id.is_on_line", "!=", True),
                ("reservation_id.sale_channel_origin_id", "=", False),
            ],
        }
        percents = {}
        adrs = {}

        for group, domain in total_groups_domains.items():
            percents[group] = self.ine_calculate_occupancy(
                self.start_date,
                self.end_date,
                domain,
            )
            adrs[group] = self.ine_calculate_adr(
                self.start_date,
                self.end_date,
                domain,
            )

        total_percent = sum(percents.values())

        if total_percent:
            # Normalize in integer hundredths so that the percentages
            # printed in the file add up to exactly 100.00: the INE
            # content validation rejects files whose percentage columns
            # exceed 100.00, and float rounding artifacts have caused
            # rejected files in the past.
            # The INE also requires the percentage and the ADR of each client
            # type to be consistent: a client type with a rate must report a
            # non-zero percentage and vice versa.
            cents = {
                group: int(round(value * 10000 / total_percent)) if adrs[group] else 0
                for group, value in percents.items()
            }
            for group, value in cents.items():
                if adrs[group] and not value:
                    cents[group] = 1
            if any(cents.values()):
                cents[max(cents, key=cents.get)] += 10000 - sum(cents.values())
            percents = {group: value / 100.0 for group, value in cents.items()}
        else:
            for group in percents:
                percents[group] = 0.0

        hotel_price_tags = [
            (
                "tour_operator_offline",
                "ADR_TOUROPERADOR_TRADICIONAL",
                "PCTN_HABITACIONES_OCUPADAS_TOUROPERADOR_TRADICIONAL",
            ),
            (
                "tour_operator_online",
                "ADR_TOUROPERADOR_ONLINE",
                "PCTN_HABITACIONES_OCUPADAS_TOUROPERADOR_ONLINE",
            ),
            ("companies", "ADR_EMPRESAS", "PCTN_HABITACIONES_OCUPADAS_EMPRESAS"),
            (
                "agencies",
                "ADR_AGENCIA_DE_VIAJE_TRADICIONAL",
                "PCTN_HABITACIONES_OCUPADAS_AGENCIA_TRADICIONAL",
            ),
            (
                "otas",
                "ADR_AGENCIA_DE_VIAJE_ONLINE",
                "PCTN_HABITACIONES_OCUPADAS_AGENCIA_ONLINE",
            ),
            ("persons", "ADR_PARTICULARES", "PCTN_HABITACIONES_OCUPADAS_PARTICULARES"),
            ("groups", "ADR_GRUPOS", "PCTN_HABITACIONES_OCUPADAS_GRUPOS"),
            ("internet", "ADR_INTERNET", "PCTN_HABITACIONES_OCUPADAS_INTERNET"),
            ("others", "ADR_OTROS", "PCTN_HABITACIONES_OCUPADAS_OTROS"),
        ]
        for group, adr_tag, pctn_tag in hotel_price_tags:
            ET.SubElement(prices_tag, adr_tag).text = self._ine_format_decimal(
                adrs[group]
            )
            ET.SubElement(prices_tag, pctn_tag).text = self._ine_format_decimal(
                percents[group]
            )

        self._ine_append_staff(survey_tag)

        return survey_tag

    def _ine_append_staff(self, survey_tag):
        staff_tag = ET.SubElement(survey_tag, "PERSONAL_OCUPADO")
        ET.SubElement(staff_tag, "PERSONAL_NO_REMUNERADO").text = str(
            self.pms_property_id.ine_unpaid_staff
        )
        ET.SubElement(staff_tag, "PERSONAL_REMUNERADO_FIJO").text = str(
            self.pms_property_id.ine_permanent_staff
        )
        ET.SubElement(staff_tag, "PERSONAL_REMUNERADO_EVENTUAL").text = str(
            self.pms_property_id.ine_eventual_staff
        )

    @api.model
    def ine_apartments_capacity(self, pms_property_id):
        """
        Returns a dictionary:
        {
            apartment_type: {
                'units': number of accommodation units,
                'seats': number of seats (excluding extra beds),
                'room_ids': [pms.room ids],
            },
            # ... one entry per INE_APARTMENT_TYPES
        }
        """
        result = {
            apartment_type: {"units": 0, "seats": 0, "room_ids": []}
            for apartment_type in INE_APARTMENT_TYPES
        }
        rooms = self.env["pms.room"].search(
            [
                ("in_ine", "=", True),
                ("pms_property_id", "=", pms_property_id.id),
            ]
        )
        for room in rooms:
            apartment_type = room.ine_get_apartment_type()
            result[apartment_type]["units"] += 1
            result[apartment_type]["seats"] += room.capacity
            result[apartment_type]["room_ids"].append(room.id)
        return result

    @api.model
    def ine_apartments_occupancy(self, start_date, end_date, pms_property_id):
        """
        Returns a dictionary (only dates with occupancy or extra beds):
        {
            date: {
                'occupied': {apartment_type: number of occupied units},
                'extra_beds': number of extra beds,
            },
            # ... more dates
        }
        Occupancy criteria mirror ine_rooms: reservation lines occupying
        availability of normal reservations in confirmed/onboard/done state,
        on INE rooms, with at least one valid check-in partner.
        """
        occupancy = {}
        for p_date in [
            start_date + datetime.timedelta(days=x)
            for x in range(0, (end_date - start_date).days + 1)
        ]:
            day_rooms = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("pms_property_id", "=", pms_property_id.id),
                        ("occupies_availability", "=", True),
                        ("reservation_id.reservation_type", "=", "normal"),
                        ("room_id.in_ine", "=", True),
                        ("date", "=", p_date),
                        (
                            "reservation_id.state",
                            "in",
                            ["confirmed", "onboard", "done"],
                        ),
                    ]
                )
                .filtered(
                    lambda r: len(
                        r.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state
                            not in ["dummy", "draft", "cancel", "precheckin"]
                        )
                    )
                    > 0
                )
                .mapped("room_id")
            )
            occupied = dict.fromkeys(INE_APARTMENT_TYPES, 0)
            for room in day_rooms:
                occupied[room.ine_get_apartment_type()] += 1
            extra_beds = self._ine_get_extra_beds(pms_property_id, p_date)
            if any(occupied.values()) or extra_beds:
                occupancy[p_date] = {
                    "occupied": occupied,
                    "extra_beds": int(extra_beds),
                }
        return occupancy

    def _ine_build_xml_apartments(self):
        """Build the Tourist Apartments Occupancy Survey (EOAP) XML.

        Prices simplification: the whole occupancy of each typology is
        reported under the normal rate (TARIFA_NORMAL = typology ADR,
        PCTN_TARIFA_NORMAL = 100), which satisfies the INE content
        validations (percentage sum must be 100 for occupied typologies).
        """
        pms_property = self.pms_property_id

        survey_tag = ET.Element("APARTAMENTOS", self._ine_get_root_attrs("apartments"))

        # EOAP XML -> CABECERA
        header_tag = ET.SubElement(survey_tag, "CABECERA")
        date = ET.SubElement(header_tag, "FECHA_REFERENCIA")
        ET.SubElement(date, "MES").text = f"{self.start_date.month:02}"
        ET.SubElement(date, "ANYO").text = str(self.start_date.year)
        ET.SubElement(header_tag, "DIAS_ABIERTO_MES_REFERENCIA").text = (
            "%02d"
            % (calendar.monthrange(self.start_date.year, self.start_date.month)[1])
        )
        ET.SubElement(header_tag, "RAZON_SOCIAL").text = pms_property.company_id.name
        ET.SubElement(header_tag, "NOMBRE_ESTABLECIMIENTO").text = pms_property.name
        ET.SubElement(header_tag, "CIF_NIF").text = self.ine_get_nif_cif(
            pms_property.company_id.vat
        )
        ET.SubElement(header_tag, "DIRECCION").text = pms_property.street
        ET.SubElement(header_tag, "CODIGO_POSTAL").text = pms_property.zip
        ET.SubElement(header_tag, "LOCALIDAD").text = pms_property.city
        ET.SubElement(header_tag, "MUNICIPIO").text = pms_property.city
        ET.SubElement(header_tag, "PROVINCIA").text = self._ine_get_province_name()
        ET.SubElement(header_tag, "TELEFONO_1").text = pms_property.phone.replace(
            " ", ""
        )[0:13]
        if pms_property.website:
            ET.SubElement(header_tag, "URL").text = pms_property.website[0:100]

        # EOAP XML -> CABECERA_APARTAMENTOS
        apartments_header_tag = ET.SubElement(survey_tag, "CABECERA_APARTAMENTOS")
        ET.SubElement(
            apartments_header_tag, "CATEGORIA"
        ).text = pms_property.ine_category_id.category

        # EOAP XML -> INFORMANTE
        informant_tag = ET.SubElement(survey_tag, "INFORMANTE")
        ET.SubElement(informant_tag, "NOMBRE").text = pms_property.ine_informant_name
        ET.SubElement(informant_tag, "CARGO").text = pms_property.ine_informant_job
        ET.SubElement(informant_tag, "TELEFONOINF").text = (
            pms_property.ine_informant_phone or pms_property.phone
        ).replace(" ", "")[0:13]
        ET.SubElement(informant_tag, "EMAIL").text = pms_property.ine_informant_email

        # EOAP XML -> ALOJAMIENTO (shared with the hotel survey)
        accommodation_tag = ET.SubElement(survey_tag, "ALOJAMIENTO")
        self._ine_append_guest_movements(accommodation_tag)

        # EOAP XML -> CAPACIDAD
        capacity = self.ine_apartments_capacity(pms_property)
        capacity_tag = ET.SubElement(survey_tag, "CAPACIDAD")
        for apartment_type in INE_APARTMENT_TYPES:
            suffix = INE_APARTMENT_XML_SUFFIXES[apartment_type]
            ET.SubElement(capacity_tag, "N_APARTAMENTOS_" + suffix).text = str(
                capacity[apartment_type]["units"]
            )
        for apartment_type in INE_APARTMENT_TYPES:
            suffix = INE_APARTMENT_XML_SUFFIXES[apartment_type]
            ET.SubElement(
                capacity_tag, "PLAZAS_TOTALES_APARTAMENTOS_" + suffix
            ).text = str(capacity[apartment_type]["seats"])

        # EOAP XML -> OCUPACION
        occupancy = self.ine_apartments_occupancy(
            self.start_date, self.end_date, pms_property
        )
        occupancy_tag = ET.SubElement(survey_tag, "OCUPACION")
        for p_date in sorted(occupancy):
            movement = ET.SubElement(occupancy_tag, "MOVIMIENTO")
            ET.SubElement(movement, "N_DIA_AP").text = f"{p_date.day:02}"
            for apartment_type in INE_APARTMENT_TYPES:
                suffix = INE_APARTMENT_XML_SUFFIXES[apartment_type]
                ET.SubElement(movement, "APARTAMENTOS_OCUPADOS_" + suffix).text = str(
                    occupancy[p_date]["occupied"][apartment_type]
                )
            ET.SubElement(movement, "PLAZAS_SUPLETORIAS").text = str(
                occupancy[p_date]["extra_beds"]
            )

        # EOAP XML -> PRECIOS
        prices_tag = ET.SubElement(survey_tag, "PRECIOS")
        for apartment_type in INE_APARTMENT_TYPES:
            block_tag = ET.SubElement(
                prices_tag, INE_APARTMENT_PRICE_TAGS[apartment_type]
            )
            occupied_any = any(
                day["occupied"][apartment_type] for day in occupancy.values()
            )
            adr = 0.0
            if occupied_any:
                adr = round(
                    pms_property._get_adr(
                        self.start_date,
                        self.end_date,
                        [
                            ("room_id.in_ine", "=", True),
                            ("room_id", "in", capacity[apartment_type]["room_ids"]),
                        ],
                    ),
                    2,
                )
                if adr <= 0:
                    raise ValidationError(
                        _(
                            "The average daily rate of the occupied "
                            "apartment typology '%s' is zero. The INE "
                            "requires a price greater than zero for "
                            "occupied typologies.",
                            INE_APARTMENT_PRICE_TAGS[apartment_type],
                        )
                    )
            ET.SubElement(block_tag, "TARIFA_NORMAL").text = self._ine_format_decimal(
                adr
            )
            ET.SubElement(
                block_tag, "PCTN_TARIFA_NORMAL"
            ).text = self._ine_format_decimal(100 if occupied_any else 0)
            for tarifa_tag, pctn_tag in [
                ("TARIFA_FIN_DE_SEMANA", "PCTN_TARIFA_FIN_DE_SEMANA"),
                ("TARIFA_TOUROPERADOR", "PCTN_TARIFA_TOUROPERADOR"),
                ("TARIFA_OTRAS", "PCTN_TARIFA_OTRAS"),
            ]:
                ET.SubElement(block_tag, tarifa_tag).text = self._ine_format_decimal(0)
                ET.SubElement(block_tag, pctn_tag).text = self._ine_format_decimal(0)

        # EOAP XML -> PERSONAL_OCUPADO
        self._ine_append_staff(survey_tag)

        # informative wizard fields
        self.ine_calculate_adr(self.start_date, self.end_date)
        self.ine_calculate_revpar(self.start_date, self.end_date)

        return survey_tag

    def _ine_append_guest_movements(self, accommodation_tag):
        """Fill the ALOJAMIENTO block (shared by all INE occupancy surveys).

        The schema requires at least one RESIDENCIA, so a period without
        guest movements cannot produce a valid file.
        """
        countries = self.ine_countries(
            self.start_date, self.end_date, self.pms_property_id.id
        )
        for key_country, value_country in countries.items():
            if key_country != CODE_SPAIN:
                country = self.env["res.country"].search([("code", "=", key_country)])
                residency_tag = ET.SubElement(accommodation_tag, "RESIDENCIA")
                ET.SubElement(residency_tag, "ID_PAIS").text = country.code_alpha3
                for key_date, value_dates in value_country.items():
                    movement = ET.SubElement(residency_tag, "MOVIMIENTO")
                    ET.SubElement(movement, "N_DIA").text = f"{key_date.day:02}"
                    ET.SubElement(movement, "ENTRADAS").text = str(
                        value_dates.get("arrivals") or 0
                    )
                    ET.SubElement(movement, "SALIDAS").text = str(
                        value_dates.get("departures") or 0
                    )
                    ET.SubElement(movement, "PERNOCTACIONES").text = str(
                        value_dates.get("pernoctations") or 0
                    )
            else:
                for code_ine, value_state in value_country.items():
                    residency_tag = ET.SubElement(accommodation_tag, "RESIDENCIA")
                    ET.SubElement(residency_tag, "ID_PROVINCIA_ISLA").text = code_ine
                    for key_date, value_dates in value_state.items():
                        movement = ET.SubElement(residency_tag, "MOVIMIENTO")
                        ET.SubElement(movement, "N_DIA").text = f"{key_date.day:02}"
                        ET.SubElement(movement, "ENTRADAS").text = str(
                            value_dates.get("arrivals") or 0
                        )
                        ET.SubElement(movement, "SALIDAS").text = str(
                            value_dates.get("departures") or 0
                        )
                        ET.SubElement(movement, "PERNOCTACIONES").text = str(
                            value_dates.get("pernoctations") or 0
                        )

        if not len(accommodation_tag):
            raise ValidationError(
                _(
                    "There are no guest movements in the selected period, so "
                    "the INE file cannot be generated: the survey schema "
                    "requires at least one place of residence."
                )
            )
