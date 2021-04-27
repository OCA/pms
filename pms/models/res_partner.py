# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    reservations_count = fields.Integer(
        string="Reservations",
        help="Number of reservations of the partner",
        compute="_compute_reservations_count",
    )
    folios_count = fields.Integer(
        string="Folios",
        help="Number of folios of the partner",
        compute="_compute_folios_count",
    )
    is_agency = fields.Boolean(
        string="Is Agency", help="Indicates if the partner is an agency"
    )
    sale_channel_id = fields.Many2one(
        string="Sale Channel",
        help="The sale channel of the partner",
        comodel_name="pms.sale.channel",
        domain=[("channel_type", "=", "indirect")],
        ondelete="restrict",
    )
    default_commission = fields.Integer(string="Commission", help="Default commission")
    apply_pricelist = fields.Boolean(
        string="Apply Pricelist",
        help="Indicates if agency pricelist is applied to his reservations",
    )
    invoice_to_agency = fields.Boolean(
        string="Invoice Agency",
        help="Indicates if agency invoices partner",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="res_partner_pms_property_rel",
        column1="res_partner_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    company_id = fields.Many2one(
        check_pms_properties=True,
    )

    def _compute_reservations_count(self):
        # TODO: recuperar las reservas de los folios del partner
        pms_reservation_obj = self.env["pms.reservation"]
        for record in self:
            record.reservations_count = pms_reservation_obj.search_count(
                [
                    (
                        "partner_id.id",
                        "child_of",
                        record.id if isinstance(record.id, int) else False,
                    )
                ]
            )

    def _compute_folios_count(self):
        pms_folio_obj = self.env["pms.folio"]
        for record in self:
            record.folios_count = pms_folio_obj.search_count(
                [
                    (
                        "partner_id.id",
                        "=",
                        record.id if isinstance(record.id, int) else False,
                    )
                ]
            )

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        if not args:
            args = []
        domain = [
            "|",
            ("phone", operator, name),
            ("mobile", operator, name),
        ]
        partners = self.search(
            domain + args,
            limit=limit,
        )
        res = partners.name_get()
        if limit:
            limit_rest = limit - len(partners)
        else:
            limit_rest = limit
        if limit_rest or not limit:
            args += [("id", "not in", partners.ids)]
            res += super(ResPartner, self).name_search(
                name, args=args, operator=operator, limit=limit_rest
            )
        return res

    @api.constrains("is_agency", "sale_channel_id")
    def _check_is_agency(self):
        for record in self:
            if record.is_agency and not record.sale_channel_id:
                raise models.ValidationError(_("Sale Channel must be entered"))
            if not record.is_agency and record.sale_channel_id:
                record.sale_channel_id = None

    # REVIEW: problems with odoo demo data
    # @api.constrains("mobile", "email")
    # def _check_duplicated(self):
    #     for record in self:
    #         partner, field = record._search_duplicated()
    #         if partner:
    #             raise models.ValidationError(
    #                 _(
    #                     "Partner %s found with same %s (%s)",
    #                     partner.name,
    #                     partner._fields[field].string,
    #                     getattr(record, field),
    #                 )
    #             )

    def _search_duplicated(self):
        self.ensure_one()
        partner = False
        for field in self._get_key_fields():
            if getattr(self, field):
                partner = self.search(
                    [(field, "=", getattr(self, field)), ("id", "!=", self.id)]
                )
                if partner:
                    field = field
        return partner, field

    @api.model
    def _get_key_fields(self):
        return []
