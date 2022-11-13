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
        string="Avoid autoinvoice downpayment",
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

    @api.depends("pms_property_ids", "pms_property_ids.journal_simplified_invoice_id")
    def _compute_is_simplified_invoice(self):
        self.is_simplified_invoice = False
        for journal in self:
            if journal.id in journal.pms_property_ids.mapped(
                "journal_simplified_invoice_id.id"
            ):
                journal.is_simplified_invoice = True

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
                        "The journal %s is used for normal invoices in the properties: %s"
                        % (
                            journal.name,
                            ", ".join(journal.pms_property_ids.mapped("name")),
                        )
                    )
                )
            if (
                not journal.is_simplified_invoice
                and journal.id
                in journal.pms_property_ids.mapped("journal_simplified_invoice_id.id")
            ):
                raise models.ValidationError(
                    _(
                        "The journal %s is used for simplified invoices in the properties: %s"
                        % (
                            journal.name,
                            ", ".join(journal.pms_property_ids.mapped("name")),
                        )
                    )
                )
