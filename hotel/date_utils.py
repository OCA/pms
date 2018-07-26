# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta
from dateutil import tz
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from openerp import fields, _
from openerp.exceptions import ValidationError


# Generate a 'datetime' object from 'str_date' string with 'dtformat' format.
def _generate_datetime(str_date, dtformat, stz=False):
    ndate = False
    try:
        ndate = datetime.strptime(str_date, dtformat)
        ndate = ndate.replace(tzinfo=tz.gettz(stz and str(stz) or 'UTC'))
    except ValueError:
        return False

    return ndate


# Try generate a 'datetime' object from 'str_date' string
# using all odoo formats
def get_datetime(str_date, dtformat=False, hours=True, end_day=False,
                 stz=False):
    if dtformat:
        date_dt = _generate_datetime(str_date, dtformat, stz=stz)
    else:
        date_dt = _generate_datetime(
            str_date,
            DEFAULT_SERVER_DATETIME_FORMAT,
            stz=stz)
        if not date_dt:
            date_dt = _generate_datetime(
                str_date,
                DEFAULT_SERVER_DATE_FORMAT,
                stz=stz)

    if date_dt:
        if end_day:
            date_dt = dt_no_hours(date_dt, end_day=True)
        elif not hours:
            date_dt = dt_no_hours(date_dt)

    return date_dt


# Compare two dates
def date_compare(str_date_a, str_date_b, hours=True):
    date_dt_a = get_datetime(str_date_a)
    date_dt_b = get_datetime(str_date_b)

    if not hours:
        date_dt_a = dt_no_hours(date_dt_a)
        date_dt_b = dt_no_hours(date_dt_b)

    return date_dt_a == date_dt_b


# Set hours to zero
def dt_no_hours(new_start_date_dt, end_day=False):
    if not end_day:
        return new_start_date_dt.replace(hour=0, minute=0, second=0,
                                         microsecond=0)
    else:
        return new_start_date_dt.replace(hour=23, minute=59, second=59,
                                         microsecond=999999)


# Get now 'datetime' object
def now(hours=False):
    now_utc_dt = fields.datetime.now().replace(tzinfo=tz.tzutc())

    if not hours:
        now_utc_dt = now_utc_dt.replace(hour=0, minute=0, second=0,
                                        microsecond=0)

    return now_utc_dt


# Get the difference in days between 'str_date_start' and 'str_date_end'
def date_diff(date_start, date_end, hours=True, stz=False):
    if not isinstance(date_start, datetime):
        date_start_dt = get_datetime(date_start, stz=stz)
    else:
        date_start_dt = date_start
    if not isinstance(date_end, datetime):
        date_end_dt = get_datetime(date_end, stz=stz)
    else:
        date_end_dt = date_end

    if not date_start_dt or not date_end_dt:
        raise ValidationError(_("Invalid date. Can't compare it!"))

    if not hours:
        date_start_dt = dt_no_hours(date_start_dt)
        date_end_dt = dt_no_hours(date_end_dt)

    return abs((date_end_dt - date_start_dt).days)


# Get a new 'datetime' object from 'date_dt' usign the 'tz' timezone
def dt_as_timezone(date_dt, stz):
    return date_dt.astimezone(tz.gettz(stz and str(stz) or 'UTC'))


# Generate a list of days start in 'cdate'
def generate_dates_list(cdate,
                        num_days,
                        outformat=DEFAULT_SERVER_DATE_FORMAT, stz=False):
    ndate = get_datetime(cdate, stz=stz) if not isinstance(cdate, datetime) \
        else cdate
    return [(ndate + timedelta(days=i)).strftime(outformat)
            for i in range(0, num_days)]


# Check if 'str_date' is between 'str_start_date' and 'str_end_date'
#   0   Inside
#   -1  'str_date' is before 'str_start_date'
#   1   'str_date' is after 'str_end_date'
def date_in(str_date, str_start_date, str_end_date, hours=True, stz=False):
    if not isinstance(str_date, datetime):
        date_dt = get_datetime(str_date, stz=stz)
    else:
        date_dt = str_date
    if not isinstance(str_start_date, datetime):
        date_start_dt = get_datetime(str_date_start, stz=stz)
    else:
        date_start_dt = str_start_date
    if not isinstance(str_end_date, datetime):
        date_end_dt = get_datetime(str_end_date, stz=stz)
    else:
        date_end_dt = str_end_date

    if not date_start_dt or not date_end_dt or not date_dt:
        raise ValidationError(_("Invalid date. Can't compare it!"))

    if not hours:
        date_start_dt = dt_no_hours(date_start_dt)
        date_end_dt = dt_no_hours(date_end_dt)

    res = -2
    if date_dt >= date_start_dt and date_dt <= date_end_dt:
        res = 0
    elif date_dt > date_end_dt:
        res = 1
    elif date_dt < date_start_dt:
        res = -1

    return res


# Check if 'str_start_date_a' and 'str_start_date_b'
# is between 'str_start_date_b' and 'str_end_date_b'
#   0   Inside
#   -1  'str_date' is before 'str_start_date'
#   1   'str_date' is after 'str_end_date'
def range_dates_in(str_start_date_a,
                   str_end_date_a,
                   str_start_date_b,
                   str_end_date_b,
                   hours=True, stz=False):
    date_start_dt_a = get_datetime(str_start_date_a, stz=stz)
    date_end_dt_a = get_datetime(str_end_date_a, stz=stz)
    date_start_dt_b = get_datetime(str_start_date_b, stz=stz)
    date_end_dt_b = get_datetime(str_end_date_b, stz=stz)

    if not date_start_dt_a or not date_end_dt_a \
            or not date_start_dt_b or not date_end_dt_b:
        raise ValidationError(_("Invalid date. Can't compare it!"))

    if not hours:
        date_start_dt_b = dt_no_hours(date_start_dt_b)
        date_end_dt_b = dt_no_hours(date_end_dt_b)

    res = -2
    if date_start_dt_a >= date_start_dt_b and date_end_dt_a <= date_end_dt_b:
        res = 0
    elif date_start_dt_a < date_start_dt_b \
            and date_end_dt_a >= date_start_dt_b:
        res = -1
    elif date_start_dt_a <= date_end_dt_b and date_end_dt_a > date_end_dt_b:
        res = 1

    return res
