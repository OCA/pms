# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import api, fields, models


class PmsAvailabilityPlanBoardRule(models.Model):
    _name = "pms.availability.plan.board.rule"
    _description = "Board service closing in an availability plan"
    _order = (
        "availability_plan_id, pms_property_id, date_from, write_date desc, id desc"
    )
    _check_pms_properties_auto = True

    availability_plan_id = fields.Many2one(
        string="Availability Plan",
        help="Availability plan whose pricelists the rule applies to",
        required=True,
        index=True,
        comodel_name="pms.availability.plan",
        ondelete="cascade",
        check_pms_properties=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property the rule applies to",
        required=True,
        index=True,
        comodel_name="pms.property",
        ondelete="cascade",
        check_pms_properties=True,
    )
    board_service_id = fields.Many2one(
        string="Board Service",
        help="Board service the rule closes or opens",
        required=True,
        index=True,
        comodel_name="product.template",
        domain="[('is_board_service', '=', True)]",
        ondelete="cascade",
        check_pms_properties=True,
    )
    date_from = fields.Date(
        string="From",
        help="First night the rule applies to",
        required=True,
    )
    date_to = fields.Date(
        string="To",
        help="Last night the rule applies to",
        required=True,
    )
    closed = fields.Boolean(
        help="Whether the board service can't be sold on these nights. "
        "Unchecked, it reopens what an earlier rule closes",
        default=True,
    )

    _sql_constraints = [
        (
            "date_range",
            "CHECK (date_to >= date_from)",
            "The end date must be on or after the start date",
        ),
    ]

    @api.model
    def _resolve_rules(self, availability_plan_id, pms_property_id, date_from, date_to):
        """The rule that decides each night: rules can overlap, and the last
        one written wins.

        TODO: once availability plans inherit from a parent plan, rank the
        rules by the depth of their plan first, and by write_date within it.

        :return: {(board_service_id, date): rule}, a missing key means the
                 board service is open
        """
        rules = self.search(
            [
                ("availability_plan_id", "=", availability_plan_id),
                ("pms_property_id", "=", pms_property_id),
                ("date_from", "<=", date_to),
                ("date_to", ">=", date_from),
            ]
        ).sorted(lambda rule: (rule.write_date, rule.id))
        winners = {}
        for rule in rules:
            night = max(rule.date_from, date_from)
            last_night = min(rule.date_to, date_to)
            while night <= last_night:
                winners[(rule.board_service_id.id, night)] = rule
                night += datetime.timedelta(days=1)
        return winners

    @api.model
    def _get_closed_board_services(
        self, availability_plan_id, pms_property_id, checkin, checkout
    ):
        """Board services closed on any night of a stay"""
        if checkout <= checkin:
            return self.env["product.template"]
        winners = self._resolve_rules(
            availability_plan_id,
            pms_property_id,
            checkin,
            checkout - datetime.timedelta(days=1),
        )
        return self.env["product.template"].browse(
            list(
                {
                    board_id
                    for (board_id, _night), rule in winners.items()
                    if rule.closed
                }
            )
        )
