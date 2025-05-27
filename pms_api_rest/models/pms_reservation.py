from odoo import api, models


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PmsReservation, self).create(vals_list)
        for record in records:
            record._portal_ensure_token()
        return records

    def build_reservation_lines_cmds(self, reservation, reservation_lines):
        cmds = []
        existing_reservation_line_ids = []
        for reservation_line in reservation_lines:
            reservation_line_vals = {}
            # search reservation line record
            reservation_line_record = self.env["pms.reservation.line"].search(
                [
                    ("date", "=", reservation_line.date),
                    ("reservation_id", "=", reservation.id)
                ]
            )
            # add reservation line record id to existing_reservation_line_ids
            if reservation_line_record:
                existing_reservation_line_ids.append(reservation_line_record.id)

            # date
            if reservation_line.date is not None:
                if not reservation_line_record or reservation_line.date != str(reservation_line_record.date):
                    reservation_line_vals.update({"date": reservation_line.date})
            # price
            if reservation_line.price is not None:
                if not reservation_line_record or round(reservation_line.price, 2) != round(reservation_line_record.price, 2):
                    reservation_line_vals.update({"price": reservation_line.price})
            # discount
            if reservation_line.discount is not None:
                if not reservation_line_record or round(reservation_line.discount, 2) != round(reservation_line_record.discount, 2):
                    reservation_line_vals.update({"discount": reservation_line.discount})
            # roomId
            if reservation_line.roomId is not None:
                if not reservation_line_record or reservation_line.roomId != reservation_line_record.room_id.id:
                    reservation_line_vals.update({"room_id": reservation_line.roomId})
            # isReselling
            if reservation_line.isReselling is not None:
                if not reservation_line_record or reservation_line.isReselling != reservation_line_record.is_reselling:
                    reservation_line_vals.update({"is_reselling": reservation_line.isReselling})

            # add reservation lines to modify/create cmds
            if reservation_line_vals:
                if not reservation_line_record:
                    cmds.append((0, 0, reservation_line_vals))
                else:
                    cmds.append((1, reservation_line_record.id, reservation_line_vals))

        # remove old reservation lines
        for reservation_line_to_remove in reservation.reservation_line_ids.filtered(
                lambda x: x.id not in existing_reservation_line_ids
        ):
            cmds.append((2, reservation_line_to_remove.id))
        return cmds

    def build_reservation_services_cmds(self, reservation_record, services, board_service_id):
        cmds, existing_service_ids = self.env['pms.folio'].build_creation_update_services_cmds(services)

        # remove board services if board_service_id is 0
        if board_service_id == 0:
            for board_service_to_remove in reservation_record.service_ids.filtered(lambda x: x.is_board_service):
                cmds.append((2, board_service_to_remove.id))

        # iterate existing services to remove the ones not in the request
        for service_to_remove in reservation_record.service_ids.filtered(lambda x: x.id not in existing_service_ids):
            cmds.append((2, service_to_remove.id))
        return cmds
