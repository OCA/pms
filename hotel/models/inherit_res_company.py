# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    additional_hours = fields.Integer('Additional Hours',
                                      help="Provide the min hours value for \
                                        check in, checkout days, whatever \
                                        the hours will be provided here based \
                                        on that extra days will be \
                                        calculated.")
    default_cancel_policy_days = fields.Integer('Cancelation Days')
    default_cancel_policy_percent = fields.Integer('Percent to pay')
