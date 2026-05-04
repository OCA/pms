This module integrates PMS (Property Management System) with the official
Odoo TicketBAI EDI module (``l10n_es_edi_tbai``).

It ensures that invoices issued to the PMS anonymous/various partner
(``pms.various_pms_partner``) are correctly identified as simplified invoices
in the TicketBAI XML submission, so that no recipient data is included in the
XML and the ``FacturaSimplificada`` flag is set to ``S``.

Without this module, simplified invoices created from PMS would fail with
TicketBAI error **B4_2000012** ("Country code is mandatory when ID Type is
not NIF-IVA"), because the system would try to include recipient data for a
partner that has no VAT or country configured.
