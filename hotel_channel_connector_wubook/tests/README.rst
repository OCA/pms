==============================
HOTEL CHANNEL CONNECTOR WUBOOK
==============================

The following list define the test to be covered by this module.

Knowledge Base
==============
- WuBook uses a default Restrictions Plan with ``rpid=0`` for the Online Reception restrictions.
- WuBook uses a default Parity Rate Plan with ``pid=0`` for the Online Reception prices.
- You can not define a Parity Restriction Plan for Online Receptions.
- You can define a Parity Rate Plan for Online Receptions.
- Handling Rooms: https://tdocs.wubook.net/wired/rooms.html
- Wired: updating availability https://tdocs.wubook.net/wired/avail.html

Scenario 1 (TS001)
==================
:Prerequisites: You have a new WuBook account ready to use **without** Rooms,
 neither Rate plans, Pricelists or Restrictions plans.

Test TC001
----------

:Summary: **Install** the `Hotel Channel Connector Wubook` module and
 **create** a `Hotel Channel Backend` will bind WuBook as the hotel channel manager.

:Procedure:
 1. Install the ``hotel_channel_connector_wubook`` module.
 2. Create a new Hotel Channel Backend with your WuBook Account Credentials.
 3. Generate a new Channel Service Security Token.

:Result:
 - You can Import OTA's Info.
 - You can Export Availability, Restrictions and Pricelists.
 - You can bind Rooms and Restriction Plans.

:Remarks: You can not Import Rooms, neither Availability, Restriction Plans and Restriction Values,
 Pricelist Plans and Pricelist Values because it is a new WuBook Account.

:Status: Test Passed.

Test TC002
------------

:Summary: Bind **Room Types** to the Hotel Channel Connector Backend.

:Requirement: TC001

:Procedure: Add the Hotel Channel Connector Backend to the Room Type.

:Result:
 - The Room Type is created in WuBook.
 - You can modify the following fields: ``name``, ``capacity``, ``price``, ``availability``,
   ``scode``, ``dboard``, ``rtype``.

:Remarks: Creating a Room Type in WuBook will `make available`
 a **default WuBook Restrictions Plan** with ``rpid=0`` and
 a **default WuBook Price Plan** with ``pid=0``.

:Status: Test Passed.

Test TC003
------------

:Summary: Bind **Restriction Plans** to the Hotel Channel Connector Backend.

:Requirement: TC001

:Procedure: Add the Hotel Channel Connector Backend to the Restriction Plan.

:Result:
 - The Restriction Plan is created in WuBook.
 - You can modify the following fields: ``name``.

:Remarks: Creating a Restriction Plan in WuBook will `create`
 a **new WuBook Restrictions Plan** with ``rpid!=0``.

:Status: Test Passed.

Test TC004
----------

:Summary: Bind **Product Pricelist** to the Hotel Channel Connector Backend.

:Requirement: TC001

:Procedure: Add the Hotel Channel Connector Backend to the Product Pricelist.

:Result:
 - The Product Pricelist is created in WuBook.
 - You can modify the following fields: ``name``.

:Remarks: Creating a Product Pricelist in WuBook will `create` a
 **new Rate WuBook Price Plan** with ``pid != 0``.

:Status: Test Passed.


Test TC005
----------

:Summary: Bind **Availability** to the Hotel Channel Connector Backend.

:Requirement: TC001

:Procedure: Add the Hotel Channel Connector Backend to the Availability.

:Result: The Availability is created in WuBook.

:Status: Unknown.


Test TC006
----------

:Summary: Bind the **default Restriction Plan** in Odoo to the Hotel Channel Connector Backend
 will start its **parity** with the default Restriction Plan **in WuBook**.

:Requirement: TC001

:Procedure: Not defined yet.

:Result:
 - The Odoo Restriction Plan created in WuBook is in parity with the
   default WuBook Restrictions Plan with ``rpid=0``.

:Status: Unknown.

Test TC007
----------

:Summary: Bind the **default Product Pricelist** in Odoo to the Hotel Channel Connector Backend
 will start its **parity** with the default Price Plan **in WuBook**.

:Requirement: TC001

:Procedure: Not defined yet.

:Result:
 - The Product Pricelist created in WuBook is in parity with the
   default WuBook Restrictions Plan with ``rpid=0``.

:Status: Unknown.

Test TC008
----------

:Summary: Update any **binded field** in a Room Type will update the corresponding field in **WuBook**.

:Requirement: TC001, TC002

:Procedure: Edit a Room Type and modify the ``name``.

:Result: The name in WuBook is also updated.

:Status: Failed.

:Reason: The field was not updated in WuBook


