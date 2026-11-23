To use this module, please, read the complete user guide at `<roomdoo.com>`_.

Working with derived room type prices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The price of a room type is only derived from its base room type on the days
a pricelist has no rule of its own for it:

* An item of the derived room type in the pricelist sets its price on its
  dates: it overrides the derivation there, and the room type follows its base
  again once the item is removed.
* Rules on a product category or on all products cover the room type as well,
  so they win over the derivation. Keep them out of the pricelists the room
  types derive in.
* The base room type is priced by the same pricelist, with its own rules or
  derived in turn. With no rule at all, its sales price is the base.
* Pricelists based on another one through category or global rules (e.g. a
  channel rate 10% above the standard one) apply on top of the derived price.
  When they hold rules for the base room type only, the derived room type has
  no rule there either: its price is derived from the price of the base room
  type in that pricelist, which may not be what you want (e.g. a breakfast
  surcharge per guest of the base room type). Give those pricelists rules for
  the derived room types too, or use category or global rules there instead.
* The base price is computed for the date and the property of the stay only,
  not for the guests: modules pricing by occupancy apply their rules to the
  derived room type afterwards.
* Prices already set on reservations do not follow later changes of the base
  price: use *Update prices* on the reservation to recompute them.
* Massive changes on pricelists leave the derived room types out of the price
  changes when no room type is selected, so that they keep following their
  base, except on the dates they have a price of their own, which is kept.
  Select them explicitly to give them a price of their own.
