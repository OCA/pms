# HOOTEL PROJECT MODULES [![Build Status](https://travis-ci.org/hootel/hootel.svg?branch=11.0)](https://travis-ci.org/hootel/hootel) [![codecov](https://codecov.io/gh/hootel/hootel/branch/11.0/graph/badge.svg)](https://codecov.io/gh/hootel/hootel) ![Unstable](https://img.shields.io/badge/stability-unstable-yellow.svg)


**IMPORTANT:**
  - Set time zone of users that use the calendar

**MODULES:**
  - [ ] hotel: Base module (Manage Rooms, Reservations, Services, Customers, Mailing, Invoicing, ...)
  - [ ] hotel_calendar: Adds calendar for manage hotel reservations and rooms configuration
  - [ ] hotel_calendar_channel_connector: Unify 'hotel_channel_connector' and 'hotel_calendar' modules
  - [ ] hotel_channel_connector: Base Channel Connector (Using Odoo Connector)
  - [ ] hotel_channel_connector_wubook: Wubook API Implementation
  - [ ] hotel_node_helper: Configure a node as a helper to serve and get information from a master one
  - [ ] hotel_node_master: Configure a node as a master

**HOW WORKS?**
  - The idea is... the hotel sell 'rooms types' and the customer is assigned to one 'real room'.
  - The folio have all reservation lines, used services, etc..
