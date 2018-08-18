# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

class ChannelBackend(models.Model):
    _name = 'channel.backend'
    _description = 'Hotel Channel Backend'
    _inherit = 'connector.backend'

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        lang = self.default_lang_id
        if lang.code != self.env.context.get('lang'):
            self = self.with_context(lang=lang.code)
        user = self.env['ir.default'].sudo().get(
            'res.config.settings', 'hotel_connector_user')
        passwd = self.env['ir.default'].sudo().get(
            'res.config.settings', 'hotel_connector_passwd')
        lcode = self.env['ir.default'].sudo().get(
            'res.config.settings', 'hotel_connector_lcode')
        pkey = self.env['ir.default'].sudo().get(
            'res.config.settings', 'hotel_connector_pkey')
        server_addr = self.env['ir.default'].sudo().get(
            'res.config.settings', 'hotel_connector_server')
        wubook_login = WuBookLogin(
            server_addr,
            user,
            passwd,
            lcode,
            pkey
        )
        with WuBookAdapter(wubook_login) as channel_api:
            _super = super(ChannelBackend, self)
            # from the components we'll be able to do: self.work.magento_api
            with _super.work_on(model_name, **kwargs) as work:
                yield work
