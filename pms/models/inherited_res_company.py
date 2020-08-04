# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Fields declaration
    pms_property_ids = fields.One2many("pms.property", "company_id", "Properties")
    # TODO: need extra explanation or remove otherwise
    # additional_hours = fields.Integer('Additional Hours',
    #                                   help="Provide the min hours value for \
    #                                   check in, checkout days, whatever \
    #                                   the hours will be provided here based \
    #                                   on that extra days will be \
    #                                   calculated.")
    # TODO: move the text to the default template for confirmed reservations
    # cardex_warning = fields.Text(
    #     'Warning in Cardex',
    #     default="Time to access rooms: 14: 00h. Departure time: \
    #             12: 00h. If the accommodation is not left at that time, \
    #             the establishment will charge a day's stay according to \
    #             current rate that day",
    #     help="Notice under the signature on the traveler's ticket.")
