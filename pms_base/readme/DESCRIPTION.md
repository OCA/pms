This module is the base module for the Property Management System (PMS)
suite.

It provides the foundation for managing real estate properties,
including:

- **Properties**: Track residential and commercial properties with
  address, timezone, area, floor information, tags, and images.
- **Rooms**: Define rooms within each property with type, capacity, and
  area.
- **Amenities**: Catalog amenities grouped by type (toiletries,
  connectivity, kitchen facilities, laundry, parking, pets, etc.).
- **Services**: Link service products (cleaning, internet, parking,
  etc.) to properties for operational tracking.
- **Stages**: Configure lifecycle stages (New, Available, Cancelled) for
  property pipelines with Kanban support.
- **Teams**: Organize properties into teams for management and
  reporting.
- **Tags**: Classify properties with color-coded tags.
- **Settings**: Enable or disable features (rooms, amenities, services,
  teams) per company and configure the unit of measure for areas.

This module also provides access rights (User / Manager), security rules
scoped per company, and integration points for optional PMS extensions
(accounting, contracts, reservations, website, CRM, and more).
