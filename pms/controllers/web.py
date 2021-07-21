import base64
import logging

import odoo
from odoo import http
from odoo.http import request

from ..pms_jwt import util

_logger = logging.getLogger(__name__)


class WebController(http.Controller):
    @http.route(
        ["/web/avatar/<int:id>", "/web/avatar/<int:id>/<string:size>"],
        auth="public",
        csrf=False,
        cors="*",
    )
    def avatar(self, id=None, size="128", **kw):
        # get product
        headers = []
        try:
            user = request.env["res.users"].sudo().browse(id)
            content = None
            mimetype = None
            if user:
                # determine field to get
                field_size = "image"
                resize = True
                if size in ["512", "128"]:
                    field_size = "%s_%s" % (field_size, size)
                    resize = False
                else:
                    field_size = "image_1920"
                content = getattr(user, field_size)
                # the following lines purpose is to get mimetype
                attachment = (
                    request.env["ir.attachment"]
                    .sudo()
                    .search(
                        [
                            ("res_model", "=", "res.partner"),
                            ("res_id", "=", user.partner_id.id),
                            ("res_field", "=", "image_1920"),
                        ]
                    )
                )
                if attachment.exists():
                    mimetype = attachment.mimetype
            if content and mimetype:
                # resize image_variant here
                if resize:
                    if size == "large":
                        width, height = (500, 500)
                    # add other size here, eg:
                    # elif size == 'huge':
                    # width, height = (800, 800)
                    else:
                        width = None
                        height = None
                    if width:
                        content = odoo.tools.image_resize_image(
                            base64_source=content,
                            size=(width or None, height or None),
                            encoding="base64",
                            avoid_if_128=True,
                        )
                        # force mime type becuz of image resizer
                        # mimetype = 'image/png'
                image_base64 = base64.b64decode(content)
            else:
                image_base64 = (
                    self.placeholder()
                )  # could return (contenttype, content) in master
                mimetype = "image/gif"
        except Exception as ex:
            # just to make sure the placeholder image existed
            image_base64 = base64.b64decode(
                "R0lGODlhAQABAIABAP///wAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
            )
            mimetype = "image/gif"
            _logger.error(str(ex))
        finally:
            headers.append(("Content-Length", len(image_base64)))
            headers.append(("Content-Type", mimetype))
            response = request.make_response(image_base64, headers)
            response.status_code = 200
            return response

    def placeholder(self, image="no_image.gif"):
        return open(util.path("jwt_provider", "static", "img", image), "rb").read()
