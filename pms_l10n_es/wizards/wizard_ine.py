import base64
import calendar
import datetime
import xml.etree.cElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# TODO: Review code (code iso ?)
CODE_SPAIN = "ES"


class WizardIne(models.TransientModel):
    _name = "pms.ine.wizard"
    _description = "Wizard to generate statistical info."

    pms_property_id = fields.Many2one(
        string="Property",
        comodel_name="pms.property",
        default=lambda self: self.env["pms.property"].browse(
            self.env.user.get_active_property_ids()[0]
        ),
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
                    lambda l: len(
                        l.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state not in ["draft", "cancel"]
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
                    lambda l: len(
                        l.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state not in ["draft", "cancel"]
                        )
                    )
                    == 2
                )
                .mapped("room_id")
            )

            # service lines with extra beds
            extra_bed_service_lines = self.env["pms.service.line"].search(
                [
                    ("pms_property_id", "=", pms_property_id.id),
                    ("product_id.is_extra_bed", "=", True),
                    ("reservation_id.reservation_type", "=", "normal"),
                    ("reservation_id.state", "in", ["confirmed", "onboard", "done"]),
                    ("date", "=", p_date),
                ]
            )

            extra_beds = 0

            # get num. extra beds
            for ebsl in extra_bed_service_lines:
                reservation_lines = ebsl.reservation_id.reservation_line_ids.filtered(
                    lambda x: x.date == ebsl.date
                    and x.room_id.in_ine
                    and x.occupies_availability
                )
                if reservation_lines:
                    extra_beds += (
                        ebsl.day_qty
                        - reservation_lines.reservation_id.children_occupying
                    )
                    # children occuppying do not have checkin partner data

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
                    lambda l: len(
                        l.reservation_id.checkin_partner_ids.filtered(
                            lambda c: c.state not in ["draft", "cancel"]
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
    def ine_nationalities(self, start_date, end_date, pms_property_id):
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
                if not entry["nationality_id"]:
                    guests_with_no_nationality = self.env["pms.checkin.partner"].search(
                        entry["__domain"]
                    )
                    guests_with_no_nationality = (
                        str(guests_with_no_nationality.mapped("name"))
                        .replace("[", "")
                        .replace("]", "")
                    )
                    raise ValidationError(
                        _(
                            "The following guests have no residence nationality set :%s.",
                            guests_with_no_nationality,
                        )
                    )
                # get nationality_id from group set read_group results
                nationality_id_code = (
                    self.env["res.country"]
                    .search([("id", "=", entry["nationality_id"][0])])
                    .code
                )
                # all countries except Spain
                if nationality_id_code != CODE_SPAIN:

                    # get count of each result
                    num = entry["__count"]

                    # update/create dicts for countries & dates and set num. arrivals
                    if not nationalities.get(nationality_id_code):
                        nationalities[nationality_id_code] = dict()
                    if not nationalities[nationality_id_code].get(date):
                        nationalities[nationality_id_code][date] = dict()
                    nationalities[nationality_id_code][date][type_of_entry] = num
                else:
                    # arrivals grouped by state_id (Spain "provincias")
                    read_by_arrivals_spain = self.env["pms.checkin.partner"].read_group(
                        entry["__domain"],
                        ["residence_state_id"],
                        ["residence_state_id"],
                        lazy=False,
                    )
                    # iterate read_group results from Spain
                    for entry_from_spain in read_by_arrivals_spain:
                        if not entry_from_spain["residence_state_id"]:
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
                                    "The following spanish guests have no state set :%s.",
                                    spanish_guests_with_no_state,
                                )
                            )
                        residence_state_id = self.env["res.country.state"].browse(
                            entry_from_spain["residence_state_id"][0]
                        )  # .ine_code
                        ine_code = residence_state_id.ine_code

                        if not ine_code:
                            raise ValidationError(
                                _(
                                    "%s does not have the INE Code configured"
                                    % residence_state_id.name
                                )
                            )
                        # get count of each result
                        num_spain = entry_from_spain["__count"]

                        # update/create dicts for states & dates and set num. arrivals
                        if not nationalities.get(CODE_SPAIN):
                            nationalities[CODE_SPAIN] = dict()

                        if not nationalities[CODE_SPAIN].get(ine_code):
                            nationalities[CODE_SPAIN][ine_code] = dict()

                        if not nationalities[CODE_SPAIN][ine_code].get(date):
                            nationalities[CODE_SPAIN][ine_code][date] = dict()
                        nationalities[CODE_SPAIN][ine_code][date][
                            type_of_entry
                        ] = num_spain

        # result object
        nationalities = dict()

        # iterate days between start_date and end_date
        for p_date in [
            start_date + datetime.timedelta(days=x)
            for x in range(0, (end_date - start_date).days + 1)
        ]:
            # search for checkin partners
            hosts = self.env["pms.checkin.partner"].search(
                [
                    ("pms_property_id", "=", pms_property_id),
                    ("checkin", "<=", p_date),
                    ("checkout", ">=", p_date),
                    ("reservation_id.reservation_type", "=", "normal"),
                    ("state", "not in", ["dummy", "draft", "cancel"]),
                ]
            )
            hosts = hosts.filtered(
                lambda x: all(
                    x.reservation_id.reservation_line_ids.mapped("room_id.in_ine")
                )
            )

            # arrivals
            arrivals = hosts.filtered(lambda x: x.checkin == p_date)

            # arrivals grouped by nationality_id
            read_by_arrivals = self.env["pms.checkin.partner"].read_group(
                [("id", "in", arrivals.ids)],
                ["nationality_id"],
                ["nationality_id"],
                orderby="nationality_id",
                lazy=False,
            )

            # departures
            departures = hosts.filtered(lambda x: x.checkout == p_date)

            # departures grouped by nationality_id
            read_by_departures = self.env["pms.checkin.partner"].read_group(
                [("id", "in", departures.ids)],
                ["nationality_id"],
                ["nationality_id"],
                orderby="nationality_id",
                lazy=False,
            )

            # pernoctations
            pernoctations = hosts - departures

            # pernoctations grouped by nationality_id
            read_by_pernoctations = self.env["pms.checkin.partner"].read_group(
                [("id", "in", pernoctations.ids)],
                ["nationality_id"],
                ["nationality_id"],
                orderby="nationality_id",
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

        return nationalities

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
            filter_percent = round(
                len(filter_reservations) * 100 / len(total_reservations), 2
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

        if not pms_property_id.ine_category_id:
            raise ValidationError(_("The property category is not established."))

    def ine_generate_xml(self):

        self.check_ine_mandatory_fields(self.pms_property_id)

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
                    "The number of seats, excluding extra beds (%s)"
                    % str(number_of_rooms)
                    + " exceeds the number of seats established in the property (%s)"
                    % str(self.pms_property_id.ine_seats)
                )
            )

        # INE XML
        survey_tag = ET.Element("ENCUESTA")

        # INE XML -> PROPERTY
        header_tag = ET.SubElement(survey_tag, "CABECERA")
        date = ET.SubElement(header_tag, "FECHA_REFERENCIA")
        ET.SubElement(date, "MES").text = f"{self.start_date.month:02}"
        ET.SubElement(date, "ANYO").text = str(self.start_date.year)
        ET.SubElement(header_tag, "DIAS_ABIERTO_MES_REFERENCIA").text = str(
            calendar.monthrange(self.start_date.year, self.start_date.month)[1]
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
        ET.SubElement(
            header_tag, "PROVINCIA"
        ).text = self.pms_property_id.partner_id.state_id.name
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
        ET.SubElement(header_tag, "URL").text = self.pms_property_id.website

        # INE XML -> GUESTS
        accommodation_tag = ET.SubElement(survey_tag, "ALOJAMIENTO")

        nationalities = self.ine_nationalities(
            self.start_date, self.end_date, self.pms_property_id.id
        )
        for key_country, value_country in nationalities.items():

            country = self.env["res.country"].search([("code", "=", key_country)])

            if key_country != CODE_SPAIN:
                residency_tag = ET.SubElement(accommodation_tag, "RESIDENCIA")
                ET.SubElement(residency_tag, "ID_PAIS").text = country.code_alpha3

                for key_date, value_dates in value_country.items():
                    movement = ET.SubElement(residency_tag, "MOVIMIENTO")
                    ET.SubElement(movement, "N_DIA").text = f"{key_date.day:02}"
                    num_arrivals = (
                        value_dates["arrivals"] if value_dates.get("arrivals") else 0
                    )
                    num_departures = (
                        value_dates["departures"]
                        if value_dates.get("departures")
                        else 0
                    )
                    num_pernoctations = (
                        value_dates["pernoctations"]
                        if value_dates.get("pernoctations")
                        else 0
                    )

                    ET.SubElement(movement, "ENTRADAS").text = str(num_arrivals)
                    ET.SubElement(movement, "SALIDAS").text = str(num_departures)
                    ET.SubElement(movement, "PERNOCTACIONES").text = str(
                        num_pernoctations
                    )
            else:
                for code_ine, value_state in value_country.items():
                    residency_tag = ET.SubElement(accommodation_tag, "RESIDENCIA")
                    ET.SubElement(residency_tag, "ID_PROVINCIA_ISLA").text = code_ine
                    for key_date, value_dates in value_state.items():
                        movement = ET.SubElement(residency_tag, "MOVIMIENTO")
                        ET.SubElement(movement, "N_DIA").text = f"{key_date.day:02}"
                        num_arrivals = (
                            value_dates["arrivals"]
                            if value_dates.get("arrivals")
                            else 0
                        )
                        num_departures = (
                            value_dates["departures"]
                            if value_dates.get("departures")
                            else 0
                        )
                        num_pernoctations = (
                            value_dates["pernoctations"]
                            if value_dates.get("pernoctations")
                            else 0
                        )
                        ET.SubElement(movement, "ENTRADAS").text = str(num_arrivals)
                        ET.SubElement(movement, "SALIDAS").text = str(num_departures)
                        ET.SubElement(movement, "PERNOCTACIONES").text = str(
                            num_pernoctations
                        )

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

        ET.SubElement(prices_tag, "REVPAR_MENSUAL").text = str(
            self.ine_calculate_revpar(
                self.start_date,
                self.end_date,
            )
        )

        ET.SubElement(prices_tag, "ADR_MENSUAL").text = str(
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

        # In this point, the groups adrs and percents are well calculated.... but,
        # our statist friends want the total of the percentage groupings to add up = 100%,
        # without conceiving that the groupings overlap, so they cannot receive real data
        # and force us to pervert the original data so that it fits in their grid notebook.
        # The purpose of the following lines of code is only to show the inefficiency
        # of the state statistics,
        # so at least I will feel that the effort made some sense :)

        total_percent = sum([val for val in percents.values()])
        for group in total_groups_domains.keys():
            percents[group] = round(percents[group] * 100 / total_percent, 2)

        ET.SubElement(prices_tag, "ADR_TOUROPERADOR_TRADICIONAL").text = str(
            adrs["tour_operator_offline"]
        )
        ET.SubElement(
            prices_tag, "PCTN_HABITACIONES_OCUPADAS_TOUROPERADOR_TRADICIONAL"
        ).text = str(percents["tour_operator_offline"])
        ET.SubElement(prices_tag, "ADR_TOUROPERADOR_ONLINE").text = str(
            adrs["tour_operator_online"]
        )
        ET.SubElement(
            prices_tag, "PCTN_HABITACIONES_OCUPADAS_TOUROPERADOR_ONLINE"
        ).text = str(percents["tour_operator_online"])
        ET.SubElement(prices_tag, "ADR_EMPRESAS").text = str(adrs["companies"])
        ET.SubElement(prices_tag, "PCTN_HABITACIONES_OCUPADAS_EMPRESAS").text = str(
            percents["companies"]
        )
        ET.SubElement(prices_tag, "ADR_AGENCIA_DE_VIAJE_TRADICIONAL").text = str(
            adrs["agencies"]
        )
        ET.SubElement(
            prices_tag, "PCTN_HABITACIONES_OCUPADAS_AGENCIA_TRADICIONAL"
        ).text = str(percents["agencies"])
        ET.SubElement(prices_tag, "ADR_AGENCIA_DE_VIAJE_ONLINE").text = str(
            adrs["otas"]
        )
        ET.SubElement(
            prices_tag, "PCTN_HABITACIONES_OCUPADAS_AGENCIA_ONLINE"
        ).text = str(percents["otas"])
        ET.SubElement(prices_tag, "ADR_PARTICULARES").text = str(adrs["persons"])
        ET.SubElement(prices_tag, "PCTN_HABITACIONES_OCUPADAS_PARTICULARES").text = str(
            percents["persons"]
        )
        ET.SubElement(prices_tag, "ADR_GRUPOS").text = str(adrs["groups"])
        ET.SubElement(prices_tag, "PCTN_HABITACIONES_OCUPADAS_GRUPOS").text = str(
            percents["groups"]
        )
        ET.SubElement(prices_tag, "ADR_INTERNET").text = str(adrs["internet"])
        ET.SubElement(prices_tag, "PCTN_HABITACIONES_OCUPADAS_INTERNET").text = str(
            percents["internet"]
        )
        ET.SubElement(prices_tag, "ADR_OTROS").text = str(adrs["others"])
        ET.SubElement(prices_tag, "PCTN_HABITACIONES_OCUPADAS_OTROS").text = str(
            percents["others"]
        )

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

        xmlstr = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        xmlstr += ET.tostring(survey_tag).decode("utf-8")

        self.txt_binary = base64.b64encode(str.encode(xmlstr))
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
