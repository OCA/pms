You will find the hotel settings in PMS Management > Configuration > Properties > Your Property.

This module required additional configuration for company, accounting, invoicing and user privileges.

Children and room capacity
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default children take no place in the room, so only the adults are checked
against its capacity. Properties that want to count them can set the system
parameter ``pms.children_occupy_capacity`` to ``True``, in Settings > Technical
> System Parameters.

Once it is on, children take the regular places of the room first and only
overflow into its children places, the ones where only a child can sleep, such
as child bunk beds. Adults never occupy those, so a room with free children
places can still be full.

Mind that turning it on refuses reservations that the property may have been
taking until then.
