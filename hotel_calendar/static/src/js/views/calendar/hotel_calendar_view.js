// Copyright 2018 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar.PMSCalendarView', function (require) {
"use strict";

var AbstractView = require('web.AbstractView'),
    PMSCalendarModel = require('hotel_calendar.PMSCalendarModel'),
    PMSCalendarController = require('hotel_calendar.PMSCalendarController'),
    PMSCalendarRenderer = require('hotel_calendar.PMSCalendarRenderer'),
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
                  active_action.widget.active_view.type === 'pms'){
              options.toHide = true;
          }
      }
      this._super(status, options);
      this._toggle_visibility(!options.toHide);
  }
});

/** SYSTRAY **/
var CalendarMenu = Widget.extend({
    template: 'HotelCalendar.SettingsMenu',
    events: {
      "click a[data-action]": "perform_callback",
    },

    start: function(){
      this.$dropdown = this.$(".o_calendar_settings_dropdown");
      return $.when(
        this._rpc({
            model: 'res.users',
            method: 'read',
            args: [[Session.uid], ["pms_show_notifications", "pms_show_pricelist", "pms_show_availability", "pms_divide_rooms_by_capacity"]],
            context: Session.user_context,
        })
      ).then(function(result) {
        this._show_notifications = result[0]['pms_show_notifications'];
        this._show_pricelist = result[0]['pms_show_pricelist'];
        this._show_availability = result[0]['pms_show_availability'];
        this._show_divide_rooms_by_capacity = result[0]['pms_divide_rooms_by_capacity'];
        return this.update();
      }.bind(this));
    },

    perform_callback: function (evt) {
        evt.preventDefault();
        var params = $(evt.target).data();
        var callback = params.action;

        if (callback && this[callback]) {
            this[callback](params, evt);
        } else {
            console.warn("No handler for ", callback);
        }
    },

    update: function() {
      // var view_type = this.getParent().getParent()._current_state.view_type;
      // if (view_type === 'pms') {
      //   this.do_show();
        this.$dropdown
            .empty()
            .append(QWeb.render('HotelCalendar.SettingsMenu.Global', {
                manager: this,
            }));
      // }
      // else {
      //   this.do_hide();
      // }
      return $.when();
    },

    toggle_show_notification: function() {
      this._show_notifications = !this._show_notifications;
      this._rpc({
          model: 'res.users',
          method: 'write',
          args: [[Session.uid], {pms_show_notifications: this._show_notifications}],
          context: Session.user_context,
      }).then(function () {
          window.location.reload();
      });
    },

    toggle_show_pricelist: function() {
      this._show_pricelist = !this._show_pricelist;
      this._rpc({
          model: 'res.users',
          method: 'write',
          args: [[Session.uid], {pms_show_pricelist: this._show_pricelist}],
          context: Session.user_context,
      }).then(function () {
          window.location.reload();
      });
    },

    toggle_show_availability: function() {
      this._show_availability = !this._show_availability;
      this._rpc({
          model: 'res.users',
          method: 'write',
          args: [[Session.uid], {pms_show_availability: this._show_availability}],
          context: Session.user_context,
      }).then(function () {
          window.location.reload();
      });
    },

    toggle_show_divide_rooms_by_capacity: function() {
      this._show_divide_rooms_by_capacity = !this._show_divide_rooms_by_capacity;
      this._rpc({
          model: 'res.users',
          method: 'write',
          args: [[Session.uid], {pms_divide_rooms_by_capacity: this._show_divide_rooms_by_capacity}],
          context: Session.user_context,
      }).then(function () {
          window.location.reload();
      });
    }
});

var PMSCalendarView = AbstractView.extend({
    display_name: _lt('Calendar PMS'),
    icon: 'fa-calendar',
    //jsLibs: [],
    cssLibs: ['/hotel_calendar/static/src/lib/hcalendar/css/hcalendar.css'],
    config: {
        Model: PMSCalendarModel,
        Controller: PMSCalendarController,
        Renderer: PMSCalendarRenderer,
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

        this.loadParams.fields = fields;
        this.loadParams.fieldsInfo = viewInfo.fieldsInfo;
        this.loadParams.creatable = false;

        this.loadParams.mode = attrs.mode;
    },
});

SystrayMenu.Items.push(CalendarMenu);
ViewRegistry.add('pms', PMSCalendarView);
//Core.view_registry.add('pms', HotelCalendarView);

return PMSCalendarView;

});
