from odoo import api, fields, models

from ..wizards.traveller_report import CREATE_OPERATION_CODE, DELETE_OPERATION_CODE


class PmsReservation(models.Model):
    _inherit = "pms.reservation"
    ses_communication_ids = fields.One2many(
        string="SES Communications",
        help="Communications related to this reservation",
        comodel_name="pms.ses.communication",
        inverse_name="reservation_id",
    )
    is_ses = fields.Boolean(
        string="Is SES",
        readonly=True,
        compute="_compute_is_ses",
        store=True,
    )
    ses_status_reservation = fields.Selection(
        string="SES Status",
        help="Status of the reservation in SES",
        selection=[
            ("not_applicable", "Not Applicable"),
            ("to_send", "Pending Notification"),
            ("to_process", "Pending Processing"),
            ("error_create", "Error Creating"),
            ("error_sending", "Error Sending"),
            ("error_processing", "Error Processing"),
            ("processed", "Processed"),
        ],
        compute="_compute_ses_status_reservation",
    )
    ses_status_traveller_report = fields.Selection(
        string="SES Status traveller",
        help="Status of the traveller report in SES",
        selection=[
            ("not_applicable", "Not Applicable"),
            ("incomplete", "Incomplete checkin data"),
            ("to_send", "Pending Notification"),
            ("to_process", "Pending Processing"),
            ("error_create", "Error Creating"),
            ("error_sending", "Error Sending"),
            ("error_processing", "Error Processing"),
            ("processed", "Processed"),
        ],
        compute="_compute_ses_status_traveller_report",
    )

    @api.depends("pms_property_id", "preferred_room_id")
    def _compute_is_ses(self):
        for record in self:
            if (
                record.preferred_room_id
                and record.preferred_room_id.institution_independent_account
                and record.preferred_room_id.institution == "ses"
            ):
                record.is_ses = True
            else:
                record.is_ses = record.pms_property_id.institution == "ses"

    def _compute_ses_status_reservation(self):
        for record in self:
            if record.pms_property_id.institution != "ses":
                record.ses_status_reservation = "not_applicable"
                continue
            communication = record.ses_communication_ids.filtered(
                lambda x: x.entity == "RH"
            )
            if len(communication) > 1:
                # get the last communication
                communication = communication.sorted(key=lambda x: x.create_date)[-1]
            record.ses_status_reservation = (
                communication.state if communication else "error_create"
            )

    def _compute_ses_status_traveller_report(self):
        for record in self:
            if record.pms_property_id.institution != "ses":
                record.ses_status_traveller_report = "not_applicable"
                continue
            communication = record.ses_communication_ids.filtered(
                lambda x: x.entity == "PV"
            )
            if len(communication) > 1:
                # get the last communication
                communication = communication.sorted(key=lambda x: x.create_date)[-1]
            record.ses_status_traveller_report = (
                communication.state if communication else "error_create"
            )

    @api.model
    def create_communication(
        self, reservation_id, operation, entity, communication_id_to_cancel=False
    ):
        reservation = self.env["pms.reservation"].browse(reservation_id)
        self.env["pms.ses.communication"].create(
            {
                "reservation_id": reservation_id,
                "operation": operation,
                "entity": entity,
                "room_id": reservation.preferred_room_id.id,
                "communication_id_to_cancel": communication_id_to_cancel,
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        reservations = super().create(vals_list)
        for reservation in reservations:
            if (
                reservation.pms_property_id.institution == "ses"
                and reservation.reservation_type != "out"
            ):
                self.create_communication(reservation.id, CREATE_OPERATION_CODE, "RH")
        return reservations

    @api.model
    def create_communication_after_update_reservation(self, reservation, vals):
        state_changed = "state" in vals and (
            (vals["state"] != "cancel" and reservation.state == "cancel")
            or (vals["state"] == "cancel" and reservation.state != "cancel")
        )
        check_changed = (
            any(
                key in vals and vals[key] != getattr(reservation, key)
                for key in ["adults", "checkin", "checkout"]
            )
            and reservation.state != "cancel"
        )

        if state_changed or check_changed:
            # delete all pending notifications
            self.env["pms.ses.communication"].search(
                [
                    ("reservation_id", "=", reservation.id),
                    ("state", "=", "to_send"),
                    ("entity", "=", "RH"),
                ]
            ).unlink()

            # last communication
            last_communication = self.env["pms.ses.communication"].search(
                [
                    ("reservation_id", "=", reservation.id),
                    ("entity", "=", "RH"),
                ],
                order="id desc",
                limit=1,
            )

            if state_changed:
                if (
                    vals["state"] == "cancel"
                    and last_communication.operation == CREATE_OPERATION_CODE
                ):
                    self.create_communication(
                        reservation.id,
                        DELETE_OPERATION_CODE,
                        "RH",
                        last_communication.id,
                    )
                elif vals["state"] != "cancel" and (
                    last_communication.operation == DELETE_OPERATION_CODE
                    or not last_communication
                ):
                    self.create_communication(
                        reservation.id, CREATE_OPERATION_CODE, "RH"
                    )
            elif check_changed:
                if last_communication.operation == CREATE_OPERATION_CODE:
                    self.create_communication(
                        reservation.id,
                        DELETE_OPERATION_CODE,
                        "RH",
                        last_communication.id,
                    )
                self.create_communication(reservation.id, CREATE_OPERATION_CODE, "RH")

    def write(self, vals):
        for record in self:
            if record.is_ses and record.reservation_type != "out":
                self.create_communication_after_update_reservation(record, vals)
        return super().write(vals)
