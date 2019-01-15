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

Scenario 1 (TS100)
==================
:Prerequisites: You have a new WuBook account ready to use **without** Rooms,
 neither Rate plans or Restrictions plans.

Test TC101
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
 - You can bind Rooms, Rate Plans and Restriction Plans.

:Remarks: You can not Import Rooms, neither Availability, Restriction Plans and Restriction Values,
 Pricelist Plans and Pricelist Values because it is a new WuBook Account.

:Status: Test Passed.

Test TC102
----------

:Summary: Bind **Room Types** to the Hotel Channel Connector Backend.

:Requirement: TC101

:Procedure: Add the Hotel Channel Connector Backend to the Room Type.

:Result:
 - The Room Type is created in WuBook.
 - You can modify the following fields: ``name``, ``capacity``, ``price``, ``availability``,
   ``scode``, ``dboard``, ``rtype``.

:Remarks: Creating a Room Type in WuBook will `make available`
 a **default WuBook Restrictions Plan** named **WuBook Restrictions** with ``rpid=0`` and
 a **default WuBook Rate Plan** named **WuBook Parity** with ``pid=0``.

:Status: Test Passed.

Test TC103
----------

:Summary: Bind **Restriction Plans** to the Hotel Channel Connector Backend.

:Requirement: TC101

:Procedure: Add the Hotel Channel Connector Backend to the Restriction Plan.

:Result:
 - The Restriction Plan is created in WuBook.
 - You can modify the following fields: ``name``.

:Remarks: Creating a Restriction Plan in WuBook will `create`
 a **new WuBook Restrictions Plan** with ``rpid!=0``.

:Status: Test Passed.

Test TC104
----------

:Summary: Add **Restrictions**

:Requirement: TC101, TC102, TC103

:Procedure: Add Restriction Items into the Restriction Plan.

:Result: The Restriction Plan is updated in WuBook.

:Remarks: For this test you need Push Restrictions in the Hotel Channel Backends Export form.

:Status: Test Passed.

Test TC105
----------

:Summary: Delete **Restrictions**

:Requirement: TC101, TC102, TC103

:Procedure: Delete a Restriction Items in Odoo.

:Result: The Restriction Plan is updated in WuBook.

:Remarks: For this test you need Push Restrictions in the Hotel Channel Backends Export form.

:Status: Test Failed.

:Reason: Restrictions remain in WuBook.

Test TC106
----------

:Summary: Bind **Product Pricelist** to the Hotel Channel Connector Backend.

:Requirement: TC101

:Procedure: Add the Hotel Channel Connector Backend to the Product Pricelist.

:Result:
 - The Product Pricelist is created in WuBook.
 - You can modify the following fields: ``name``.

:Remarks: Creating a Product Pricelist in WuBook will `create` a
 **new WuBook Rate Plan** with ``pid!=0``.

:Status: Test Passed.

Test TC107
----------

:Summary: Add Room Type **Price**

:Requirement: TC101, TC102, TC105

:Procedure: Add Room Type Unit Price into the Rate Plan.

:Result: The Rate Plan is updated in WuBook.

:Remarks: For this test use the Massive Changes Wizard.

:Status: Test Passed.

Test TC108
----------

:Summary: Add **Availability** to the Hotel Room Type.

:Requirement: TC101, TC102, T103

:Procedure: Add the availability to the Room Type using a Hotel Channel Connector Backend.

:Result: The Availability is created in WuBook.

:Remarks: The availability is updated in WuBook after Push Availability.

:Status: Test Passed.

Test TC109
----------

:Summary: Delete **Availability** from the Hotel Room Type.

:Requirement: TC101, TC102, T103

:Procedure: Delete Availability Items in Odoo.

:Result: The Restriction Plan is updated in WuBook.

:Remarks: The availability is updated in WuBook after Push Availability.

:Status: Test Failed.

Test TC110
----------

:Summary: Bind the **Restriction Plan** in Odoo to the Hotel Channel Connector Backend
 using ``ID on Channel=0`` will start its **parity** with the default Restriction Plan **in WuBook**.

:Requirement: TC101

:Procedure: Add the Hotel Channel Connector Backend to the Restriction Plan using **``ID on Channel=0``**.

:Result: The Odoo Restriction Plan will be in parity with the
 default WuBook Restrictions Plan with ``rpid=0`` named **WuBook Restrictions**.

:Status: Test Passed.

Test TC111
----------

:Summary: Bind the **Product Pricelist** in Odoo to the Hotel Channel Connector Backend
 will start its **parity** with the default Price Plan **in WuBook**.

:Requirement: TC101

:Procedure: Add the Hotel Channel Connector Backend to the Product Pricelis using **``ID on Channel=0``**.

:Result: The Product Pricelist created in WuBook is in parity with the
 default WuBook Restrictions Plan with ``rpid=0``.

:Status: Unknown.

Test TC112
----------

:Summary: Update any **binded field** in a Room Type will automatically update the corresponding field in **WuBook**.

:Requirement: TC101, TC102

:Procedure: Edit a Room Type and modify the ``name``.

:Result: The name in WuBook is also updated.

:Status: Failed.

:Reason: Some fields (``name``, ``list_price``) are updated `only` if the Hotel Channel Connector Binding is updated.


Scenario 2 (TS002)
==================
:Prerequisites: `Scenario 1 (TS100)`_ Tests passed.

:Summary: This tests review the basic reservation management.

Test TC201
----------

:Summary: **Create** a Reservation **decreases** the Room Type Availability in one in the corresponding Plan in Wubook.

:Procedure: Create a reservation with a room type binded to the Hotel Channel Connector Backend.

:Result: The availability is decreased by one.

:Status: Test Failed.

:Reason: The availability remains the same.

Test TC202
----------

:Summary: **Cancel** a Reservation **increases** the Room Type Availability in one in the corresponding Plan in Wubook.

:Procedure: Cancel a reservation with a room type binded to the Hotel Channel Connector Backend.

:Result: The availability is increased by one.

:Status: Not done yet.

Test TC203
----------

:Summary: **Change** the Room Type in a Reservation **modifies** the Room Type Availability
 in the corresponding Plan in Wubook.

:Procedure: Change the Room Type in a reservation to any room type binded to the Hotel Channel Connector Backend.

:Result: The availability is modified according to the change done.

:Status: Not done yet.

Test TC204
----------

:Summary: **Change** Checkin/Checkout dates in a Reservation **modifies** the Room Type Availability
 in the corresponding Plan in Wubook.

:Procedure: Change the Checkin/Checkout in a reservation with a room type binded to the Hotel Channel Connector Backend.

:Result: The availability is modified according to the change done.

:Status: Not done yet.

Test TC205
----------

:Summary: **Reselling** state in a Reservation **increases** the Room Type Availability
 in the corresponding Plan in Wubook.

:Procedure: Mark a reservation as `reselling` with a room type binded to the Hotel Channel Connector Backend.

:Result: The availability is increased by one.

:Status: Not done yet.