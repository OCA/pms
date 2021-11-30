# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


class PropertyTableCompute(object):
    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey, ppr):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= ppr:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(ppr):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=20, ppr=4):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        x = 0
        for p in products:
            x = min(1, ppr)
            y = min(1, ppr)
            if index >= ppg:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % ppr, pos // ppr, x, y, ppr):
                pos += 1
            # if 21st products (index 20) and the last line is full (ppr products in it), break
            # (pos + 1.0) / ppr is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) // ppr) > maxy:
                break

            if x == 1 and y == 1:  # simple heuristic for CPU optimization
                minpos = pos // ppr

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False
            self.table[pos // ppr][pos % ppr] = {"product": p, "x": x, "y": y}
            if index <= ppg:
                maxy = max(maxy, y + (pos // ppr))
            index += 1

        # Format table according to HTML needs
        rows = sorted(self.table.items())
        rows = [r[1] for r in rows]
        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            x += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]

        return rows


class WebsiteSale(WebsiteSale):
    def _get_property_search_domain(self, search, category, guest, args):
        domain = []
        if search:
            domain += [("city", "ilike", search)]
        if guest:
            domain += [("no_of_guests", ">=", int(guest))]
        if category:
            domain += [("property_category_ids", "child_of", category.id)]
        if args.get("date_range"):
            date_range = args.get("date_range").split("-")
            start = date_range[0].strip() + " 00:00:00"
            end = date_range[1].strip() + " 23:59:59"
            start = datetime.strptime(start, "%m/%d/%Y %H:%M:%S")
            end = datetime.strptime(end, "%m/%d/%Y %H:%M:%S")
            reservation_ids = request.env["pms.reservation"].search(
                [
                    ("stop", "<=", end),
                    "|",
                    "|",
                    ("start", ">=", start),
                    ("start", ">=", end),
                    ("stop", ">=", start),
                ]
            )
            property_ids = reservation_ids.mapped("property_id")
            domain += [("id", "not in", property_ids.ids)]
        domain += [("property_child_ids", "=", False)]
        return domain

    def _get_pricelist_context(self):
        pricelist_context = dict(request.env.context)
        pricelist = False
        if not pricelist_context.get("pricelist"):
            pricelist = request.website.get_current_pricelist()
            pricelist_context["pricelist"] = pricelist.id
        else:
            pricelist = request.env["product.pricelist"].browse(
                pricelist_context["pricelist"]
            )

        return pricelist_context, pricelist

    def _update_property_values(self, Property, post):
        values = {
            "city": list(
                {
                    property_rec.city
                    for property_rec in Property.search([])
                    if property_rec.city
                }
            )
        }
        return values

    @http.route(
        [
            """/property""",
            """/property/page/<int:page>""",
            """/property/category/<model("pms.website.category"):category>""",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def property(
        self, page=0, ppg=False, category=None, search="", guest_select="", **post
    ):
        Category = request.env["pms.website.category"]
        if category:
            category = Category.search([("id", "=", int(category))], limit=1)
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post["ppg"] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env["website"].get_current_website().shop_ppg or 20

        ppr = request.env["website"].get_current_website().shop_ppr or 4

        domain = self._get_property_search_domain(
            search=search, category=category, guest=guest_select, args=post
        )

        keep = QueryURL("/property", category=category and int(category))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(
            request.context, pricelist=pricelist.id, partner=request.env.user.partner_id
        )

        Property = request.env["pms.property"].with_context(bin_size=True)

        search_property = Property.search(domain, order="name asc")
        url = "/property"

        categs_domain = [("parent_id", "=", False)]
        if search:
            search_categories = Category.search(
                [("property_ids", "in", search_property.ids)]
            ).parents_and_self
            categs_domain.append(("id", "in", search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        product_count = len(search_property)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post
        )
        offset = pager["offset"]
        properties = search_property[offset : offset + ppg]

        layout_mode = "grid"

        values = self._update_property_values(Property=Property, post=post)
        # properties
        values.update(
            {
                "category": category,
                "search_city": search,
                "search_guest": guest_select,
                "search_raneg": post.get("date_range"),
                "pager": pager,
                "pricelist": pricelist,
                "properties": properties,
                "search_count": product_count,  # common for all searchbox
                "bins": PropertyTableCompute().process(properties, ppg, ppr),
                "ppg": ppg,
                "ppr": ppr,
                "keep": keep,
                "layout_mode": layout_mode,
                "categories": categs,
                "search_categories_ids": search_categories.ids,
            }
        )

        return request.render("pms_website_sale.properties", values)
