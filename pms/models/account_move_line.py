# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Fields declaration
    folio_line_id = fields.Many2one(
        string="Folio Lines",
        help="The folio lines in the account move lines",
        copy=False,
        comodel_name="folio.sale.line",
    )
    folio_ids = fields.Many2many(
        string="Folios",
        comodel_name="pms.folio",
        relation="payment_folio_rel",
        column1="move_id",
        column2="folio_id",
    )
    name_changed_by_user = fields.Boolean(
        help="Indicates if the line's name have been changed by user",
        string="Custom label",
        readonly=False,
        default=False,
        store=True,
        compute="_compute_name_changed_by_user",
    )
    move_line_to_delete = fields.Boolean(
        help="Indicates if the line should be automatically deleted to maintain"
        " consistency with the lines with which it is associated",
        default=False,
        readonly=True,
        store=False,
        compute="_compute_delete_this_move_line",
    )

    @api.depends("quantity")
    def _compute_delete_this_move_line(self):
        for record in self:
            record.move_line_to_delete = False

            if (
                record.folio_line_id.service_line_ids
                and record.folio_line_id.is_board_service
            ):
                num_nights = len(
                    record.folio_line_id.folio_sale_line_master_ids.reservation_line_ids
                )
                adults = record.folio_line_id.reservation_id.adults
                max_allowed_qty = num_nights * adults
                if record.quantity > max_allowed_qty:
                    raise ValidationError(
                        _(
                            "Max qty for this line is: %s",
                            max_allowed_qty,
                        )
                    )
                elif record.quantity % adults:
                    raise ValidationError(
                        _(
                            "Qty of board service lines should be consistent with its nights"
                        )
                    )
                elif not (record.quantity % adults) and record.quantity != max_allowed_qty:
                    raise ValidationError(
                        _(
                            "Inconsistent qty for related night/s."
                        )
                    )
            elif record.folio_line_id.reservation_line_ids:
                fsl_related = self.env['folio.sale.line'].search(
                    [
                        ("folio_sale_line_master_ids", "in", record.folio_line_id.id)
                    ]
                )
                print(fsl_related.ids)
                aml_related = self.env['account.move.line'].search(
                    [
                        ("folio_line_id", "in", fsl_related.ids)
                    ]
                )
                nights = record.quantity
                adults = record.folio_line_id.reservation_id.adults
                aml_related.quantity = nights * adults

    @api.depends("name")
    def _compute_name_changed_by_user(self):
        for record in self:
            # if not record._context.get("auto_name"):
            if not self._context.get("auto_name"):
                record.name_changed_by_user = True
            else:
                record.name_changed_by_user = False

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
    )

    @api.depends("quantity")
    def _compute_name(self):
        for record in self:
            record.name = self.env["folio.sale.line"].generate_folio_sale_name(
                record.folio_line_id.reservation_id,
                record.product_id,
                record.folio_line_id.service_id,
                record.folio_line_id.reservation_line_ids,
                record.folio_line_id.service_line_ids,
                qty=record.quantity,
            )
            # TODO: check why this code doesn't work
            # if not record.name_changed_by_user:
            #   record.with_context(auto_name=True).name = self
            #       .env["folio.sale.line"].generate_folio_sale_name(
            #           record.folio_line_id.service_id,
            #           record.folio_line_id.reservation_line_ids,
            #           record.product_id,
            #           qty=record.quantity)
            #     record.with_context(auto_name=True)
            #       ._compute_name_changed_by_user()

    def _copy_data_extend_business_fields(self, values):
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values["folio_line_id"] = self.folio_line_id.id

    # @api.constrains("quantity")
    # def check_value(self):
    #     for record in self:
    #         adults = record.folio_line_id.reservation_id.adults
    #         if (
    #             record.folio_line_id.service_line_ids
    #             and record.folio_line_id.is_board_service
    #         ):
    #             allowed_qty = (
    #                 len(
    #                     record.folio_line_id.folio_sale_line_master_ids.reservation_line_ids
    #                 )
    #                 * adults
    #             )
    #             if record.quantity != allowed_qty:
    #                 raise ValidationError(
    #                     _(
    #                         "Qty for this line should be: %s",
    #                         allowed_qty,
    #                     )
    #                 )
