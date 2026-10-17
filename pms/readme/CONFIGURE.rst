You will find the hotel settings in PMS Management > Configuration > Properties > Your Property.

This module required additional configuration for company, accounting, invoicing and user privileges.

Derived room type prices
~~~~~~~~~~~~~~~~~~~~~~~~

A room type can take its price from another one, e.g. a Superior room costing
10 more than the Double one, so that the pricelists only need the prices of
the latter. Set it in the *Derived Price* section of the room type:

* *Price Derived From*: the room type the price is taken from. It must be
  available in all the properties of the room type, and it can take its price
  from a third one in turn (e.g. Family = Superior + 20), up to ten levels.
* *Price Variation Type* and *Price Variation*: a fixed amount, in the currency
  of the pricelist, or a percentage of the base price. Negative values lower
  it, and the price never goes below zero.
* *Price Rounding*: the multiple the prices derived by a percentage are rounded
  to, e.g. 1 for whole amounts. Zero rounds them to the currency.
* *Derive in Pricelists*: the pricelists the price is derived in. Leave it
  empty to derive it in all of them.

Mind that a derived room type with no rule of its own in a pricelist it does
not derive in gets its sales price there.
