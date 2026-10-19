INE occupancy surveys
~~~~~~~~~~~~~~~~~~~~~

Go to *Reservations > Generate INE file*, pick the property and a date in
the month to report, and generate.

The questionnaire the establishment receives asks for a single week
(hotels) or fortnight (apartments), but the file always covers the whole
natural month, so the period is expanded to the month of the start date.
A file built for part of a month is rejected: the INE checks the daily
chain of every place of residence, and the first day of a partial file
never matches it.

Before handing the file over, the same content rules the INE applies after
the schema are run over it, and a file that would be rejected raises an
error naming the day and the figures behind it instead of being
downloaded.

The file is then uploaded to the IRIA portal of the INE. Note that IRIA no
longer allows editing a questionnaire once it has been uploaded.
