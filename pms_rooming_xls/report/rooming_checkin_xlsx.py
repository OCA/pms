# Copyright 2020 Commitsun.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class RoomingCheckinXlsx(models.AbstractModel):
    _name = "report.pms_rooming_xls.rooming_export_xlsx"
    _description = "Rooming list"
    _inherit = "report.report_xlsx.abstract"

    def _get_ws_params(self, wb, data, folios):
        CheckinPartner = self.env["pms.checkin.partner"]
        checkin_template = {
            "code": {
                "header": {
                    "value": "Code",
                },
                "data": {
                    "value": self._render("checkin.identifier"),
                },
                "width": 10,
                "hidden": True,
            },
            "folio": {
                "header": {
                    "value": "Folio",
                },
                "data": {
                    "type": "string",
                    "value": self._render("checkin.folio_id.name"),
                },
                "width": 10,
            },
            "room": {
                "header": {
                    "value": "Room",
                },
                "data": {
                    "value": self._render("checkin.reservation_id.rooms"),
                },
                "width": 20,
            },
        }
        wanted_list = ["code", "folio", "room"]
        for field_str in self.env["pms.checkin.partner"]._checkin_partner_fields():
            render_field_str = (
                "checkin." + field_str + " if checkin." + field_str + " else ''"
            )
            checkin_template[field_str] = {
                "header": {
                    "value": CheckinPartner._fields[field_str].string,
                },
                "data": {
                    "value": self._render(render_field_str) or "",
                },
                "width": 10,
            }
            wanted_list.append(field_str)
        ws_params = {
            "ws_name": "Rooming",
            "generate_ws_method": "_roomlist_report",
            "wanted_list": wanted_list,
            "col_specs": checkin_template,
        }

        return [ws_params]

    def _roomlist_report(self, workbook, ws, ws_params, data, checkins):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        FORMATS["format_ws_reservation_group"] = workbook.add_format(
            {"bg_color": "#D8D8D8", "align": "left"}
        )

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_left"],
        )
        ws.freeze_panes(row_pos, 0)
        reservation_id = False
        format_row = FORMATS["format_tcell_left"]
        for checkin in checkins.sorted("reservation_id"):
            if checkin.reservation_id.id != reservation_id:
                reservation_id = checkin.reservation_id.id
                format_row = (
                    FORMATS["format_ws_reservation_group"]
                    if format_row == FORMATS["format_tcell_left"]
                    else FORMATS["format_tcell_left"]
                )
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "checkin": checkin,
                },
                default_format=format_row,
            )
