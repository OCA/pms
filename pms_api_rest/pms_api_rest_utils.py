from odoo import _
from odoo.exceptions import AccessDenied
from odoo.http import request


def url_image_pms_api_rest(model, record_id, field):
    pms_api_check_access(
        user=request.env.user, records=request.env[model].sudo().browse(record_id)
    )
    rt_image_attach = (
        request.env["ir.attachment"]
        .sudo()
        .search(
            [
                ("res_model", "=", model),
                ("res_id", "=", record_id),
                ("res_field", "=", field),
            ]
        )
    )
    if rt_image_attach and not rt_image_attach.access_token:
        rt_image_attach.generate_access_token()
    result = (
        request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        + "/web/image/%s?access_token=%s"
        % (rt_image_attach.id, rt_image_attach.access_token)
        if rt_image_attach
        else False
    )
    return result if result else ""


def pms_api_check_access(user, records=False):
    if not records or user.has_group("base.group_public"):
        return
    # Property access check
    if records._name == "pms.property":
        record_ids = records.ids
        user_property_ids = user.pms_property_ids.ids
        if not all(record_id in user_property_ids for record_id in record_ids):
            properties_not_allowed = records.filtered(
                lambda record: record.id not in user_property_ids
            )
            raise AccessDenied(
                _("You are not allowed to access these properties. %s")
                % properties_not_allowed.mapped("name")
            )
    elif hasattr(records, "pms_property_id"):
        pms_property_ids = [
            record.pms_property_id.id for record in records if record.pms_property_id
        ]
        if pms_property_ids:
            user_property_ids = user.pms_property_ids.ids
            if not any(prop_id in user_property_ids for prop_id in pms_property_ids):
                properties_not_allowed = records.filtered(
                    lambda record: record.pms_property_id.id not in user_property_ids
                )
                raise AccessDenied(
                    _("You are not allowed to access this properties. %s")
                    % properties_not_allowed.mapped("pms_property_id.name")
                )
    elif hasattr(records, "pms_property_ids"):
        pms_property_ids = [
            prop_id for record in records for prop_id in record.pms_property_ids.ids
        ]
        if pms_property_ids:
            user_property_ids = user.pms_property_ids.ids
            if not any(prop_id in user_property_ids for prop_id in pms_property_ids):
                properties_not_allowed = records.filtered(
                    lambda record: any(
                        prop_id not in user_property_ids
                        for prop_id in record.pms_property_ids.ids
                    )
                )
                raise AccessDenied(
                    _("You are not allowed to access this properties. %s")
                    % properties_not_allowed.mapped("pms_property_ids.name")
                )
    # Other access check
    # ...
