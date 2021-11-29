odoo.define("pms_sale.PMSConfiguratorFormView", function (require) {
    "use strict";

    var PMSConfiguratorFormController = require("pms_sale.PMSConfiguratorFormController");
    var FormView = require("web.FormView");
    var viewRegistry = require("web.view_registry");

    /**
     * @see EventConfiguratorFormController for more information
     */
    var PMSConfiguratorFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: PMSConfiguratorFormController,
        }),
    });

    viewRegistry.add("pms_configurator_form", PMSConfiguratorFormView);

    return PMSConfiguratorFormView;
});
