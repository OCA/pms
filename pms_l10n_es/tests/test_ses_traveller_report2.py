import base64
import io
import time
import xml.dom.minidom
import xml.etree.ElementTree as ET
import zipfile

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from .common import TestPms

# Desactivar las advertencias de solicitud insegura
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def string_to_zip_to_base64(string_data):
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("data.xml", string_data.encode("utf-8"))
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_base64 = base64.b64encode(zip_data)
        return zip_base64.decode()
    except Exception as e:
        print(f"Error string to ZIP to Base64: {e}")
        return None


class TestPmsSES(TestPms):
    def _test_SES(self):
        url = "https://hospedajes.pre-ses.mir.es/hospedajes-web/ws/v1/comunicacion"
        user = "B01642958WS"
        password = "Temporal1"
        userAndPassBase64 = "Basic " + base64.b64encode(
            bytes(user + ":" + password, "utf-8")
        ).decode("utf-8")
        headers = {
            "Authorization": userAndPassBase64,
            "Content-Type": "text/xml; charset=utf-8",
        }

        property_code = "0000000972"

        var_xml_create_reservation = f"""<ns2:peticion xmlns:ns2="http://www.neg.hospedajes.mir.es/altaReservaHospedaje">
            <solicitud>
                <comunicacion>
                    <establecimiento>
                        <!--<codigo>0000000972</codigo>-->
                        <datosEstablecimiento>
                            <tipo>HOTEL</tipo>
                            <nombre>HOTEL DE PRUEBA</nombre>
                            <direccion>
                                <direccion>Hotel de prueba, dirección s/n</direccion>
                                <codigoMunicipio>36027</codigoMunicipio>
                                <codigoPostal>36967</codigoPostal>
                                <pais>ESP</pais>
                            </direccion>
                        </datosEstablecimiento>
                    </establecimiento>
                    <contrato>
                        <referencia>F-87347783</referencia>
                        <fechaContrato>2023-06-19+02:00</fechaContrato>
                        <fechaEntrada>2024-06-22T10:05:44.607+02:00</fechaEntrada>
                        <fechaSalida>2024-06-23T10:05:44.607+02:00</fechaSalida>
                        <numPersonas>1</numPersonas>
                        <pago>
                            <tipoPago>DESTI</tipoPago>
                        </pago>
                    </contrato>
                    <persona>
                        <rol>TI</rol>
                        <nombre>John</nombre>
                        <apellido1>Doe</apellido1>
                        <correo>correo@correo.es</correo>
                    </persona>
                </comunicacion>
            </solicitud>
        </ns2:peticion>"""

        data = string_to_zip_to_base64(var_xml_create_reservation)

        payload = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
                    <soapenv:Header/>
                    <soapenv:Body>
                        <com:comunicacionRequest>
                            <peticion>
                                <cabecera>
                                    <codigoArrendador>0000000972</codigoArrendador>
                                    <aplicacion>Roomdoo</aplicacion>
                                    <tipoOperacion>A</tipoOperacion>
                                    <tipoComunicacion>RH</tipoComunicacion>
                                </cabecera>
                                <solicitud>{data}</solicitud>
                            </peticion>
                        </com:comunicacionRequest>
                    </soapenv:Body>
                </soapenv:Envelope>
            """

        soap_response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False
        )
        root = ET.fromstring(soap_response.text)
        batch = root.find(".//lote").text
        var_xml_get_batch = f"""
            <con:lotes xmlns:con="http://www.neg.hospedajes.mir.es/consultarComunicacion">
                <con:lote>{batch}</con:lote>
            </con:lotes>
        """
        data = string_to_zip_to_base64(var_xml_get_batch)
        payload = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
            xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
                <soapenv:Header/>
                <soapenv:Body>
                    <com:comunicacionRequest>
                        <peticion>
                            <cabecera>
                                <codigoArrendador>{property_code}</codigoArrendador>
                                <aplicacion>Roomdoo</aplicacion>
                                <tipoOperacion>C</tipoOperacion>
                            </cabecera>
                            <solicitud>{data}</solicitud>
                        </peticion>
                    </com:comunicacionRequest>
                </soapenv:Body>
            </soapenv:Envelope>
        """
        time.sleep(35)

        soap_response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False
        )
        xml_formatted = xml.dom.minidom.parseString(soap_response.text).toprettyxml()
        print(xml_formatted)
        root = ET.fromstring(soap_response.text)
        error = root.find(".//error")
        print(error or "no hay error")

    def _test_SES2(self):
        url = "https://hospedajes.pre-ses.mir.es/hospedajes-web/ws/v1/comunicacion"
        user = "B01642958WS"
        password = "Temporal1"
        userAndPassBase64 = "Basic " + base64.b64encode(
            bytes(user + ":" + password, "utf-8")
        ).decode("utf-8")
        headers = {
            "Authorization": userAndPassBase64,
            "Content-Type": "text/xml; charset=utf-8",
        }

        property_code = "0000000972"

        var_xml_create_reservation = f"""<ns2:peticion xmlns:ns2="http://www.neg.hospedajes.mir.es/altaParteHospedaje">
            <solicitud>
                <codigoEstablecimiento>0000000972</codigoEstablecimiento>
                <comunicacion>
                    <contrato>
                        <referencia>F-87347783</referencia>
                        <fechaContrato>2023-05-19+02:00</fechaContrato>
                        <fechaEntrada>2023-05-02T14:00:00.000+02:00</fechaEntrada>
                        <fechaSalida>2023-05-03T12:00:00.000+02:00</fechaSalida>
                        <numPersonas>1</numPersonas>
                        <pago>
                            <tipoPago>DESTI</tipoPago>
                        </pago>
                    </contrato>
                    <persona>
                        <rol>VI</rol>
                        <nombre>Miguel</nombre>
                        <apellido1>Padín</apellido1>
                        <tipoDocumento>NIF</tipoDocumento>
                        <numeroDocumento>77406659K</numeroDocumento>
                        <soporteDocumento>CHQ106431</soporteDocumento>
                        <fechaNacimiento>1985-03-20+02:00</fechaNacimiento>
                        <nacionalidad>ESP</nacionalidad>
                        <sexo>H</sexo>
                        <direccion>
                            <direccion>Joaquín Costa 18, 303</direccion>
                            <codigoMunicipio>35016</codigoMunicipio>
                            <codigoPostal>35007</codigoPostal>
                            <pais>ESP</pais>
                        </direccion>
                        <telefono>639476254</telefono>
                    </persona>
                </comunicacion>
            </solicitud>
        </ns2:peticion>"""

        data = string_to_zip_to_base64(var_xml_create_reservation)

        payload = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
                    <soapenv:Header/>
                    <soapenv:Body>
                        <com:comunicacionRequest>
                            <peticion>
                                <cabecera>
                                    <codigoArrendador>0000000972</codigoArrendador>
                                    <aplicacion>Roomdoo</aplicacion>
                                    <tipoOperacion>A</tipoOperacion>
                                    <tipoComunicacion>PV</tipoComunicacion>
                                </cabecera>
                                <solicitud>{data}</solicitud>
                            </peticion>
                        </com:comunicacionRequest>
                    </soapenv:Body>
                </soapenv:Envelope>
            """

        soap_response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False
        )

        root = ET.fromstring(soap_response.text)
        batch = root.find(".//lote").text
        var_xml_get_batch = f"""
            <con:lotes xmlns:con="http://www.neg.hospedajes.mir.es/consultarComunicacion">
                <con:lote>{batch}</con:lote>
            </con:lotes>
        """
        data = string_to_zip_to_base64(var_xml_get_batch)
        payload = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
            xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
                <soapenv:Header/>
                <soapenv:Body>
                    <com:comunicacionRequest>
                        <peticion>
                            <cabecera>
                                <codigoArrendador>{property_code}</codigoArrendador>
                                <aplicacion>Roomdoo</aplicacion>
                                <tipoOperacion>C</tipoOperacion>
                            </cabecera>
                            <solicitud>{data}</solicitud>
                        </peticion>
                    </com:comunicacionRequest>
                </soapenv:Body>
            </soapenv:Envelope>
        """
        time.sleep(35)

        soap_response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False
        )
        xml_formatted = xml.dom.minidom.parseString(soap_response.text).toprettyxml()
        print(xml_formatted)
        root = ET.fromstring(soap_response.text)
        error = root.find(".//error")
        print(error or "no hay error")

    def test_SES3(self):
        self.env["traveller.report.wizard"].generate_xml_reservation(32)
        print("test")
