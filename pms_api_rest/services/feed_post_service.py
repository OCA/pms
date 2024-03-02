from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


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
        for rss in self.env["rss.post"].search([], limit=5, order="publish_date desc"):
            result_rss.append(
                PmsFeedRss(
                    postId=rss.post_id,
                    title=rss.title,
                    link=rss.link,
                    description=rss.description,
                    publishDate=str(rss.publish_date),
                    author=rss.author if rss.author else "",
                    imageUrl=rss.image_url or "",
                )
            )
        return result_rss
