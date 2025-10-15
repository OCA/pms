import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from ..wizards.traveller_report import CREATE_OPERATION_CODE

CODE_SPAIN = "ES"
CODE_NIF = "D"
CODE_NIE = "N"

_logger = logging.getLogger(__name__)


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    support_number = fields.Char(
        string="Support number",
        help="ID support number",
        readonly=False,
        store=True,
        compute="_compute_partner_document_data",
    )

    ses_partners_relationship = fields.Selection(
        selection=[
            ("AB", "Abuelo/a"),
            ("BA", "Bisabuelo/a"),
            ("BN", "Bisnieto/a"),
            ("CD", "Cuñado/a"),
            ("CY", "Cónyuge"),
            ("HJ", "Hijo/a"),
            ("HR", "Hermano"),
            ("NI", "Nieto/a"),
            ("PM", "Padre o Madre"),
            ("SB", "Sobrino/a"),
            ("SG", "Suegro/a"),
            ("TI", "Tío/a"),
            ("YN", "Yerno o Nuera"),
            ("TU", "Tutor/a"),
            ("OT", "Otro"),
        ],
        required=False,
    )

    ses_related_checkin_partner_id = fields.Many2one(
        comodel_name="pms.checkin.partner",
        string="Related checkin partner",
        required=False,
    )

    def _compute_partner_document_data(self):
        res = super()._compute_partner_document_data()
        for record in self:
            last_update_document = record.partner_id.id_numbers.filtered(
                lambda x, record=record: x.write_date
                == max(record.partner_id.id_numbers.mapped("write_date"))
            )
            if (
                not record.support_number
                and last_update_document
                and last_update_document[0].support_number
            ):
                record.support_number = last_update_document[0].support_number
        return res

    def _checkin_mandatory_fields(self):
        self.ensure_one()
        mandatory_fields = super()._checkin_mandatory_fields()
        mandatory_fields.extend(
            [
                "birthdate_date",
                "gender",
                "nationality_id",
                "street",
                "city",
                "country_id",
                "zip",
            ]
        )

        if self.birthdate_date:
            # Checkins with age greater than 14 must have an identity document
            if self.birthdate_date <= fields.Date.today() - relativedelta(years=14):
                mandatory_fields.extend(
                    [
                        "document_number",
                        "document_type",
                        "document_country_id",
                    ]
                )
            # Checkins with age lower than 18 must have a relationship
            # with another checkin partner
            if self.birthdate_date > fields.Date.today() - relativedelta(years=18):
                mandatory_fields.extend(
                    [
                        "ses_partners_relationship",
                        "ses_related_checkin_partner_id",
                    ]
                )

        if self.country_id and self.country_id.code == CODE_SPAIN:
            mandatory_fields.extend(
                [
                    "state_id",
                ]
            )
        if (
            self.document_type
            and self.document_type.code
            and self.document_type.code == CODE_NIF
        ):
            mandatory_fields.extend(
                [
                    "lastname2",
                ]
            )
        if self.document_type and self.document_type.code in [CODE_NIF, CODE_NIE]:
            mandatory_fields.extend(
                [
                    "support_number",
                ]
            )
        return mandatory_fields

    @api.model
    def _checkin_manual_fields(self, country=False):
        manual_fields = super()._checkin_manual_fields()
        manual_fields.extend(
            [
                "support_number",
                "ses_partners_relationship",
                "ses_related_checkin_partner_id",
            ]
        )
        return manual_fields

    def get_document_vals(self):
        vals = super().get_document_vals()
        vals["support_number"] = self.support_number
        return vals

    def write(self, vals):
        result = super().write(vals)
        for record in self:
            if (
                "state" in vals
                and record.reservation_id.pms_property_id.institution == "ses"
                and record.state == "onboard"
            ):
                previous_incomplete_traveller_communication = self.env[
                    "pms.ses.communication"
                ].search(
                    [
                        ("reservation_id", "=", record.reservation_id.id),
                        ("entity", "=", "PV"),
                        ("operation", "=", CREATE_OPERATION_CODE),
                        ("state", "=", "incomplete"),
                    ]
                )
                if not previous_incomplete_traveller_communication:
                    previous_incomplete_traveller_communication = self.env[
                        "pms.ses.communication"
                    ].create(
                        {
                            "reservation_id": record.reservation_id.id,
                            "operation": CREATE_OPERATION_CODE,
                            "entity": "PV",
                            "state": "incomplete",
                        }
                    )
                # check if all checkin partners in the reservation are onboard
                if (
                    all(
                        [
                            checkin.state == "onboard"
                            for checkin in record.reservation_id.checkin_partner_ids
                        ]
                    )
                    and len(record.reservation_id.checkin_partner_ids)
                    == record.reservation_id.adults
                ):
                    previous_incomplete_traveller_communication.state = "to_send"

        return result
