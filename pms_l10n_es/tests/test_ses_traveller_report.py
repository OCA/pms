import datetime

from freezegun import freeze_time
import xml.etree.cElementTree as ET
import xml.dom.minidom

from .common import TestPms


@freeze_time("2021-02-01")
class TestWizardTravellerReport(TestPms):
    def setUp(self):
        super().setUp()
        # creamos un canal de venta directo
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

        # creamos el tipo de habitación
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room type test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        # creamos la habitación
        self.room_double_1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 1",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )

    def test_generate_ses_file(self):
        self.env['pms.reservation'].create({
            'pms_property_id': self.pms_property1.id,
            'checkin': '2021-01-01',
            'checkout': '2021-01-02',
            'adults': 2,
            'partner_name': 'tomás',
            'preferred_room_id': self.room_double_1.id,
            'sale_channel_origin_id': self.sale_channel_direct1.id,
        })

        # Crear el elemento raíz con el prefijo ns2 y el espacio de nombres
        root = ET.Element("{http://www.neg.hospedajes.mir.es/altaReservaHospedaje}peticion")

        # Crear el subelemento solicitud
        solicitud = ET.SubElement(root, "solicitud")

        # Crear el subelemento comunicacion
        comunicacion = ET.SubElement(solicitud, "comunicacion")

        # Crear el subelemento establecimiento dentro de comunicacion
        establecimiento = ET.SubElement(comunicacion, "establecimiento")
        codigo = ET.SubElement(establecimiento, "codigo")
        codigo.text = "0000000972"

        # Crear el subelemento contrato dentro de comunicacion
        contrato = ET.SubElement(comunicacion, "contrato")
        referencia = ET.SubElement(contrato, "referencia")
        referencia.text = "F-87347783"
        fechaContrato = ET.SubElement(contrato, "fechaContrato")
        fechaContrato.text = "2023-06-19+02:00"
        fechaEntrada = ET.SubElement(contrato, "fechaEntrada")
        fechaEntrada.text = "2024-06-22T10:05:44.607+02:00"
        fechaSalida = ET.SubElement(contrato, "fechaSalida")
        fechaSalida.text = "2024-06-23T10:05:44.607+02:00"
        numPersonas = ET.SubElement(contrato, "numPersonas")
        numPersonas.text = "1"
        numHabitaciones = ET.SubElement(contrato, "numHabitaciones")
        numHabitaciones.text = "1"

        # Crear el subelemento pago dentro de contrato
        pago = ET.SubElement(contrato, "pago")
        tipoPago = ET.SubElement(pago, "tipoPago")
        tipoPago.text = "EFECT"
        fechaPago = ET.SubElement(pago, "fechaPago")
        fechaPago.text = "2023-05-19+02:00"
        medioPago = ET.SubElement(pago, "medioPago")
        medioPago.text = "texto"
        titular = ET.SubElement(pago, "titular")
        titular.text = "texto"
        caducidadTarjeta = ET.SubElement(pago, "caducidadTarjeta")
        caducidadTarjeta.text = "12/2027"

        # Crear el subelemento persona dentro de comunicacion
        persona = ET.SubElement(comunicacion, "persona")
        rol = ET.SubElement(persona, "rol")
        rol.text = "TI"
        nombre = ET.SubElement(persona, "nombre")
        nombre.text = "John"
        apellido1 = ET.SubElement(persona, "apellido1")
        apellido1.text = "Doe"
        numeroDocumento = ET.SubElement(persona, "numeroDocumento")
        numeroDocumento.text = "00000000T"
        correo = ET.SubElement(persona, "correo")
        correo.text = "correo@correo.es"

        # Crear el árbol XML
        tree = ET.ElementTree(root)

        # Guardar el árbol XML en un archivo
        tree.write("archivo.xml", encoding="utf-8", xml_declaration=True)
        xml_string = ET.tostring(root, encoding="unicode", method="xml")
        xml_formatted = xml.dom.minidom.parseString(xml_string).toprettyxml()

        print(xml_formatted)
        self.assertTrue(1)
