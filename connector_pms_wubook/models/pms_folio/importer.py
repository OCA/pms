# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2.extensions import AsIs

from odoo import _, fields

from odoo.addons.component.core import Component


class ChannelWubookPmsFolioDelayedBatchImporter(Component):
    _name = "channel.wubook.pms.folio.delayed.batch.importer"
    _inherit = "channel.wubook.delayed.batch.importer"

    _apply_on = "channel.wubook.pms.folio"


class ChannelWubookPmsFolioDirectBatchImporter(Component):
    _name = "channel.wubook.pms.folio.direct.batch.importer"
    _inherit = "channel.wubook.direct.batch.importer"

    _apply_on = "channel.wubook.pms.folio"


class ChannelWubookPmsFolioImporter(Component):
    _name = "channel.wubook.pms.folio.importer"
    _inherit = "channel.wubook.importer"

    _apply_on = "channel.wubook.pms.folio"

    def _import_dependencies(self, external_data, external_fields):
        self._import_dependency(
            {x["room_id"] for x in external_data.get("reservations", [])},
            "channel.wubook.pms.room.type",
        )
        self._import_dependency(
            {x["board"] for x in external_data.get("reservations", []) if x["board"]},
            "channel.wubook.pms.board.service",
        )
        self._import_dependency(
            {x["rate_id"] for x in external_data.get("reservations", [])},
            "channel.wubook.product.pricelist",
        )
        self._import_dependency(
            [
                r
                for r in external_data["modified_reservations"]
                if r != external_data["reservation_code"]
            ],
            "channel.wubook.pms.folio",
        )

    def _after_import(self, binding):
        folio = binding.odoo_id
        # If Wubook status is 7 (Wubook modification) the folio state is not changed
        if binding.wubook_status in ("3", "5", "6") and binding.state != "cancel":
            # If folio has draft invoice, cancel invoices:
            draft_invoices = folio.move_ids.filtered(lambda x: x.state == "draft")
            if draft_invoices:
                draft_invoices.button_cancel()
                draft_invoices.unlink()
            folio.action_cancel()
        elif binding.wubook_status in ("1", "2", "4") and binding.state == "cancel":
            folio.with_context(confirm_all_reservations=True).action_confirm()

        # TODO: move get_all_items action_cancel here
        # binding.reservation_ids.filtered(lambda x: x['wubook_status'] == '5').action_cancel()

        # Pre payment Folio
        if binding.payment_gateway_fee > 0:
            # REVIEW: If the agency has configured invoice the agency manually,
            # and a payment from the agency enters, we preset in the folio invoice the agency to true
            # (p.e. Expedia Collect)
            if folio.agency_id and folio.agency_id.invoice_to_agency == "manual":
                folio.invoice_to_agency = True
            # Wubook Pre payment
            if (
                folio.sale_channel_origin_id
                == binding.backend_id.backend_type_id.child_id.direct_channel_type_id
            ):
                journal = binding.backend_id.wubook_journal_id
            # Other OTAs Pre payment
            else:
                journal = binding.backend_id.backend_journal_ota_ids.filtered(
                    lambda x: x.agency_id.id == folio.agency_id.id
                ).journal_id
                # auto update OTAs payment on modified/cancelled reservations
                ota_payments = folio.payment_ids.filtered(
                    lambda x: x.journal_id.id == journal.id
                )
                if ota_payments:
                    if folio.state == "cancel" and folio.amount_total == 0:
                        ota_payments.action_draft()
                        ota_payments.action_cancel()
                        folio.sudo().message_post(
                            body=_(
                                "The folio and the OTA payment have been cancelled."
                            ),
                            subtype_id=self.env.ref("mail.mt_note").id,
                            email_from=self.env.user.partner_id.email_formatted
                            or folio.pms_property_id.email_formatted,
                        )
                    elif binding.payment_gateway_fee != sum(
                        ota_payments.mapped("amount")
                    ):
                        ota_payments.action_draft()
                        ota_payments[0].amount = binding.payment_gateway_fee
                        ota_payments[0].action_post()
                        if len(ota_payments) > 1:
                            ota_payments[1:].action_cancel()
                        folio.sudo().message_post(
                            body=_(
                                "The amount of the payment has been updated to %s by OTA modification"
                                % binding.payment_gateway_fee
                            ),
                            subtype_id=self.env.ref("mail.mt_note").id,
                            email_from=self.env.user.partner_id.email_formatted
                            or folio.pms_property_id.email_formatted,
                        )
            # We omit those payments from agencies that that have already been registered in previous imports,
            # that the total of the folio is zero, or that do not have a journal configured
            if (
                not folio.payment_ids.filtered(lambda p: p.state == "posted")
                and folio.amount_total > 0
                and journal
            ):
                payment_amount = (
                    binding.payment_gateway_fee
                    if binding.payment_gateway_fee <= folio.amount_total
                    else folio.amount_total
                )
                folio.do_payment(
                    journal,
                    journal.suspense_account_id,
                    self.env.user,
                    payment_amount,
                    folio,
                    reservations=False,
                    services=False,
                    partner=folio.partner_id,
                )

        # REVIEW: mark actual_write_date to now
        # in availability and force to update Wubook avail changes
        # (Wubook add/delete avail by itself)
        dates = folio.mapped("reservation_ids.reservation_line_ids.date")
        avails = self.env["channel.wubook.pms.availability"].search(
            [
                ("backend_id", "=", binding.backend_id.id),
                ("date", ">=", min(dates)),
                ("date", "<=", max(dates)),
                ("room_type_id", "in", folio.mapped("reservation_ids.room_type_id.id")),
            ]
        )
        query = (
            'UPDATE "channel_wubook_pms_availability" SET "actual_write_date"=%s WHERE id IN %%s'
            % (AsIs("(now() at time zone 'UTC')"),)
        )
        cr = self.env.cr
        for sub_ids in cr.split_for_in_conditions(
            set(avails.filtered(lambda i: i.date >= fields.Date.today()).ids)
        ):
            cr.execute(query, [sub_ids])

    def _create(self, model, values):
        """Create the Internal record"""
        return super()._create(
            model.with_context(mail_create_nosubscribe=True, force_overbooking=True),
            values,
        )

    def _update(self, binding, values):
        """Update an Internal record"""
        return super()._update(
            binding.with_context(mail_create_nosubscribe=True, force_overbooking=True),
            values,
        )
