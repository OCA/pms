// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.Constants', function (require) {
"use strict";

  var Core = require('web.core'),
      Time = require('web.time'),

      l10n = Core._t.database.parameters;

  return {
    ODOO_DATE_MOMENT_FORMAT: 'YYYY-MM-DD',
    ODOO_DATETIME_MOMENT_FORMAT: 'YYYY-MM-DD HH:mm:ss',
    L10N_DATE_MOMENT_FORMAT: "DD/MM/YYYY", //FIXME: Time.strftime_to_moment_format(l10n.date_format),
    L10N_DATETIME_MOMENT_FORMAT: 'DD/MM/YYYY ' + Time.strftime_to_moment_format(l10n.time_format),

    CURRENCY_SYMBOL: "€",
  };

});
