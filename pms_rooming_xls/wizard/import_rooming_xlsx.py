# Copyright 2020 Commitsun.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import tempfile
from collections import OrderedDict

import xlrd

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ImportRoomingXlsx(models.TransientModel):

    _name = "import.rooming.xlsx"
    _description = "Rooming Import"

    name = fields.Char("File name")
    file = fields.Binary("File")
    type = fields.Selection([("xlsx", "XLSX")], default="xlsx", string="File type.")

    def import_rooming(self):
        self.ensure_one()
        if self.type == "xlsx":
            CheckinPartner = self.env["pms.checkin.partner"]
            checkin_fields = CheckinPartner._checkin_partner_fields()
            if not self.file or not self.name.lower().endswith(
                (
                    ".xls",
                    ".xlsx",
                )
            ):
                raise ValidationError(_("Please Select an .xls file to Import"))
            temp_path = tempfile.gettempdir()
            file_data = base64.decodestring(self.file)
            fp = open(temp_path + "/xsl_file.xls", "wb+")
            fp.write(file_data)
            fp.close()
            wb = xlrd.open_workbook(temp_path + "/xsl_file.xls")
            data_list = []
            header_list = []
            headers_dict = {}
            roomlist = []
            for sheet in wb.sheets():
                # Checkin data xlsx
                for rownum in range(sheet.nrows):
                    if rownum == 0:
                        header_list = [x for x in sheet.row_values(rownum)]
                        headers_dict = {
                            "identifier": header_list.index("Code"),
                            "folio_id": header_list.index("Folio"),
                            "reservation_id": header_list.index("Room"),
                        }
                        for header in header_list:
                            for field_str in checkin_fields:
                                if CheckinPartner._fields[field_str].string == header:
                                    headers_dict[field_str] = header_list.index(header)
                                    break
                    if rownum >= 1:
                        data_list.append(sheet.row_values(rownum))
                count = 1
                for row in data_list:
                    count += 1
                    checkin_dict = OrderedDict()
                    folio = self.env["pms.folio"].search(
                        [("name", "=", row[headers_dict["folio_id"]])]
                    )
                    reservation = self.env["pms.reservation"].search(
                        [
                            ("folio_id", "=", folio.id),
                            ("rooms", "=", row[headers_dict["reservation_id"]]),
                        ]
                    )
                    checkin_dict["folio_id"] = folio.id
                    checkin_dict["reservation_id"] = reservation.id
                    if not (reservation and folio):
                        raise ValidationError(
                            _("Not found reservation (%s)"),
                            row[headers_dict["reservation_id"]],
                        )
                    for key, value in headers_dict.items():
                        if key in ("reservation_id", "folio_id"):
                            continue
                        checkin_dict[key] = row[value]
                    roomlist.append(checkin_dict)
                self.env["pms.checkin.partner"].import_room_list_json(
                    json.dumps(roomlist)
                )
