def migrate(cr, version):
    cr.execute("UPDATE pms_reservation SET to_send_mail = NOT is_mail_send")
