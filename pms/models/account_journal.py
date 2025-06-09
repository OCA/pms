from odoo import _, api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        ondelete="restrict",
        relation="account_journal_pms_property_rel",
        column1="account_journal_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    allowed_pms_payments = fields.Boolean(
        string="For manual payments",
        help="Use to pay for reservations",
    )
    avoid_autoinvoice_downpayment = fields.Boolean(
        help="Avoid autoinvoice downpayment",
        default=False,
    )
    is_simplified_invoice = fields.Boolean(
        string="Simplified invoice",
        help="Use to simplified invoice",
        compute="_compute_is_simplified_invoice",
        readonly=False,
        store=True,
    )
    allowed_room_ids = fields.Many2many(
        string="Rooms Filter allowed",
        comodel_name="pms.room",
        relation="account_journal_allow_room_rel",
        column1="account_journal_id",
        column2="room_id",
        help="Room to filter the room in the reservation",
        compute="_compute_allowed_room_ids",
    )
    room_filter_ids = fields.Many2many(
        string="Apply Rooms",
        comodel_name="pms.room",
        relation="account_journal_room_rel",
        column1="account_journal_id",
        column2="room_id",
        help="Room to filter the room types in the reservation",
        domain="[('id', 'in', allowed_room_ids)]",
    )

    @api.depends("pms_property_ids", "pms_property_ids.journal_simplified_invoice_id")
    def _compute_is_simplified_invoice(self):
        self.is_simplified_invoice = False
        for journal in self:
            if journal.id in journal.pms_property_ids.mapped(
                "journal_simplified_invoice_id.id"
            ):
                journal.is_simplified_invoice = True

    @api.depends("pms_property_ids")
    def _compute_allowed_room_ids(self):
        for journal in self:
            if not journal.pms_property_ids:
                journal.allowed_room_ids = self.env["pms.room"].search([]).ids
            else:
                journal.allowed_room_ids = (
                    self.env["pms.room"]
                    .search([("pms_property_id", "in", journal.pms_property_ids.ids)])
                    .ids
                )

    @api.constrains("is_simplified_invoice")
    def _check_pms_properties_simplified_invoice(self):
        for journal in self:
            if (
                journal.is_simplified_invoice
                and journal.id
                in journal.pms_property_ids.mapped("journal_normal_invoice_id.id")
            ):
                raise models.ValidationError(
                    _(
                        "The journal %(journal)s is used for normal "
                        "invoices in the properties: %(properties)s",
                        journal=journal.name,
                        properties=", ".join(journal.pms_property_ids.mapped("name")),
                    )
                )
            if (
                not journal.is_simplified_invoice
                and journal.id
                in journal.pms_property_ids.mapped("journal_simplified_invoice_id.id")
            ):
                raise models.ValidationError(
                    _(
                        "The journal %(journal)s is used for simplified "
                        "invoices in the properties: %(properties)s",
                        journal=journal.name,
                        properties=", ".join(journal.pms_property_ids.mapped("name")),
                    )
                )
