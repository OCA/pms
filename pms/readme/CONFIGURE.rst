You will find the hotel settings in PMS Management > Configuration > Properties > Your Property.

This module required additional configuration for company, accounting, invoicing and user privileges.

Commercial inventory
~~~~~~~~~~~~~~~~~~~~

How many rooms of a type the property puts on sale is configured in
PMS Management > Revenue Management > Inventory, and does not depend on the rate.
Each rule covers a date range and applies to every night in it, either in general,
through a sale channel or through an agency:

* ``Quota`` is an allowance: what is left to sell is the quota minus what the scope
  already sold. Cancelling a reservation does **not** give it back, since the quota
  was spent when it was sold.
* ``Max. Availability`` is an exposure cap and is never consumed.
* Use ``-1`` for no limit and ``0`` to close the scope.

The effective limit is the **lowest** one across the scopes that apply, so a rule for
a sale channel can only restrict further what the general rule allows. With no general
rule for a night, the ``Default Quota`` and ``Default Max. Availability`` of the room
type are used instead; the absence of a channel or agency rule adds no limit of its own.

Rules of the same scope may overlap on purpose, which is how a season is overridden for
a shorter period: on the overlap, the rule modified last wins.

Several properties, room types or days of the week can be configured at once from
PMS Management > Revenue Management > Massive Inventory Changes. Repeating a massive
change over the same period and scope rewrites the rule already there instead of adding
another one on top of it.
