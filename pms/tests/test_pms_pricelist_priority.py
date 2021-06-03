import datetime

from freezegun import freeze_time

from odoo.tests import common


class TestPmsPricelistRules(common.SavepointCase):
    def create_common_scenario(self):
        self.product_template = self.env["product.template"].create(
            {"name": "Template1"}
        )
        self.product_category = self.env["product.category"].create(
            {"name": "Category1"}
        )

        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {"name": "Availability 1"}
        )

        self.availability_plan2 = self.env["pms.availability.plan"].create(
            {"name": "Availability"}
        )
        # sequences
        self.folio_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.reservation_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.checkin_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room Class", "default_code": "ROOM"}
        )

        self.room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id, self.property2.id],
                "name": "Single",
                "default_code": "SIN",
                "class_id": self.room_type_class.id,
                "list_price": 30,
            }
        )

        self.room = self.env["pms.room"].create(
            {
                "pms_property_id": self.property1.id,
                "name": "Single 101",
                "room_type_id": self.room_type.id,
            }
        )

        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property2.id,
                "name": "Single 102",
                "room_type_id": self.room_type.id,
            }
        )

        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist_1",
            }
        )

        self.partner1 = self.env["res.partner"].create({"name": "Carles"})

    @freeze_time("2000-01-01")
    def test_simple_price_without_items(self):
        # TEST CASE : no items applied

        # ARRANGE
        self.create_common_scenario()

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today(),
                "checkout": datetime.datetime.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "partner_id": self.partner1.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.room.room_type_id.list_price * n_days

        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_subtotal, "The price is not as expected"
        )

    @freeze_time("2022-01-01")
    def test_items_sort(self):

        # ARRANGE
        self.create_common_scenario()

        # - test cases to verify the order for each field considered individually
        # - test cases to prioritize fields over other fields:
        #                                                   1. applied_on
        #                                                   2. date
        #                                                   3. date consumption
        #                                                   4. num. properties
        #                                                   5. id
        # - tie
        # - no [date_start|date_end|date_start_consumption|date_end_consumption]
        properties = self.room_type.product_id.pms_property_ids.ids
        test_cases = [
            {
                "name": "sorting applied_on",
                "expected_price": 50 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "2_product_category",
                        "categ_id": self.product_category.id,
                        "fixed_price": 60.0,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "fixed_price": 50.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "1_product",
                        "product_id": self.room_type.product_id.id,
                        "product_tmpl_id": self.product_template.id,
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "sorting SALE date min range",
                "expected_price": 50.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=2),
                        "fixed_price": 60.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=1),
                        "fixed_price": 50.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "sorting CONSUMPTION date min range",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=6),
                        "fixed_price": 60.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=10),
                        "fixed_price": 50.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "sorting num. properties",
                "expected_price": 50.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "fixed_price": 60.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "pms_property_ids": [self.property1.id],
                        "fixed_price": 50.0,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "pms_property_ids": [self.property1.id, self.property2.id],
                        "fixed_price": 40.0,
                    },
                ],
            },
            {
                "name": "sorting by item id",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "fixed_price": 60.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "fixed_price": 50.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "prioritize applied_on over SALE date",
                "expected_price": 60.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=2),
                        "fixed_price": 60.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "product_id": self.room_type.product_id.id,
                        "product_tmpl_id": self.product_template.id,
                        "applied_on": "1_product",
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=1),
                        "fixed_price": 50.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "prioritize SALE date over CONSUMPTION date",
                "expected_price": 120.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=10),
                        "fixed_price": 120.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "fixed_price": 50.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "prioritize CONSUMPTION date over min. num. properties",
                "expected_price": 50.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "fixed_price": 120.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "pms_property_ids": [self.property1.id, self.property2.id],
                        "fixed_price": 50.0,
                    },
                ],
            },
            {
                "name": "prioritize min. num. properties over item id",
                "expected_price": 50.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "fixed_price": 120.0,
                        "pms_property_ids": properties,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "pms_property_ids": [self.property1.id, self.property2.id],
                        "fixed_price": 50.0,
                    },
                ],
            },
            {
                "name": "tie => order by item id",
                "expected_price": 50.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "pms_property_ids": [self.property1.id, self.property2.id],
                        "fixed_price": 120.0,
                    },
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "date_start": datetime.datetime.now(),
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "pms_property_ids": [self.property1.id, self.property2.id],
                        "fixed_price": 50.0,
                    },
                ],
            },
            {
                "name": "no SALE DATE START",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=1),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "no SALE DATE END",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "no consumption DATE START",
                "expected_price": 40.0 + self.room_type.list_price * 2,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_end_consumption": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "no consumption DATE END",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "only applied consumption in one night",
                "expected_price": 40.0 + self.room_type.list_price * 2,
                "items": [
                    {
                        "pricelist_id": self.pricelist.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
        ]

        for tc in test_cases:
            with self.subTest(k=tc):

                # ARRANGE
                items = []
                for item in tc["items"]:
                    item = self.env["product.pricelist.item"].create(item)
                    items.append(item.id)

                # ACT
                reservation = self.env["pms.reservation"].create(
                    {
                        "partner_id": self.partner1.id,
                        "checkin": datetime.datetime.now(),
                        "checkout": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "preferred_room_id": self.room.id,
                        "pms_property_id": self.property1.id,
                        "pricelist_id": self.pricelist.id,
                    }
                )
                reservation_price = reservation.price_subtotal
                self.env["pms.reservation"].browse(reservation.id).unlink()
                self.env["product.pricelist.item"].browse(items).unlink()

                # ASSERT
                self.assertEqual(tc["expected_price"], reservation_price, tc["name"])
