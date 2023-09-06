from odoo import http


def url_image(context, model, record_id, field):
    rt_image_attach = context.env['ir.attachment'].sudo().search([
        ('res_model', '=', model),
        ('res_id', '=', record_id),
        ('res_field', '=', field),
    ])
    if rt_image_attach and not rt_image_attach.access_token:
        rt_image_attach.generate_access_token()
    result = (
        http.request.env['ir.config_parameter']
            .sudo().get_param('web.base.url') +
        '/web/image/%s?access_token=%s' % (
            rt_image_attach.id, rt_image_attach.access_token
        ) if rt_image_attach else False
    )
    return result if result else ''
