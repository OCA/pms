# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import uuid

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.connector_pms_wubook.controllers.main import WUBOOK_PUSH_BASE_URLS

_logger = logging.getLogger(__name__)


class ChannelWubookBackend(models.Model):
    _name = "channel.wubook.backend"
    _inherit = "connector.backend"
    _inherits = {"channel.backend": "parent_id"}
    _description = "Channel Wubook PMS Backend"

    parent_id = fields.Many2one(
        comodel_name="channel.backend",
        string="Parent Channel Backend",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "backend_parent_uniq",
            "unique(parent_id)",
            "Only one backend child is allowed for each generic backend.",
        ),
    ]

    # connection data
    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)

    url = fields.Char(
        string="Url", default="https://wired.wubook.net/xrws/", required=True
    )
    property_code = fields.Char(string="Property code", required=True)
    pkey = fields.Char(string="PKey", required=True)

    security_token = fields.Char(string="Security Token", required=False)

    pricelist_external_id = fields.Integer(string="Parity Pricelist ID", required=True)

    # push
    def generate_security_key(self):
        for rec in self:
            rec.security_token = uuid.uuid4().hex

    def set_push_url(self):
        for rec in self:
            base_url = self.env["ir.config_parameter"].get_param("web.base.url")
            url = urls.url_join(
                urls.url_join(base_url, WUBOOK_PUSH_BASE_URLS["reservations"]),
                rec.security_token,
            )
            with rec.work_on("channel.wubook.pms.folio") as work:
                adapter = work.component(usage="backend.adapter")
            adapter.push_activation(url, test=1)

    # room type
    def import_room_types(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.pms.room.type"].with_delay().import_data(
                backend_record=rec
            )

    def export_room_types(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.pms.room.type"].with_delay().export_data(
                backend_record=rec
            )

    # room type class
    def import_room_type_classes(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.pms.room.type.class"].with_delay().import_data(
                backend_record=rec
            )

    def export_room_types_classes(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.pms.room.type.class"].with_delay().export_data(
                backend_record=rec
            )

    # pricelist
    pricelist_date_from = fields.Date("Pricelist Date From")
    pricelist_date_to = fields.Date("Pricelist Date To")
    pricelist_ids = fields.Many2many(
        comodel_name="product.pricelist",
        relation="wubook_backend_pricelist_rel",
        column1="backend_id",
        column2="pricelist_id",
        domain=[("pricelist_type", "=", "daily")],
    )
    # TODO: add logic to control this and filter the rooms by the current property
    pricelist_room_type_ids = fields.Many2many(
        comodel_name="pms.room.type",
        relation="wubook_backend_pricelist_room_type_rel",
        column1="backend_id",
        column2="room_type_id",
    )

    def import_pricelists(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            if rec.pricelist_date_to < rec.pricelist_date_from:
                raise UserError(_("Date to must be greater than date from"))
            rec.env["channel.wubook.product.pricelist"].with_delay().import_data(
                rec,
                rec.pricelist_date_from,
                rec.pricelist_date_to,
                rec.pricelist_ids,
                rec.pricelist_room_type_ids,
            )

    def export_pricelists(self, *args, **kwargs):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.product.pricelist"].with_delay(
                *args, **kwargs
            ).export_data(backend_record=rec)

    # availability plan
    plan_date_from = fields.Date("Availability Plan Date From")
    plan_date_to = fields.Date("Availability Plan Date To")
    # TODO: add logic to control this and filter the rooms by the current property
    plan_room_type_ids = fields.Many2many(
        comodel_name="pms.room.type",
        relation="wubook_backend_plan_room_type_rel",
        column1="backend_id",
        column2="room_type_id",
    )
    plan_ids = fields.Many2many(
        comodel_name="pms.availability.plan",
        relation="wubook_backend_plan_availability_plan_rel",
        column1="backend_id",
        column2="availability_plan_id",
    )

    def import_availability_plans(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            if rec.plan_date_to < rec.plan_date_from:
                raise UserError(_("Date to must be greater than date from"))
            rec.env["channel.wubook.pms.availability.plan"].with_delay().import_data(
                rec,
                rec.plan_date_from,
                rec.plan_date_to,
                rec.plan_room_type_ids,
            )

    def export_availability_plans(self, *args, **kwargs):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.pms.availability.plan"].with_delay(
                *args, **kwargs
            ).export_data(backend_record=rec)

    # availability
    avail_date_from = fields.Date("Availability Date From")
    avail_date_to = fields.Date("Availability Date To")
    # TODO: add logic to control this and filter the rooms by the current property
    avail_room_type_ids = fields.Many2many(
        comodel_name="pms.room.type",
        relation="wubook_backend_avail_room_type_rel",
        column1="backend_id",
        column2="room_type_id",
    )

    def export_availability(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            if rec.avail_date_to < rec.avail_date_from:
                raise UserError(_("Date to must be greater than date from"))
            rec.env["channel.wubook.pms.availability"].with_delay().export_data(
                rec,
                rec.avail_date_from,
                rec.avail_date_to,
                rec.avail_room_type_ids,
            )

    # property availability
    def export_property_availability(self, *args, **kwargs):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            rec.env["channel.wubook.pms.property.availability"].with_delay(
                *args, **kwargs
            ).export_data(backend_record=rec)

    # folio
    folio_date_arrival_from = fields.Date(string="Arrival Date From")
    folio_date_arrival_to = fields.Date(string="Arrival Date To")
    folio_mark = fields.Boolean(string="Mark")
    folio_reservation_code = fields.Integer(string="Reservation Code")

    def import_folios(self):
        if self.user_id:
            self = self.with_user(self.user_id)
        for rec in self:
            if rec.folio_reservation_code:
                rec.env["channel.wubook.pms.folio"].with_delay().import_record(
                    rec, rec.folio_reservation_code
                )
            else:
                if rec.folio_date_arrival_to < rec.folio_date_arrival_from:
                    raise UserError(_("Date to must be greater than date from"))
                rec.env["channel.wubook.pms.folio"].with_delay().import_data(
                    rec,
                    rec.folio_date_arrival_from,
                    rec.folio_date_arrival_to,
                    rec.folio_mark,
                )

    # scheduler
    @api.model
    def _scheduler_export(self, interval=1, count=1):
        """
        :param interval: minutes
        :param count: number of executions for every interval

        Examples: interval=1 and num=12 -> execute 12 times every minute
                  interval=60 and num=6 -> execute 6 times every hour

        IF this is called using Odoo Cron job, the interval must be
        the same as the interval execution defined in job
        """
        interval_sec = interval * 60
        now = fields.Datetime.now()
        for backend in self.env["channel.wubook.backend"].search([]):
            if backend.user_id:
                backend = backend.with_user(self.user_id)
            for i in range(0, interval_sec, int(interval_sec / count)):
                eta = fields.Datetime.add(now, seconds=i)
                backend.export_property_availability(eta=eta)
            backend.export_availability_plans()
            backend.export_pricelists()
