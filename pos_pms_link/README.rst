POS PMS LINK
=======================

**Table of contents**

.. contents::
   :local:

Settings
--------

- PMS Service product needs to be avaible in pos (available_in_pos = True) to add it from pms.service.line.
- On pos.config you can mark pay_on_reservation = True to be able to pay with reservations. After that select a pos.payment.method that will be used after selecting the reservation.


Add reservation services to pos.order
-------------------------------------

- While on a pos.order click on the 'Reservation' button. A modal will open, select the desired reservation and the lines will be added as pos.order.lines.
    - Only the lines of the service with the current date will be added.
    - This will only add the quantity of the lines that is not already linked to another pos.order.line.

Pay pos.order on pms.reservation
--------------------------------

- if pay_on_reservation is active on pos.config, the payment screen will show the payment method: 'Reservation'.
- Click on it and the reservation modal will open, select the resired reservation, the pos.order will be validated and you will be shown the bill printing screen.
    - This will add the payment method selected in the pos.config.
    - pos.order.lines will be added as pms.service.lines in the reservation.
