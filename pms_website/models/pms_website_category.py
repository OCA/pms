# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class PMSWebsiteCategory(models.Model):
    _name = "pms.website.category"
    _inherit = ["website.seo.metadata", "website.multi.mixin", "image.mixin"]
    _description = "Website Property Category"
    _parent_store = True
    _order = "name, id"

    name = fields.Char(string="Category Name", help="Category Name", required=True)
    parent_path = fields.Char(index=True)
    parents_and_self = fields.Many2many(
        "pms.website.category", compute="_compute_parents_and_self_new"
    )
    parent_id = fields.Many2one(
        string="Parent Category",
        comodel_name="pms.website.category",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "pms.website.category", "parent_id", string="Children Property category"
    )
    property_ids = fields.Many2many("pms.property", relation="property_category_rel")

    @api.constrains("parent_id")
    def check_parent_id(self):
        if not self._check_recursion():
            raise ValueError(_("Error ! You cannot create recursive categories."))

    def name_get(self):
        res = []
        for category in self:
            for category in self:
                res.append(
                    (category.id, " / ".join(category.parents_and_self.mapped("name")))
                )
        return res

    def _compute_parents_and_self_new(self):
        for category in self:
            if category.parent_path:
                category.parents_and_self = self.env["pms.website.category"].browse(
                    [int(p) for p in category.parent_path.split("/")[:-1]]
                )
            else:
                category.parents_and_self = category
