from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        pms_properties = env["pms.property"].search([])
        for pms_property in pms_properties:
            if not pms_property.sequence_id:
                pms_property.sequence_id = env["ir.sequence"].create(
                    {
                        "name": "sequence for property: " + pms_property.name,
                        "code": "property." + str(pms_property.id),
                        "padding": 3,
                    }
                )
