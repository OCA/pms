from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    document_number = fields.Char(
        help="Host document number",
        readonly=False,
        store=True,
        compute="_compute_partner_document_data",
    )
    document_type = fields.Many2one(
        help="Select a valid document type",
        readonly=False,
        store=True,
        index=True,
        comodel_name="res.partner.id_category",
        compute="_compute_partner_document_data",
        domain="['|', ('country_ids', '=', False),"
        " ('country_ids', 'in', document_country_id)]",
    )
    document_expedition_date = fields.Date(
        string="Expedition Date",
        help="Date on which document_type was issued",
        readonly=False,
        store=True,
        compute="_compute_partner_document_data",
    )

    document_country_id = fields.Many2one(
        string="Document Country",
        help="Country of the document",
        comodel_name="res.country",
        compute="_compute_partner_document_data",
        store=True,
        readonly=False,
    )

    @api.depends("partner_id")
    def _compute_partner_document_data(self):
        for record in self:
            last_update_document = record.partner_id.id_numbers.filtered(
                lambda x, record=record: x.write_date
                == max(record.partner_id.id_numbers.mapped("write_date"))
            )
            if (
                not record.document_number
                and last_update_document
                and last_update_document[0].name
            ):
                record.document_number = last_update_document[0].name
            if (
                not record.document_type
                and last_update_document
                and last_update_document[0].category_id
            ):
                record.document_type = last_update_document[0].category_id
            if (
                not record.document_expedition_date
                and last_update_document
                and last_update_document[0].valid_from
            ):
                record.document_expedition_date = last_update_document[0].valid_from
            if (
                not record.document_country_id
                and last_update_document
                and last_update_document[0].country_id
            ):
                record.document_country_id = last_update_document[0].country_id

    def get_document_vals(self):
        return {
            "name": self.document_number,
            "partner_id": self.partner_id.id,
            "category_id": self.document_type.id,
            "valid_from": self.document_expedition_date,
            "country_id": self.document_country_id.id,
        }

    @api.constrains("document_number", "document_type", "document_country_id")
    def validate_id_number(self):
        """Validate the given ID number
        The method raises an odoo.exceptions.ValidationError if the eval of
        python validation code fails
        """
        for record in self:
            if (
                record.document_number
                and record.document_type
                and record.document_country_id
            ):
                id_number = self.env["res.partner.id_number"].new(
                    {
                        "name": record.document_number,
                        "category_id": record.document_type,
                        "country_id": record.document_country_id,
                    }
                )
                if (
                    self.env.context.get("id_no_validate")
                    or not record.document_type.validation_code
                ):
                    return
                eval_context = record._validation_eval_context(id_number)
                try:
                    safe_eval(
                        record.document_type.validation_code,
                        eval_context,
                        mode="exec",
                        nocopy=True,
                    )
                except Exception as e:
                    raise UserError(
                        _(
                            "Error when evaluating the id_category "
                            "validation code:\n %(name)s \n(%(error)s)",
                            name=self.name,
                            error=e,
                        )
                    ) from e
                if eval_context.get("failed", False):
                    raise ValidationError(
                        _(
                            "%(doc_number)s is not a valid %(doc_type)s identifier",
                            doc_number=record.document_number,
                            doc_type=record.document_type.name,
                        )
                    )

    @api.constrains("document_country_id", "document_type")
    def _check_document_country_id_document_type_consistence(self):
        for record in self:
            if record.document_country_id and record.document_type:
                if (
                    record.document_type.country_ids
                    and record.document_country_id
                    not in record.document_type.country_ids
                ):
                    raise ValidationError(
                        _("Document type and country of document do not match")
                    )

    @api.constrains("document_number")
    def check_document_number(self):
        for record in self:
            if record.partner_id:
                for number in record.partner_id.id_numbers:
                    if record.document_type == number.category_id:
                        if record.document_number != number.name:
                            raise ValidationError(_("Document_type has already exists"))

    @api.model
    def _get_partner_by_document(self, document_number, document_type):
        number = (
            self.sudo()
            .env["res.partner.id_number"]
            .search(
                [
                    ("name", "=", document_number),
                    ("category_id", "=", document_type.id),
                ]
            )
        )
        return (
            self.sudo().env["res.partner"].search([("id", "=", number.partner_id.id)])
        )

    def set_partner_id(self):
        for record in self:
            if not record.partner_id:
                if record.document_number and record.document_type:
                    partner = self._get_partner_by_document(
                        record.document_number, record.document_type
                    )
                    if partner:
                        record.partner_id = partner
                    else:
                        super(PmsCheckinPartner, record).set_partner_id()
        return True

    @api.model
    def _checkin_manual_fields(self, country=False):
        manual_fields = super()._checkin_manual_fields(country=country)
        manual_fields += [
            "document_number",
            "document_type",
            "document_expedition_date",
            "document_country_id",
        ]
        return manual_fields

    def _create_or_update_partner_document(self):
        for record in self:
            document_id = (
                self.sudo()
                .env["res.partner.id_number"]
                .search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("name", "=", record.document_number),
                        ("category_id", "=", record.document_type.id),
                    ],
                    limit=1,
                )
            )
            if document_id:
                document_vals = record.get_document_vals()
                document_id.write(document_vals)
            else:
                document_vals = record.get_document_vals()
                self.env["res.partner.id_number"].create(document_vals)

    def action_on_board(self):
        self._create_or_update_partner_document()
        return super().action_on_board()
