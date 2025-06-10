from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get("pos_user_force", False):
            return (
                super()
                .sudo()
                .with_context(pos_user_force=False)
                .search_read(domain, fields, offset, limit, order)
            )
        else:
            return super().search_read(domain, fields, offset, limit, order)
