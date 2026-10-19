"""Content validations the INE applies to the occupancy survey files.

The INE validates an uploaded questionnaire twice: first against the XML
schema, and then against a list of content rules published in the survey
web service specification, identified there as XML_0 to XML_17. A file
that passes the schema and fails a content rule is rejected all the same,
and the establishment only finds out on the IRIA portal, days later, with
a message that names neither the guest nor the setting behind it.

Running the same rules here turns that into an error raised while the file
is being built, naming the day and the figures involved.

The functions take the built XML and plain numbers, never a record, so the
rules can be read and tested on their own. They return a list of sentences
ready to show, empty when the file would be accepted.
"""
from collections import defaultdict

from odoo import _

# Tags shared by both surveys: the block of guest movements is identical in
# the hotel and the tourist apartments questionnaires.
ACCOMMODATION_XPATH = "ALOJAMIENTO/RESIDENCIA"
HOTEL_ROOT_TAG = "ENCUESTA"


def _read_movements(residency_tag):
    """Return {day: (arrivals, departures, overnight stays)} of a residence."""
    movements = {}
    for movement_tag in residency_tag.findall("MOVIMIENTO"):
        day = int(movement_tag.findtext("N_DIA"))
        movements[day] = (
            int(movement_tag.findtext("ENTRADAS")),
            int(movement_tag.findtext("SALIDAS")),
            int(movement_tag.findtext("PERNOCTACIONES")),
        )
    return movements


def _residence_name(residency_tag):
    """Country or province the residence block stands for."""
    return residency_tag.findtext("ID_PAIS") or residency_tag.findtext(
        "ID_PROVINCIA_ISLA"
    )


def check_guest_movements(survey_tag, days_in_month):
    """Validate the ALOJAMIENTO block, shared by every occupancy survey.

    Covers the day as a key of the residence (XML_3), non negative figures
    (XML_6), overnight stays against arrivals (XML_7) and the daily chain
    of each residence (XML_8), which is the rule that rejects a file built
    for a week instead of the whole month.

    Returns the problems found, the overnight stays per day and the days
    carrying movements, the last two being what the room checks need.
    """
    problems = []
    overnight_stays = defaultdict(int)
    days_with_movement = set()
    for residency_tag in survey_tag.findall(ACCOMMODATION_XPATH):
        residence = _residence_name(residency_tag)
        days = [
            int(movement_tag.findtext("N_DIA"))
            for movement_tag in residency_tag.findall("MOVIMIENTO")
        ]
        for day in sorted({day for day in days if days.count(day) > 1}):
            problems.append(
                _(
                    "Place of residence %(residence)s: day %(day)s is "
                    "reported twice. The survey schema uses the day as a "
                    "key, so it can only appear once.",
                    residence=residence,
                    day=day,
                )
            )
        movements = _read_movements(residency_tag)
        previous_stays = None
        for day in range(1, days_in_month + 1):
            arrivals, departures, stays = movements.get(day, (0, 0, 0))
            if day in movements:
                days_with_movement.add(day)
                overnight_stays[day] += stays
            if min(arrivals, departures, stays) < 0:
                problems.append(
                    _(
                        "Place of residence %(residence)s, day %(day)s: "
                        "negative values are not allowed.",
                        residence=residence,
                        day=day,
                    )
                )
            if stays < arrivals:
                problems.append(
                    _(
                        "Place of residence %(residence)s, day %(day)s: "
                        "%(stays)s overnight stays for %(arrivals)s "
                        "arrivals. Every guest checking in stays at "
                        "least that night.",
                        residence=residence,
                        day=day,
                        stays=stays,
                        arrivals=arrivals,
                    )
                )
            expected = (previous_stays or 0) + arrivals - departures
            if previous_stays is not None and stays != expected:
                problems.append(
                    _(
                        "Place of residence %(residence)s, day %(day)s: "
                        "%(stays)s overnight stays, but the previous day "
                        "had %(previous)s with %(arrivals)s arrivals and "
                        "%(departures)s departures, so the INE expects "
                        "%(expected)s.",
                        residence=residence,
                        day=day,
                        stays=stays,
                        previous=previous_stays,
                        arrivals=arrivals,
                        departures=departures,
                        expected=expected,
                    )
                )
            previous_stays = stays
    return problems, overnight_stays, days_with_movement


