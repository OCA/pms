from freezegun import freeze_time

from odoo.tests.common import TransactionCase

freeze_time("2000-02-02")


class TestPmsPayment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    # TODO: Test allowed manual payment
    # create a journal with allowed_pms_payments = True and
    # check that the _get_payment_methods property method return it

    # TODO: Test not allowed manual payment
    # create a journal without allowed_pms_payments = True and
    # check that the _get_payment_methods property method dont return it

    # TODO: Test default account payment create
    # create a bank journal, a reservation, pay the reservation
    # with do_payment method without pay_type parameter
    # and check that account payment was created

    # TODO: Test default statement line create
    # create a cash journal, a reservation, pay the reservation
    # with do_payment method without pay_type parameter
    # and check that statement line was created

    # TODO: Test set pay_type cash, statement line create
    # create a bank journal, a reservation, pay the reservation
    # with do_payment method with 'cash' pay_type parameter
    # and check that statement line was created

    # TODO: Test set pay_type bank, account payment create
    # create a cash journal, a reservation, pay the reservation
    # with do_payment method with 'bank' pay_type parameter
    # and check that account payment was created
