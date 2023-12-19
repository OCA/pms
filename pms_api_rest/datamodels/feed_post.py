from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class FeedPost(Datamodel):
    _name = "feed.post.info"
    postId = fields.String(required=True, allow_none=False)
    title = fields.String(required=True, allow_none=False)
    link = fields.String(required=True, allow_none=False)
    description = fields.String(required=True, allow_none=False)
    publishDate = fields.String(required=True, allow_none=False)
    author = fields.String(required=True, allow_none=False)
    imageUrl = fields.String(required=True, allow_none=False)
