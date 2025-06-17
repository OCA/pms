from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_pay_on_reservation = fields.Boolean(
        related="pos_config_id.pay_on_reservation", readonly=False
    )
    pos_pay_on_reservation_method_id = fields.Many2one(
        related="pos_config_id.pay_on_reservation_method_id", readonly=False
    )
    pos_reservation_allowed_propertie_ids = fields.Many2many(
        related="pos_config_id.reservation_allowed_propertie_ids", readonly=False
    )
    pos_close_session_allowed = fields.Boolean(
        related="pos_config_id.close_session_allowed", readonly=False
    )
    pos_cash_in_out_allowed = fields.Boolean(
        related="pos_config_id.cash_in_out_allowed", readonly=False
    )
    pos_cash_move_partner = fields.Boolean(
        related="pos_config_id.cash_move_partner", readonly=False
    )
