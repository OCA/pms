from odoo.tests import common

INVALID_HOURS = [
    "8:00",
    "8:0",
    "1400",
    "14:00:00",
    "24:00",
    "14:99",
    "aa:bb",
    "14:",
]


class TestPms(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.availability_plan1 = cls.env["pms.availability.plan"].create(
            {"name": "Availability Plan 1"}
        )
        cls.pricelist1 = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist 1",
                "availability_plan_id": cls.availability_plan1.id,
            }
        )
        cls.company1 = cls.env["res.company"].create(
            {
                "name": "Company 1",
            }
        )
        cls.pms_property1 = cls.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )
        cls.room_type_class1 = cls.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class 1",
                "default_code": "RTC1",
            }
        )
        cls.board_service_room_only = cls.env.ref(
            "pms.product_template_board_room_only"
        )
        for pricelist in cls.env["product.pricelist"].search([]):
            if not pricelist.availability_plan_id:
                pricelist.write(
                    {
                        "availability_plan_id": cls.availability_plan1.id,
                        "is_pms_available": True,
                        "board_service_ids": [(4, cls.board_service_room_only.id)],
                    }
                )

    @classmethod
    def _create_board_service(cls, name, guests=("adult",), **vals):
        """A board service consumed by the given guests: one variant for
        each of ("adult", "child"), or a single one for every guest if empty"""
        attribute_lines = []
        if guests:
            attribute_lines = [
                (
                    0,
                    0,
                    {
                        "attribute_id": cls.env.ref(
                            "pms.product_attribute_board_guest"
                        ).id,
                        "value_ids": [
                            (
                                6,
                                0,
                                [
                                    cls.env.ref(
                                        f"pms.product_attribute_value_board_guest_{guest}"
                                    ).id
                                    for guest in guests
                                ],
                            )
                        ],
                    },
                )
            ]
        return cls.env["product.template"].create(
            dict(
                {
                    "name": name,
                    "type": "service",
                    "is_board_service": True,
                    "attribute_line_ids": attribute_lines,
                },
                **vals,
            )
        )

    @staticmethod
    def _board_service_variant(board_service, guest_type):
        return board_service.product_variant_ids.filtered(
            lambda product: product.board_guest_type == guest_type
        )
