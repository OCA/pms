# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
        # If Wubook status is 7 (Wubook modification) the folio state is not changed
        if binding.wubook_status in ("3", "5", "6") and binding.state != "cancel":
            binding.odoo_id.action_cancel()
        elif binding.wubook_status in ("1", "2", "4") and binding.state == "cancel":
            binding.odoo_id.with_context(confirm_all_reservations=True).action_confirm()

        # TODO: move get_all_items action_cancel here
        # binding.reservation_ids.filtered(lambda x: x['wubook_status'] == '5').action_cancel()

        # Pre payment Folio
        if binding.payment_gateway_fee > 0:
            folio = binding.odoo_id
            # REVIEW: avoid duplicate payment
            if folio.payment_ids:
                return
            # Wubook Pre payment
            if (
                folio.channel_type_id
                == binding.backend_id.backend_type_id.child_id.direct_channel_type_id
            ):
                journal = binding.backend_id.wubook_journal_id
            # OTAs Pre payment
            else:
                journal = binding.backend_id.backend_journal_ota_ids.filtered(
                    lambda x: x.agency_id.id == folio.agency_id.id
                ).journal_id
            if not journal:
                raise NotImplementedError(
                    _("Not configure journal payments to %s OTA")
                    % (folio.agency_id.name,)
                )
            folio.do_payment(
                journal,
                journal.suspense_account_id,
                self.env.user,
                binding.payment_gateway_fee,
                folio,
                reservations=False,
                services=False,
                partner=folio.partner_id,
                date=folio.last_checkout,
            )

    def _create(self, model, values):
        """ Create the Internal record """
        return super()._create(
            model.with_context(mail_create_nosubscribe=True, force_overbooking=True),
            values,
        )

    def _update(self, binding, values):
        """ Update an Internal record """
        return super()._update(
            binding.with_context(mail_create_nosubscribe=True, force_overbooking=True),
            values,
        )
