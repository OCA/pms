// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.MPMSCalendarView', function (require) {
"use strict";

var AbstractView = require('web.AbstractView'),
    MPMSCalendarModel = require('hotel_calendar.MPMSCalendarModel'),
    MPMSCalendarController = require('hotel_calendar.MPMSCalendarController'),
    MPMSCalendarRenderer = require('hotel_calendar.MPMSCalendarRenderer'),
    ViewRegistry = require('web.view_registry'),
    SystrayMenu = require('web.SystrayMenu'),
    ControlPanel = require('web.ControlPanel'),
    Widget = require('web.Widget'),
    Session = require('web.session'),
    Core = require('web.core'),

    _lt = Core._lt,
    QWeb = Core.qweb;

/* HIDE CONTROL PANEL */
/* FIXME: Look's like a hackish solution */
ControlPanel.include({
  update: function(status, options) {
      if (typeof options === 'undefined') {
        options = {};
      }
      if (typeof options.toHide === 'undefined')
          options.toHide = false;
      var action_stack = this.getParent().action_stack;
      if (action_stack && action_stack.length) {
          var active_action = action_stack[action_stack.length-1];
          if (active_action.widget && active_action.widget.active_view &&
                  active_action.widget.active_view.type === 'mpms'){
              options.toHide = true;
          }
      }
      this._super(status, options);
      this._toggle_visibility(!options.toHide);
  }
});

var MPMSCalendarView = AbstractView.extend({
    display_name: _lt('Calendar MPMS'),
    icon: 'fa-calendar',
    jsLibs: ['/hotel_calendar/static/src/lib/hcalendar/js/hcalendar_management.js'],
    cssLibs: [
        '/hotel_calendar/static/src/lib/hcalendar/css/hcalendar.css',
        '/hotel_calendar/static/src/lib/hcalendar/css/hcalendar_management.css'
    ],
    config: {
        Model: MPMSCalendarModel,
        Controller: MPMSCalendarController,
        Renderer: MPMSCalendarRenderer,
    },

    init: function (viewInfo, params) {
        this._super.apply(this, arguments);
        var arch = viewInfo.arch;
        var fields = viewInfo.fields;
        var attrs = arch.attrs;

        // If form_view_id is set, then the calendar view will open a form view
        // with this id, when it needs to edit or create an event.
        this.controllerParams.formViewId =
            attrs.form_view_id ? parseInt(attrs.form_view_id, 10) : false;
        if (!this.controllerParams.formViewId && params.action) {
            var formViewDescr = _.find(params.action.views, function (v) {
                return v[1] ===  'form';
            });
            if (formViewDescr) {
                this.controllerParams.formViewId = formViewDescr[0];
            }
        }

        this.controllerParams.readonlyFormViewId = !attrs.readonly_form_view_id || !utils.toBoolElse(attrs.readonly_form_view_id, true) ? false : attrs.readonly_form_view_id;
        this.controllerParams.context = params.context || {};
        this.controllerParams.displayName = params.action && params.action.name;

        this.rendererParams.model = viewInfo.model;

        this.loadParams.fields = fields;
        this.loadParams.fieldsInfo = viewInfo.fieldsInfo;
        this.loadParams.creatable = false;

        this.loadParams.mode = attrs.mode;
    },
});

ViewRegistry.add('mpms', MPMSCalendarView);

return MPMSCalendarView;

});
