import datetime
import json

import requests
import time

from odoo import api, fields, models


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    invitation_ids = fields.One2many(
        string="Reservation invitation ids",
        comodel_name="pms.door.invitation",
        readonly=False,
        store=True,
        inverse_name="reservation_id",
    )

    @api.model
    def create(self, vals):
        record = super(PmsReservation, self).create(vals)
        if not record.splitted:
            for door in record.preferred_room_id.door_ids:
                door_id = door.id
                headers = {
                    "Authorization": "Bearer " + record.pms_property_id.noukee_jwt
                }
                response = requests.post(
                    "https://cloud.noukee.com/api/v1/sites/"
                    + record.pms_property_id.noukee_site_id
                    + "/invitations",
                    headers=headers,
                    json={
                        "doorId": door.noukee_id,
                        "startsAt": int(datetime.datetime.timestamp(record.checkin_datetime)*1000),
                        "endsAt": int(datetime.datetime.timestamp(record.checkout_datetime)*1000),
                    },
                )

                if response.status_code == 200:
                    self.env["pms.door.invitation"].create(
                        {
                            "starts_at": record.checkin_datetime,
                            "ends_at": record.checkout_datetime,
                            "reservation_id": record.id,
                            "door_id": door_id,
                            "pin": response.json()["pin"],
                            "invitation_link": response.json()["link"],
                            "noukee_invitation_id": response.json()["invitationId"],
                        }
                    )
        else:
            # TODO: manage splitted reservations (check commented reference below)
            pass
            # record.reservation_line_ids.mapped("room_id")

        return record

    # def create(self, vals):
    #     for record in self:
    #         if not record.splitted:
    #             invitations = self.env["pms.door.invitation"].search(
    #                 [
    #                     "reservation_id",
    #                     "=",
    #                     record.id,
    #                 ]
    #             )
    #             for invitation in invitations:
    #                 if (
    #                     invitation.door_id not in record.preferred_room_id.door_ids
    #                     or invitation.starts_at != record.checkin_datetime
    #                     or invitation.ends_at != record.checkout_datetime
    #                 ):
    #                     response = requests.delete(
    #                         "https://cloud.noukee.com/api/v1/sites/"
    #                         + record.pms_property_id.noukee_site_id
    #                         + "/invitations/"
    #                         + invitation.invitation_id
    #                     )
    #                     invitation.unlink()
    #                     if response.status_code != 200:
    #                         raise ValidationError("No funciona el PMS")
    #
    #             for door in record.preferred_room_id.door_ids:
    #                 if door.id not in invitations.door_id.ids:
    #                     headers = {"Authorization": "Bearer " + record.pms_property_id.noukee_jwt}
    #                     response = requests.post(
    #                         "https://cloud.noukee.com/api/v1/sites/"
    #                         + record.pms_property_id.noukee_site_id
    #                         + "/invitations",
    #                         headers=headers,
    #                         data={
    #                             "doorId": door.noukee_id,
    #                             "startsAt": record.checkin_datetime.microsecond / 1000,
    #                             "endsAt": record.checkout_datetime.microsecond / 1000,
    #                         },
    #                     )
    #                     if response.status_code == 200:
    #                         new_invitation = self.env["pms.door.invitation"].create(
    #                             {
    #                                 "starts_at": record.checkin_datetime.microsecond
    #                                 / 1000,
    #                                 "ends_at": record.checkout_datetime.microsecond
    #                                 / 1000,
    #                                 "reservation_id": record.id,
    #                                 "door_id": door.id,
    #                                 "pin": response.content["pin"],
    #                                 "invitation_link": response.content["link"],
    #                                 "noukee_invitation_id": response.content[
    #                                     "invitationId"
    #                                 ],
    #                             }
    #                         )
    #         else:
    #             # crear tantas invitacioens como room_ids
    #             record.reservation_line_ids.mapped("room_id")
