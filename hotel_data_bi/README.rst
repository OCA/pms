REVENUE EXPORTER
=============

Export Odoo data for Revenue  MyDataBI

Usage
=======
To use this module, you need to:

Create a user and give the "Hotel Management / Export data BI" permission.

To connect to Odoo via xmlrpc there are examples in https://www.odoo.com/documentation/10.0/api_integration.html in the "Calling methods" section with examples in several languages.

A python example:
import xmlrpclib

url = 'https://www.example.org'

username = 'username@example.org'

password = '123passwordexample'

db = 'example_db_name'

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))

uid = common.authenticate(db, username, password, {})

models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

models.execute_kw(db, uid, password,'data_bi','export_data_bi', [ 8, '2018-01-01'])

In the parameters of export_data_bi:

archivo == 1 'Tarifa'

archivo == 2 'Canal'

archivo == 3 'Hotel'

archivo == 4 'Pais'

archivo == 5 'Regimen'

archivo == 6 'Reservas'

archivo == 7 'Capacidad'

archivo == 8 'Tipo Habitación'

archivo == 9 'Budget'

archivo == 10 'Bloqueos'

archivo == 11 'Motivo Bloqueo'

archivo == 12 'Segmentos'

archivo == 13 'Clientes'

archivo == 14 'Estado Reservas'

fechafoto = start date to take data

in the example recive 8 'Tipo Habitación' from '2018-01-01'


Credits
=======

Creator
------------

* Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
