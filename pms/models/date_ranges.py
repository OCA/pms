# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Turning a set of nights into the ranges that cover them.

Shared by the models that express a period as one record, and by the writers
that reach them holding a set of dates instead.
"""
import datetime


def collapse_dates(dates):
    """Group nights into the fewest ranges that cover them.

    :param dates: an iterable of dates, in any order and with repeats.
    :return: a list of ``(date_from, date_to)`` tuples, both included.
    """
    ranges = []
    start = previous = None
    for date in sorted(set(dates)):
        if start is None:
            start = previous = date
        elif date == previous + datetime.timedelta(days=1):
            previous = date
        else:
            ranges.append((start, previous))
            start = previous = date
    if start is not None:
        ranges.append((start, previous))
    return ranges
