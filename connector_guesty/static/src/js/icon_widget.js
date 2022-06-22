odoo.define("icon_widget", function (require) {
    "use strict";
    // Var core = require("web.core");
    // var _t = core._t;
    // var QWeb = core.qweb;

    var registry = require("web.field_registry");
    var AbstractField = require("web.AbstractField");

    const IconWidget = AbstractField.extend({
        _render: function () {
            // This.$el.html(QWeb.render(this.template, {widget: this}));
            var body_list = [];
            for (var i = 0; i < this.value; i++) {
                body_list.push("<i class='fa fa-bed pl-2'/>");
            }
            this.$el.html(body_list.join(""));
            return this._super.apply(this, arguments);
        },
    });

    registry.add("icon_widget", IconWidget);
});