def check_hotel_rooms(survey_tag, overnight_stays):
    """Validate the HABITACIONES block against the guest movements.

    Covers occupied rooms and overnight stays agreeing with each other
    (XML_9, XML_10, XML_11), the overnight stays fitting in the declared
    seats plus the extra beds (XML_12) and the occupied rooms fitting in
    the rooms of the establishment (XML_13).
    """
    problems = []
    rooms_total = int(survey_tag.findtext("CABECERA/HABITACIONES") or 0)
    seats = int(survey_tag.findtext("CABECERA/PLAZAS_DISPONIBLES_SIN_SUPLETORIAS") or 0)
    for movement_tag in survey_tag.findall("HABITACIONES/HABITACIONES_MOVIMIENTO"):
        day = int(movement_tag.findtext("HABITACIONES_N_DIA"))
        double_as_double = int(movement_tag.findtext("HABITACIONES_DOBLES_USO_DOBLE"))
        occupied = (
            double_as_double
            + int(movement_tag.findtext("HABITACIONES_DOBLES_USO_INDIVIDUAL"))
            + int(movement_tag.findtext("HABITACIONES_OTRAS"))
        )
        extra_beds = int(movement_tag.findtext("PLAZAS_SUPLETORIAS"))
        stays = overnight_stays.get(day, 0)
        if bool(occupied) != bool(stays):
            problems.append(
                _(
                    "Day %(day)s: %(rooms)s occupied rooms and %(stays)s "
                    "overnight stays. The INE expects both to be zero or "
                    "both greater than zero.",
                    day=day,
                    rooms=occupied,
                    stays=stays,
                )
            )
        if occupied > stays:
            problems.append(
                _(
                    "Day %(day)s: %(rooms)s occupied rooms for only "
                    "%(stays)s overnight stays.",
                    day=day,
                    rooms=occupied,
                    stays=stays,
                )
            )
        if stays and occupied == stays and double_as_double:
            problems.append(
                _(
                    "Day %(day)s: as many occupied rooms as overnight "
                    "stays, so no double room can be reported as used by "
                    "two people.",
                    day=day,
                )
            )
        if stays > seats + extra_beds:
            problems.append(
                _(
                    "Day %(day)s: %(stays)s overnight stays exceed the "
                    "%(seats)s available seats plus %(extra)s extra beds. "
                    "Check the seats declared in the property.",
                    day=day,
                    stays=stays,
                    seats=seats,
                    extra=extra_beds,
                )
            )
        if occupied > rooms_total:
            problems.append(
                _(
                    "Day %(day)s: %(rooms)s occupied rooms exceed the "
                    "%(total)s rooms of the establishment.",
                    day=day,
                    rooms=occupied,
                    total=rooms_total,
                )
            )
    return problems


def check_survey_content(survey_tag, days_in_month):
    """Return every content rule the built file would be rejected for.

    Empty when the INE would accept it.
    """
    problems, overnight_stays, days_with_movement = check_guest_movements(
        survey_tag, days_in_month
    )
    days_open = int(survey_tag.findtext("CABECERA/DIAS_ABIERTO_MES_REFERENCIA") or 0)
    # XML_0: the establishment cannot be open more days than the month has.
    if days_open > days_in_month:
        problems.append(
            _(
                "The file reports %(open)s days open in a month of " "%(days)s days.",
                open=days_open,
                days=days_in_month,
            )
        )
    # XML_2: no more days carrying guests than days open.
    if len(days_with_movement) > days_open:
        problems.append(
            _(
                "The file reports guest movements on %(moved)s days but "
                "only %(open)s days open.",
                moved=len(days_with_movement),
                open=days_open,
            )
        )
    if survey_tag.tag == HOTEL_ROOT_TAG:
        problems += check_hotel_rooms(survey_tag, overnight_stays)
    return problems


def extra_bed_nights(survey_tag):
    """Days reported with an extra bed, as they appear in the file.

    Reporting them is what keeps the file valid, but a room whose capacity
    is set too low would report an extra bed every single night, so they
    are listed back instead of passing unnoticed.
    """
    if survey_tag.tag == HOTEL_ROOT_TAG:
        movement_tags = survey_tag.findall("HABITACIONES/HABITACIONES_MOVIMIENTO")
        day_tag = "HABITACIONES_N_DIA"
    else:
        movement_tags = survey_tag.findall("OCUPACION/MOVIMIENTO")
        day_tag = "N_DIA_AP"
    return [
        movement_tag.findtext(day_tag)
        for movement_tag in movement_tags
        if int(movement_tag.findtext("PLAZAS_SUPLETORIAS") or 0)
    ]
