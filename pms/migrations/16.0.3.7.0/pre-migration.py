from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    _deleted_xml_records = [
        "pms.view_partner_property_form",
        "pms.autoinvoicing_folios",
        "pms.autoinvoicing_downpayments",
        "pms.autoinvoice_folio_job_function",
        "pms.autovalidate_invoice_folio_job_function",
        "pms.channel_autoinvoicing_folios",
    ]
    openupgrade.delete_records_safely_by_xml_id(env, _deleted_xml_records)
