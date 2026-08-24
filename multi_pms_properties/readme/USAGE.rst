* Use the standard multicompany guidelines applied to pms.property:

  ``_check_pms_properties_auto like model attribute to autocheck  on create/write``
  ``check_pms_properties like field attribute to check relational record properties consistence``
  ``This module not implement propety dependent fields``

* ``check_pms_properties`` injects a domain referring to the property field of the
  model, so any view showing such a field must keep ``pms_property_id(s)``
  available for every group combination. Restricting it with ``groups`` makes Odoo
  refuse to validate the view. To hide it from some users, add a companion node
  instead, the same way core does with ``company_id`` and ``check_company``::

    <field name="pms_property_ids" groups="pms.group_pms_user" />
    <field name="pms_property_ids" groups="!pms.group_pms_user" invisible="1" />
