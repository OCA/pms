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
    )

    @api.depends("pms_property_id")
    def _compute_is_ses(self):
        for record in self:
            record.is_ses = record.pms_property_id.institution == "ses"

    @api.model
    def create_communication(self, reservation_id, operation, entity):
        self.env["pms.ses.communication"].create(
            {
                "reservation_id": reservation_id,
                "operation": operation,
                "entity": entity,
            }
        )

    @api.model
    def create(self, vals):
        reservation = super(PmsReservation, self).create(vals)
        if reservation.pms_property_id.institution == "ses":
            self.create_communication(reservation.id, CREATE_OPERATION_CODE, "RH")
        return reservation

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
                        reservation.id, DELETE_OPERATION_CODE, "RH"
                    )
                elif (
                    vals["state"] != "cancel"
                    and last_communication.operation == DELETE_OPERATION_CODE
                ):
                    self.create_communication(
                        reservation.id, CREATE_OPERATION_CODE, "RH"
                    )
            elif check_changed:
                if last_communication.operation == CREATE_OPERATION_CODE:
                    self.create_communication(
                        reservation.id, DELETE_OPERATION_CODE, "RH"
                    )
                self.create_communication(reservation.id, CREATE_OPERATION_CODE, "RH")

    def write(self, vals):
        for record in self:
            if record.pms_property_id.institution == "ses":
                self.create_communication_after_update_reservation(record, vals)
        return super(PmsReservation, self).write(vals)
