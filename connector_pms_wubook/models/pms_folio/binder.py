# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ChannelWubookPmsFolioBinder(Component):
    _name = "channel.wubook.pms.folio.binder"
    _inherit = "channel.wubook.binder"

    _apply_on = "channel.wubook.pms.folio"

    _internal_alt_id = "reservation_origin_code"
    _external_alt_id = "reservation_code"

    def _get_internal_record_alt(self, model_name, values):
        binder = self.component(usage="binder")
        record = binder.to_internal(values['reservation_origin_code'])
        return record.odoo_id
