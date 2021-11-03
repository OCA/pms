from odoo import fields, models


class PmsDoorInvitation(models.Model):
    _name = "pms.door.invitation"
    _description = "Noukee door invitation"

    starts_at = fields.Datetime(string="Invitation date start")
    ends_at = fields.Datetime(string="Invitation date end")
    reservation_id = fields.Many2one(
        string="reservation",
        comodel_name="pms.reservation",
    )
    door_id = fields.Many2one(
        comodel_name="pms.door",
        string="Door Id",
    )

    # NOUKEE FIELDS
    pin = fields.Integer(string="PIN CODE")
    invitation_link = fields.Char(string="Invitation noukee link")
    noukee_invitation_id = fields.Char(string="Noukee Invitation Id")
