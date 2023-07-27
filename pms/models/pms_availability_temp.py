# Copyright 2021  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import _, api, fields, models


class PmsAvailabilityTemp(models.Model):
    _name = "pms.availability.temp"
    _description = "Room type availability per day"
    _auto = False

    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type for which availability is indicated",
        readonly=True,
        comodel_name="pms.room.type",
    )
    date = fields.Date(
        string="Date",
        help="Date for which availability applies",
        readonly=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the availability is directed",
        readonly=True,
        comodel_name="pms.property",
    )
    real_avail = fields.Integer(
        string="Real Avail",
        help="",
        readonly=True,
    )
    total_rooms = fields.Integer(
        string="Total Rooms",
        help="",
        readonly=True,
    )
    busy_rooms = fields.Integer(
        string="Busy Rooms",
        help="",
        readonly=True,
    )
    max_avail = fields.Integer(
        string="Max avail.",
        help="",
        readonly=True,
    )
    quota = fields.Integer(
        string="Quota",
        help="",
        readonly=True,
    )
    sale_avail = fields.Integer(
        string="Sale Avail.",
        help="",
        readonly=True,
        compute="_compute_sale_avail",
    )

    def _compute_sale_avail(self):
        for record in self:
            record.sale_avail = min(
                record.real_avail,
                record.quota if record.quota >= 0 else record.real_avail,
                record.max_avail if record.max_avail >= 0 else record.real_avail,
            )

    @property
    def _table_query(self):
        date_from = self.env.context.get('checkin') or fields.Date.today()
        date_to = self.env.context.get('checkout') or fields.Date.today() + timedelta(days=365)
        avail_plan_id = self.env.context.get('avail_plan_id') or False
        if not avail_plan_id and self.env.context.get('pricelist_id'):
            avail_plan_id = self.env['product.pricelist'].browse(self.env.context.get('pricelist_id')).availability_plan_id.id
        pms_property_ids = [self.env.context.get('pms_property_id')] or self.env['pms.property'].search([]).ids
        sql = """
            SELECT
            row_number() over() id,
            dpr.date,
            dpr.property_id pms_property_id,
            dpr.room_type_id,
            COUNT(l.id) busy_rooms,
            COUNT(dpr.room_id) total_rooms,
            COUNT(dpr.room_id) - COUNT(l.id) real_avail,
            COALESCE(r.max_avail, dpr.default_max_avail) max_avail,
            COALESCE(r.quota, dpr.default_quota) quota
            FROM
                (SELECT d.date, pr.property_id, pr.default_pricelist_id, pr.room_type_id, pr.room_id,
                        pr.default_max_avail, pr.default_quota
                 FROM (	SELECT (CURRENT_DATE + date ) date
                        FROM generate_series(date '%s' - CURRENT_DATE, date '%s' - CURRENT_DATE) date
                ) d,
                (SELECT p.id property_id, p.default_pricelist_id, r.room_type_id, r.id room_id,
                        rt.default_max_avail, rt.default_quota
                 FROM pms_property p
                 INNER JOIN pms_room r ON r.pms_property_id = p.id
                 INNER JOIN pms_room_type rt ON rt.id = r.room_type_id) pr
                ) dpr
                LEFT JOIN pms_reservation_line l ON l.room_id = dpr.room_id AND l.date = dpr.date
                LEFT JOIN pms_availability_plan_rule r ON r.date = dpr.date AND r.pms_property_id = dpr.property_id
                AND r.room_type_id = dpr.room_type_id
                AND r.availability_plan_id = %s
            WHERE dpr.property_id IN %s
            GROUP BY dpr.room_type_id, dpr.date, dpr.property_id,
            COALESCE(r.max_avail, dpr.default_max_avail),
            COALESCE(r.quota, dpr.default_quota)
        """ % (
                date_from,
                date_to,
                avail_plan_id or 'NULL',
                str(pms_property_ids).replace('[', '(').replace(']', ')'),
            )
        print(sql)

        return sql
