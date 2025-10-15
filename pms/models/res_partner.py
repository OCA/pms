# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    reservations_count = fields.Integer(
        string="Number of Reservations",
        help="Number of reservations of the partner",
        compute="_compute_reservations_count",
    )
    folios_count = fields.Integer(
        string="Number of Folios",
        help="Number of folios of the partner",
        compute="_compute_folios_count",
    )
    is_agency = fields.Boolean(help="Indicates if the partner is an agency")
    sale_channel_id = fields.Many2one(
        string="Sale Channel",
        help="The sale channel of the partner",
        comodel_name="pms.sale.channel",
        domain=[("channel_type", "=", "indirect")],
        ondelete="restrict",
        index=True,
    )
    default_commission = fields.Integer(string="Commission", help="Default commission")
    commission_type = fields.Selection(
        selection=[
            ("included", "Commission Included in Price"),
            ("subtract", "Commission Subtracts from Price"),
        ],
        help="""
        If select subtract commission, for automatic import of reservations,
        the commission is calculated as price - (price * commission / 100)
        """,
        default="included",
    )
    apply_pricelist = fields.Boolean(
        help="Indicates if agency pricelist is applied to his reservations",
    )
    invoice_to_agency = fields.Selection(
        string="Invoice Agency",
        help="Indicates if agency invoices partner",
        selection=[
            ("never", "Never"),
            ("manual", "Manual"),
            ("always", "Always"),
        ],
        default="never",
        required=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="res_partner_pms_property_rel",
        column1="res_partner_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    pms_checkin_partner_ids = fields.One2many(
        string="Checkin Partners",
        help="Associated checkin partners",
        comodel_name="pms.checkin.partner",
        inverse_name="partner_id",
    )
    pms_reservation_ids = fields.One2many(
        string="Reservations",
        help="Associated reservation",
        comodel_name="pms.reservation",
        inverse_name="partner_id",
    )
    pms_folio_ids = fields.One2many(
        string="Folios",
        help="Associated Folios",
        comodel_name="pms.folio",
        inverse_name="partner_id",
    )

    comment = fields.Text(
        tracking=True,
    )
    invoicing_policy = fields.Selection(
        help="""The invoicing policy of the partner,
         set Property to user the policy configured in the Property""",
        selection=[
            ("property", "Property Policy Invoice"),
            ("manual", "Manual"),
            ("checkout", "From Checkout"),
            ("month_day", "Month Day Invoice"),
        ],
        default="property",
    )
    invoicing_month_day = fields.Integer(
        help="The day of the month to invoice",
    )
    margin_days_autoinvoice = fields.Integer(
        string="Days from Checkout",
        help="Days from Checkout to generate the invoice",
    )

    def _compute_reservations_count(self):
        # Return reservation with partner included in reservation and/or checkin
        pms_reservation_obj = self.env["pms.reservation"]
        for record in self:
            checkin_reservation_ids = (
                self.env["pms.checkin.partner"]
                .search([("partner_id", "=", record.id)])
                .mapped("reservation_id.id")
            )
            record.reservations_count = pms_reservation_obj.search_count(
                [
                    "|",
                    (
                        "partner_id.id",
                        "child_of",
                        record.id if isinstance(record.id, int) else False,
                    ),
                    ("id", "in", checkin_reservation_ids),
                ]
            )

    def action_partner_reservations(self):
        self.ensure_one()
        checkin_reservation_ids = (
            self.env["pms.checkin.partner"]
            .search([("partner_id", "=", self.id)])
            .mapped("reservation_id.id")
        )
        reservations = self.env["pms.reservation"].search(
            [
                "|",
                (
                    "partner_id.id",
                    "child_of",
                    self.id if isinstance(self.id, int) else False,
                ),
                ("id", "in", checkin_reservation_ids),
            ]
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms.open_pms_reservation_form_tree_all"
        )
        if len(reservations) > 1:
            action["domain"] = [("id", "in", reservations.ids)]
        elif len(reservations) == 1:
            form_view = [(self.env.ref("pms.pms_reservation_view_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = reservations.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        if len(self) == 1:
            context = {
                "default_partner_id": self.id,
                "default_user_id": self.user_id.id,
            }
            action["context"] = context
        return action

    def _compute_folios_count(self):
        # Return folios count with partner included in folio and/or folio checkins
        pms_folio_obj = self.env["pms.folio"]
        for record in self:
            checkin_folio_ids = (
                self.env["pms.checkin.partner"]
                .search([("partner_id", "=", record.id)])
                .mapped("folio_id.id")
            )
            record.folios_count = pms_folio_obj.search_count(
                [
                    "|",
                    (
                        "partner_id.id",
                        "=",
                        record.id if isinstance(record.id, int) else False,
                    ),
                    ("id", "in", checkin_folio_ids),
                ]
            )

    def action_partner_folios(self):
        self.ensure_one()
        checkin_folio_ids = (
            self.env["pms.checkin.partner"]
            .search([("partner_id", "=", self.id)])
            .mapped("folio_id.id")
        )
        folios = self.env["pms.folio"].search(
            [
                "|",
                (
                    "partner_id.id",
                    "child_of",
                    self.id if isinstance(self.id, int) else False,
                ),
                ("id", "in", checkin_folio_ids),
            ]
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms.open_pms_folio1_form_tree_all"
        )
        if len(folios) > 1:
            action["domain"] = [("id", "in", folios.ids)]
        elif len(folios) == 1:
            form_view = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = folios.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        if len(self) == 1:
            context = {
                "default_partner_id": self.id,
                "default_user_id": self.user_id.id,
            }
            action["context"] = context
        return action

    @api.constrains("is_agency", "sale_channel_id")
    def _check_is_agency(self):
        for record in self:
            if record.is_agency and not record.sale_channel_id:
                raise models.ValidationError(_("Sale Channel must be entered"))
            if record.is_agency and record.sale_channel_id.channel_type != "indirect":
                raise models.ValidationError(
                    _("Sale Channel for an agency must be indirect")
                )
            if not record.is_agency and record.sale_channel_id:
                record.sale_channel_id = None

    @api.model
    def _get_key_fields(self):
        key_fields = super()._get_key_fields()
        key_fields.extend(["document_number"])
        return key_fields

    def _check_enought_invoice_data(self):
        self.ensure_one()
        # Template to be inherited by localization modules
        return True

    @api.constrains("is_agency", "property_product_pricelist")
    def _check_agency_pricelist(self):
        if any(
            record.is_agency and not record.property_product_pricelist.is_pms_available
            for record in self
        ):
            raise models.ValidationError(
                _(
                    """
                    Agency must have a PMS pricelist, please review the
                    pricelists configuration (%(pricelists)s) to allow it for PMS,
                    or the pricelist selected for the agencies: %(agencies)s
                    """
                )
                % {
                    "pricelists": ",".join(
                        self.mapped("property_product_pricelist.name")
                    ),
                    "agencies": "".join(self.mapped("name")),
                }
            )
