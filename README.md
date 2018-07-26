# HOOTEL PROJECT MODULES [![Build Status](https://travis-ci.org/hootel/hootel.svg?branch=10.0)](https://travis-ci.org/hootel/hootel) [![codecov](https://codecov.io/gh/hootel/hootel/branch/10.0/graph/badge.svg)](https://codecov.io/gh/hootel/hootel) ![Unstable](https://img.shields.io/badge/stability-unstable-yellow.svg)


**IMPORTANT:**
  - Set time zone of users that use the calendar

**MODULES:**
  - [x] hotel: Base module (Inspired by the work of SerpentCS Hotel Module)
  - [x] hotel_calendar: Adds calendar for manage hotel reservations and rooms configuration
  - [x] hotel_calendar_wubook: Unify 'hotel_wubook_prototype' and 'hotel_calendar' modules
  - [x] hotel_data_bi: Export reservations data for Revenue to MyDataBI
  - [x] hotel_l10n_es: Procedures for check-in process in Spain
  - [ ] hotel_wubook: NOTHING... the idea is use Odoo Connector
  - [x] hotel_wubook_prototype: Current implementation of Wubook Connector... sync data with wubook.net account.
  - [ ] hotel_node_slave: Configure a node as a slave to serve and get information from a master one
  - [ ] hotel_node_master: Configure a node as a master
  - [ ] glasof_exporter: Export Odoo data to Glasof xls format
  - [x] hotel_revenue: Export Odoo data for Revenue in xls format
  - [x] cash_daily_report: Export Odoo Payments & Payment Returns to xls format
  - [x] invoice_payments_report: Add payments info in invoices
  - [x] theme_chatter_right: Puts chatter to the right
  - [x] report_qweb_pdf_preview: Adds new report_type to generate pdf and launch preview/print process
  - [x] l10n_es_events_scraper: Gets info about relevant events in Spain

**HOW WORKS?**
  - The idea is... the hotel sell 'virtual rooms' and the customer is assigned to one 'normal room'.
  - The folio have all reservation lines, used services...
