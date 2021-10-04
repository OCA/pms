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
    # board_services_invoiced_related_ids = fields.One2many(
    #     string="Related board services",
    #     help="Related invoice lines with board services",
    #     compute="_compute_board_services_invoiced_related",
    # )
    # board_service_related_quantity = fields.Float(
    #     string="Quantity",
    #     help="Board service has automativ quantity based on adults and room nights invoiced",
    #     digits="Product Unit of Measure",
    #     compute="_compute_board_service_quantity",
    #     store="True",
    # )
    update_board_move_lines = fields.Boolean(
        help="Indicates if the board related lines should be automatically updated to maintain"
        " consistency with the lines with which it is associated",
        store=True,
        readonly=True,
        compute="_compute_update_board_move_lines",
    )

    def _compute_board_services_invoiced_related_ids(self):
        self.board_services_invoiced_related_ids = False
        for record in self.filtered("folio_line_ids"):
            fsl_dependants = self.env["folio.sale.line"].search(
                [("folio_sale_line_master_ids", "in", record.folio_line_id.id)]
            )
            if fsl_dependants:
                record.board_services_invoiced_related_ids = [
                    (
                        6,
                        0,
                        fsl_dependants.move_line_ids.filtered(
                            lambda l: l.move_id == record.move_id
                        ).ids,
                    )
                ]

    @api.depends("quantity")
    def _compute_update_board_move_lines(self):
        self.update_board_move_lines = False
        for record in self.filtered("folio_line_id"):
            # Dont allowed modify directly cuantity in board services invoice lines related
            if (
                record.folio_line_id.service_line_ids
                and record.folio_line_id.is_board_service
            ):
                allowed_qty = sum(
                    record.folio_line_id.folio_sale_line_master_ids.move_line_ids.filtered(
                        lambda l: l.move_id == record.move_id
                    ).quantity
                )
                if record.quantity != allowed_qty:
                    raise ValidationError(
                        _(
                            """This line is a board service related with a room, please,
                            update the room cuantity"""
                        )
                    )
            elif record.folio_line_id.reservation_line_ids:
                fsl_dependant = self.env["folio.sale.line"].search(
                    [("folio_sale_line_master_ids", "in", record.folio_line_id.id)]
                )
                # qty_attempt_number_services = (
                #     record.quantity * record.folio_line_id.reservation_id.adults
                # )
                for fsl_d in fsl_dependant:
                    current_invoice_lines_related = fsl_d.move_line_ids.filtered(
                        lambda l: l.move_id == record.move_id
                    )
                    sum(current_invoice_lines_related.cuantity)

                    # If board service is related with more than this invoice,
                    # the related quantity...
                    # else:
                    #     other_nights = fsl_d.folio_sale_line_master_ids.filtered(
                    #         lambda x: x.move_id != record.move_id
                    #     )
                    #     other_invoiced_nights = sum(
                    #         fsl_d.folio_sale_line_master_ids.filtered(
                    #             lambda s: s.record.folio_line_id.id
                    #         ).qty_invoiced
                    #     )
                    #     fsl_qty = fsl_d.product_uom_qty - (
                    #       other_invoiced_nights * record.folio_line_id.reservation_id.adults
                    #     )

                    # if fsl_qty > qty_attempt_number_services:
                    #     raise UserError(
                    #         _(
                    #             """Cannot increase nights related to board services.
                    #              Need to create a new line."""
                    #         )
                    #     )
                    # elif fsl_qty < qty_attempt_number_services:
                    #     # ¿ delete / create / update ?
                    #     # recover board services invoice lines related
                    #     board_move_lines = fsl_d.invoice_lines.filtered(
                    #       lambda l: l.move_id == record.move_id
                    #     )
                    #     if qty_attempt_number_services == 0

                    #     fsl_d.move_id.write(
                    #         {
                    #             1,
                    #             fsl_d.id,
                    #             {
                    #                 "quantity": qty_attempt_number_services,
                    #             },
                    #         }
                    #     )

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
