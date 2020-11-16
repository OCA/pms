from odoo import fields, models


class ReservationWizard(models.TransientModel):
    _name = "pms.reservation.wizard"
    allowed_rooms = fields.One2many("pms.room", compute="_compute_allowed_rooms")
    options = fields.Many2one("pms.room", string="Room")

    def _compute_allowed_rooms(self):
        for record in self:
            record.allowed_rooms = self._context.get("rooms_available")

    def unify(self):
        if self.options:
            for line in (
                self.env["pms.reservation"]
                .search([("id", "=", self._context.get("active_id"))])
                .reservation_line_ids
            ):
                line.room_id = self.options
