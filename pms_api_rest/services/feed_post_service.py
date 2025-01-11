from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


class PmsFeedRss(Component):
    _inherit = "base.rest.service"
    _name = "pms.feed.rss.service"
    _usage = "feed-posts"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("feed.post.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_feed_posts(self):
        result_rss = []
        PmsFeedRss = self.env.datamodels["feed.post.info"]
        posts = (
            self.env["rss.post"].sudo().search([], limit=5, order="publish_date desc")
        )
        pms_api_check_access(user=self.env.user, records=posts)
        for post in posts:
            result_rss.append(
                PmsFeedRss(
                    postId=post.post_id,
                    title=post.title,
                    link=post.link,
                    description=post.description,
                    publishDate=str(post.publish_date),
                    author=post.author if post.author else "",
                    imageUrl=post.image_url or "",
                )
            )
        return result_rss
