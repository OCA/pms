![](Aspose.Words.1ff0a55d-02ba-4d5f-8f72-acc1fcb3dba4.001.png)

Standard3 Check-in & Check-out API

Check-in & Check-out API

[\*\*Introduction](#_page3_x72.00_y50.55) **[4**
](#\_page3_x72.00_y50.55)[Changelog](#_page4_x72.00_y50.55)
[5\*\* ](#_page4_x72.00_y50.55)[Flow](#_page5_x72.00_y50.55)
[6\*\*](#_page5_x72.00_y50.55)\*\*

[Check-In](#_page5_x72.00_y105.04)
[6 ](#_page5_x72.00_y105.04)[Online](#_page5_x72.00_y150.64)
[6 ](#_page5_x72.00_y150.64)[Kiosk](#_page5_x72.00_y364.63)
[6 ](#_page5_x72.00_y364.63)[Check-out](#_page5_x72.00_y578.62)
[6 ](#_page5_x72.00_y578.62)[Online](#_page5_x72.00_y624.22)
[6 ](#_page5_x72.00_y624.22)[Kiosk](#_page6_x72.00_y50.55) [7](#_page6_x72.00_y50.55)

[\*\*Authentication](#_page7_x72.00_y50.55) **[8**
](#\_page7_x72.00_y50.55)[Headers](#_page7_x72.00_y680.40)\*\*
[8 ](#_page7_x72.00_y680.40)[Request](#_page8_x72.00_y50.55)
[9 ](#_page8_x72.00_y50.55)[Response](#_page8_x72.00_y113.67)
[9](#_page8_x72.00_y113.67)

[\*\*Booking](#_page9_x72.00_y50.55) **[10**
](#\_page9_x72.00_y50.55)[Search By Form](#_page9_x72.00_y134.02)\*\*
[10 ](#_page9_x72.00_y134.02)[Headers](#_page10_x72.00_y50.55)
[11 ](#_page10_x72.00_y50.55)[Request](#_page10_x72.00_y148.64)
[11 ](#_page10_x72.00_y148.64)[Response](#_page10_x72.00_y667.56)
[11 ](#_page10_x72.00_y667.56)[Search By Unique Identifier](#_page15_x72.00_y637.96)
[15 ](#_page15_x72.00_y637.96)[Headers](#_page16_x72.00_y50.55)
[16 ](#_page16_x72.00_y50.55)[Request](#_page16_x72.00_y148.64)
[16 ](#_page16_x72.00_y148.64)[Response](#_page16_x72.00_y246.74)
[16 ](#_page16_x72.00_y246.74)[Search By Entrance Date](#_page16_x72.00_y411.75)
[16 ](#_page16_x72.00_y411.75)[Headers](#_page16_x72.00_y486.32)
[16 ](#_page16_x72.00_y486.32)[Request](#_page16_x72.00_y584.42)
[16 ](#_page16_x72.00_y584.42)[Response](#_page16_x72.00_y682.51)
[16 ](#_page16_x72.00_y682.51)[Search By Departure Date](#_page17_x72.00_y98.49)
[17 ](#_page17_x72.00_y98.49)[Headers](#_page17_x72.00_y192.04)
[17 ](#_page17_x72.00_y192.04)[Request](#_page17_x72.00_y290.13)
[17 ](#_page17_x72.00_y290.13)[Response](#_page17_x72.00_y388.23)
[17](#_page17_x72.00_y388.23)

[\*\*Payment](#_page18_x72.00_y50.55) **[18**
](#\_page18_x72.00_y50.55)[Invoicing](#_page18_x72.00_y334.78)\*\*
[18 ](#_page18_x72.00_y334.78)[Headers](#_page18_x72.00_y380.38)
[18 ](#_page18_x72.00_y380.38)[Request](#_page18_x72.00_y478.47)
[18 ](#_page18_x72.00_y478.47)[Response](#_page19_x72.00_y117.47)
[19 ](#_page19_x72.00_y117.47)[Register Payment](#_page19_x72.00_y591.19)
[19 ](#_page19_x72.00_y591.19)[Headers](#_page19_x72.00_y636.79)
[19 ](#_page19_x72.00_y636.79)[Request](#_page20_x72.00_y50.55)
[20 ](#_page20_x72.00_y50.55)[Response](#_page20_x72.00_y475.29)
[20](#_page20_x72.00_y475.29)

[\*\*Guest](#_page21_x72.00_y50.55) **[21**](#\_page21_x72.00_y50.55)\*\*

[Data Submission](#_page21_x72.00_y171.96)
[21 ](#_page21_x72.00_y171.96)[Headers](#_page21_x72.00_y265.51)
[21 ](#_page21_x72.00_y265.51)[Request](#_page21_x72.00_y363.60)
[21 ](#_page21_x72.00_y363.60)[Response](#_page24_x72.00_y233.36)
[24 ](#_page24_x72.00_y233.36)[Download File](#_page24_x72.00_y437.35)
[24 ](#_page24_x72.00_y437.35)[Url](#_page25_x72.00_y117.46)
[25 ](#_page25_x72.00_y117.46)[Headers](#_page25_x72.00_y172.16)
[25 ](#_page25_x72.00_y172.16)[Request](#_page25_x72.00_y280.26)
[25 ](#_page25_x72.00_y280.26)[Response](#_page25_x72.00_y407.32)
[25 ](#_page25_x72.00_y407.32)[Get Legal Texts](#_page25_x72.00_y553.37)
[25 ](#_page25_x72.00_y553.37)[Headers](#_page26_x72.00_y50.55)
[26 ](#_page26_x72.00_y50.55)[Request](#_page26_x72.00_y142.64)
[26 ](#_page26_x72.00_y142.64)[Response](#_page26_x72.00_y298.68)
[26](#_page26_x72.00_y298.68)

[\*\*Check-In](#_page27_x72.00_y50.55) **[27**
](#\_page27_x72.00_y50.55)[Confirmation](#_page27_x72.00_y105.04)\*\*
[27 ](#_page27_x72.00_y105.04)[Headers](#_page27_x72.00_y198.59)
[27 ](#_page27_x72.00_y198.59)[Request](#_page27_x72.00_y296.68)
[27 ](#_page27_x72.00_y296.68)[Response](#_page27_x72.00_y394.78)
[27](#_page27_x72.00_y394.78)

[\*\*Check-out](#_page28_x72.00_y50.55) **[28**
](#\_page28_x72.00_y50.55)[Confirmation](#_page28_x72.00_y105.04)\*\*
[28 ](#_page28_x72.00_y105.04)[Headers](#_page28_x72.00_y217.56)
[28 ](#_page28_x72.00_y217.56)[Request](#_page28_x72.00_y315.66)
[28 ](#_page28_x72.00_y315.66)[Response](#_page28_x72.00_y413.75)
[28](#_page28_x72.00_y413.75)

[\*\*Data Format](#_page29_x72.00_y50.55) **[29**
](#\_page29_x72.00_y50.55)[Data types](#_page29_x72.00_y423.75)\*\*
[29 ](#_page29_x72.00_y423.75)[String](#_page29_x72.00_y469.35)
[29 ](#_page29_x72.00_y469.35)[Integer](#_page30_x72.00_y50.55)
[30](#_page30_x72.00_y50.55)

[Float](#_page30_x72.00_y90.70)
[30 ](#_page30_x72.00_y90.70)[Boolean](#_page30_x72.00_y217.76)
[30 ](#_page30_x72.00_y217.76)[Enum](#_page30_x72.00_y315.86)
[30 ](#_page30_x72.00_y315.86)[Object](#_page32_x72.00_y282.33)
[32 ](#_page32_x72.00_y282.33)[Array](#_page32_x72.00_y322.48)
[32](#_page32_x72.00_y322.48)

[\*\*Additional documentation](#_page33_x72.00_y50.55)
**[33**](#\_page33_x72.00_y50.55)\*\*

Introduction

The first point to make clear is that this API is not standard because the communication
initiative is led by Civitfun and not the integrated system, that is, it is Civitfun who
sends requests to the PMS and the PMS who responds. There is only one request, "Download
files", in which the initiative is taken by the integrated system.

This API is intended for PMS that do not have an API available for Civitfun to integrate
with them.

Therefore, Civitfun Standard3 Check-in & Check-out API is a set of services that
performs check-in and check-out operations. These services are made up of requests, sent
by Civitfun, and responses, returned by the PMS.

The PMS must publish one or more endpoints to which Civitfun will send requests. Once
the PMS receives a request, it must process it and build a response accordingly.

Both the request and response format and the specifications of each of the message
fields are indicated in this document. The "\*" indicates that the field is included in
the request or must be included in the response as either: empty string (“”) or
**_null_**, depending on the field type.

Changelog

| 2021-08-05 | Included Authentication section                                                                                                                                                                                                                                          | A. Ortega, X. Gómez |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| 2021-08-13 | <p>- Added holder field format in Booking>Search By Form>Response.</p><p>●</p><p>Added holderCountry field in Booking>Search By Form>Response.</p><p>- Added case for “Language” in “Data Format”.</p><p>- Changed “String” by “Enum” in fields related to language.</p> | X. Gómez            |
| 2021-08-20 | <p>Added “howMeet” and “customerNotes” in “customFields” object in:</p><p>- Booking>Search By Form>Response</p><p>- Guest>Data Submission>Request</p>                                                                                                                    | X. Gómez            |
| 2021-09-08 | <p>Added “survey” as an option for the “code” field in the file object within the “files” array.</p><p>● Guest>Data Submission>Request</p>                                                                                                                               | X. Gómez            |

Flow

Check-In

Online

- Booking - Search By Form/Unique Identifier
- Payment - Invoicing (Optional)
- Payment - Payment Registration (Optional)
- Guest - Get Legal Texts (Optional)
- Guest - Data Submission
- Check-in - Confirmation

Kiosk

- Booking - Search By Entrance Date/Unique Identifier
- Payment - Invoicing (Optional)
- Payment - Payment Registration (Optional)
- Guest - Get Legal Texts (Optional)
- Guest - Data Submission
- Check-in - Confirmation

Check-out

Online

- Booking - Search By Form/Unique Identifier
- Payment - Invoicing
- Payment - Payment Registration
- Check-out - Confirmation

Kiosk

- Booking - Search By Departure Date/Unique Identifier
- Payment - Invoicing
- Payment - Payment Registration
- Check-out - Confirmation

Authentication

Regarding security in the communication between Civitfun and the integrated system, use
of HTTPS is advisable although it is not a requirement.

First, the integrated must have an endpoint of authentication to which Civitfun will
make a call to obtain an authentication token.

Civitfun will include this token at the headers of the rest of its calls:

- “Authorization: token”

The token will be generated by the integrated with the following characteristics:

- It must be a json web token, [JWT](https://jwt.io/).
- The duration must be at least 15 minutes
- In the Token _payload_, a "publicKey" field will be added. That value will be provided
  by Civitfun (public key)
- Sample:

{“**publicKey**”: “ODTeMMzjIOImp78P”}

- The _signature_ must include a secret key that Civitfun will provide too.
- Sample:

**secretKey** = “bYSaTQ17AOl7a1Pn” HMACSHA256( base64UrlEncode(header) + "." +
base64UrlEncode(payload), **secretKey**)

That token must be saved by the integrated in its systems and verify that Civitfun sends
it correctly in its calls (as mentioned, in all calls except for the authentication and
the get legal texts). It must also be checked that the token is not expired.
**Otherwise, the integrated must return a 401 Unauthorized erro**r.

Headers

- “Civitfun-Standard3-Request: authorization”

Request

- **propertyId**\*: [Integer] property identifier in Civitfun.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **token**\*: [String] authentication token.

Booking

These services facilitate the search for bookings in the PMS, given specific parameters.

Search By Form

It must allow the booking to be found for the following cases:

1. In the check-in process
   1. If the guest has the booking reference/voucher, via direct or OTA/TO, and the
      entrance date.
   1. If the guest does not have the booking reference/voucher, via direct or OTA/TO,
      but does have the entrance date, departure date and name of the holder of the
      booking.
   1. Directly
1. In the check-out process

a. If the guest has the booking reference/voucher, via direct or OTA/TO, and the
departure date.

Based on the booking number (reference number, booking reference or voucher) and the
entrance date, it should be possible to find the booking unequivocally, although
depending on the needs of the PMS, other parameters can be added to the request, such
as: departure date and/or holder of the booking

It is best to use as little data as possible to find the booking.

It should also obtain the arrivals booking list given a date ("Search by entrance date")
and the departures booking list given a date ("Search by departure date"). These
requests are useful at the "kiosk", for check-in and check-out respectively.

The response can return more than one booking if the PMS manages the
sub-bookings/rooms/breakdowns of the same booking as separate bookings or also in the
case of booking references or group vouchers. This is explained in detail at the end of
the next section.

Headers

- "Civitfun-Standard3-Request: booking-searchByForm"
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **bookingCode\***: [String] booking reference in the OTA/TO.
- **entranceDate\***: [String] booking entrance date.
- **departureDate**: [String] booking departure date.
- **bookingHolder**: [String] holder of the booking. If the property is configured in
  Civitfun to search the booking by name of the holder, this field is requested to the
  guest in the form.

Depending on how the PMS manages bookings, there are 3 possible responses:

1. There is no booking: there is no match.
1. There is a booking: there is a match.
1. There are multiple bookings: There is more than one match. In this case, it is
   understood that it usually occurs due to one of the following reasons:
1. _Booking per room_: The PMS manages each room in the booking as an "independent
   booking". Depending on the PMS they can be called: breakdowns, sub-bookings or simply
   rooms.
1. _Group booking_: the PMS manages groups of bookings that come from OTA /TO under the
   same booking reference or voucher.

i. If this is a frequent case with PMS clients, we recommend using the "bookingHolder"
to filter between those bookings.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **bookings**\*: [Array] of booking type objects:
  - **bookingIdentifier\***: [String] unique booking identifier in the PMS.
  - **bookingCode**: [String] booking reference in the OTA/TO.
  - **status\***: [Enum] booking status.
  - **holder\***: [String] holder of the booking. Must be built by the last name
    followed by a comma(“,”) and the given name..
  - Sample: “Doe, Jane”
  - **holderCountry**: [Enum] booking holder’s country.
  - **email**: [String] booking email.
  - **entrance\***: [String] booking entrance date.
  - **entranceTime\***: [String] booking entrance time.
  - **departure\***: [String] booking departure date.
  - **departureTime\***: [String] booking departure time.
  - **adults\***: [Integer] number of adults in the booking.
  - **children\***: [Integer] number of children in the booking.
  - **babies\***: [Integer] number of babies in the booking.
  - **regimeStay**: [String] booking meal plan.
  - **agency**: [String] name of the OTA/TO where the booking was made.
  - **stayAmount**: [Float] booking price.
  - **depositAmount**: [Float] booking deposit amount.
  - **customerNotes**: [String] booking comments.
  - **roomTypes\***: [Array] of roomType objects:
    - id**\***: [String] unique room type identifier in the PMS.
    - name**\***: [String] room type name.
    - assignedRoom**\***: [Object] assigned room, if it has none, its value shall be
      null.
      - _id_: [String] unique room identifier in the PMS of this type, assigned to the
        booking.
      - _name_: [String] room name, of this type, assigned to the booking.
    - capacity**\***: [Integer] maximum number of occupants allowed in the room.
    - emptySlot**\***: [Integer] number of empty slots in the room.
  - **reallocationPropertyId**: [String] property identifier in Civitfun where the
    booking has been relocated.
  - **additionalInfo**: [Array] of replaceTag = {name,value} type objects which is used
    to obtain extra information on the booking that is required to be shown in any of
    the PDF files that are generated or in the check-in confirmation email.
    - name**\***: data name. This is the label that must be inserted into the PDF file
      content or email body for it to be replaced correctly.
    - value**\***: data value.
  - **guestsFilled**: [Boolean] If the value is true, it indicates that the guest data
    is in the "guests" field and should be used to pre-fill in the data forms. If it is
    false, no other steps are required.
  - **guests**: [Array] of guest type objects:
    - id**\***: [String] unique guest identifier in the PMS.
    - position**\***: [Integer] position in the booking. The first position is
      associated with the holder and is represented by 1.
    - email\*: [String] email.
    - lang\*: [Enum] language.
    - name**\***: [String] name.
    - surname**\***: [String] first surname.
    - secondSurname: [String] second surname.
    - gender: [Enum] gender.
    - birthDate: [String] date of birth.
    - nationality: [Enum] nationality.
    - documentType: [Enum] document type.
    - documentNumber: [String] document number.
    - expeditionDate: [String] document issue date.
    - expirationDate: [String] document expiration date.
    - assignedRoom: [Object]
      - _id_: [String] unique room identifier in the PMS, assigned to the guest.
      - _name_: [String] room name in the PMS, assigned to the guest.
    - customFields: [Object].
      - _phone_ [String]
      - _address_ [String]
      - _postalCode_ [String]
      - _city_ [String]
      - _province_ [String]
      - _state_ [String]
      - _country_ [String]
      - _allergy_ [String]
      - _noCommonAllergy_ : [String]
      - _maritalStatus_ [String]
      - _occupation_ [String]
      - _mobilityProblems_ [String]
      - _plateNumber_ [String]
    - _firstTime_ [String]
    - _paymentType_ [String]
    - _environmentalTax_ [String]
    - _hotelInsurance_ [String]
    - _arrivalTime_ [String]
    - _arrivalFlight_ [String]
    - _arrivalFlightTime_ [String]
    - _departureTime_ [String]
    - _departureFlight_ [String]
    - _departureFlightTime_ [String]
    - _howMeet_ [String]
    - _customerNotes_ [String]
  - As the name suggests, these fields are customised and not all properties include
    them in the guest data form. It should not be assumed that all the fields are always
    sent, nor that they are sent in the same order, since it depends on the creation of
    the fields in each property, in the same property the order is maintained.
  - legalFields: [Object].
    - _dataPrivacyPolicy_: [Enum] acceptance of the data privacy policy of the hotel.
    - _dataCommercialUse_: [Enum] acceptance of the commercial use of the data by the
      hotel.
    - _loyaltyProgram_: [Enum] acceptance to join the loyalty program of the hotel.

Search By Unique Identifier

Locates the booking directly as it uses the unique booking identifier in the PMS. Cannot
return more than one booking.

Headers

- "Civitfun-Standard3-Request: booking-searchById"
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **bookingIdentifier\***: [String] unique booking identifier in the PMS.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **bookings**\*: [Array] of a booking type object. The booking type object is identical
  to the one above. If there are no matching results, the array will be empty.

Search By Entrance Date

Obtains all the bookings whose arrival matches the entrance date indicated in the
request.

Headers

- "Civitfun-Standard3-Request: booking-searchByEntranceDate"
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **entranceDate\***: [String] booking entrance date.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **bookings**\*: [Array] of a booking type object. The booking type object is identical
  to

the one above. If there are no matching results, the array will be empty.

Search By Departure Date

Obtains all bookings whose departure coincides with the departure date indicated in the
request.

Headers

- "Civitfun-Standard3-Request: booking-searchByDepartureDate"
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **departureDate\***: [String] booking departure date.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **bookings**\*: [Array] of booking type objects. If there are no matching results, the
  array will be empty.

Payment

This functionality charges the guest for any outstanding charges in the booking at the
time of check-in or check-out. As soon as the online payment is made, the accounts paid
are notified to the PMS.

In the check-in process, the only outstanding account is usually the one related to the
booking cost, although it could include those related to services selected at the time
of booking.

In the check-out process it is more common for there to be more than one outstanding
account.

In both cases, the integrated system controls which accounts are sent to Civitfun to be
paid by the guest.

Invoicing

Headers

- "Civitfun-Standard3-Request: payment-invoicing"
- “Authorization: token”

Request

- **propertyId\***: [Integer] is the property identifier in Civitfun.
- **bookingIdentifier\***: [String] is the unique booking identifier in the PMS.
- **process\*** [Enum]: indicates the process by which the request is made: check-in or
  check-out.
- **lang\***: [Enum] is the language of the guest checking in/checking out that is
  identified in order to receive the translations of the "description", the "accounts",
  and the "concept" of the "charges" if available.
- **guests**: [Array] of guest type objects. It is only used if the calculation of taxes
  is carried out in the PMS and the age of every guest is required. Only the following
  guest object data are included: name, surname, secondSurname, gender, birthDate,
  nationality, documentType, documentNumber, expeditionDate, and expirationDate.
- In this case, the hotel must configure the payment option as "Mandatory with taxes"

or "Optional with taxes" in Civitfun. The payment screen will be displayed when the last
guest checks in, once the ages of all guests in the booking are available.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **currency\***: [String]
- **accounts\***: [Array] of account objects.
- **id\***: [String] account identifier in the PMS.
- **description**: [String] information on the account.
- **amount\***: [Float] account total.
- **charges\***: [Array] is the breakdown of the account into charges.
- **id\***: [String] charge identifier in the PMS.
- **concept\***: [String] name or description of the charge. Must be unique within
  "charges", if not:
- Aggregate the amount of the repeated charges into one amount.
- Include the date and/or time to make it unique.
- **amount\***: [Float] charge price.

Register Payment

Headers

- "Civitfun-Standard3-Request: payment-register"
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **bookingIdentifier\***: [String] unique booking identifier in the PMS.
- **process\*** [Enum]: indicates the process by which the request is made: check-in or
  check-out.
- **paymentToken\***: [String] token of the payment operation performed.
- **paymentCard\***: [Object] is sent if the payment gateway configured by the property
  returns this data.
- type: [Enum] is the type of payment card.
- expirationDate: [String] is the expiration date of the payment card.
- maskedNumber: [String] is the masked payment card number.
- **accountIds\***: [Array] identifiers of paid accounts. They coincide with the "id" of
  objects within "accounts" that are received in the response to the "Billing" request.
- In the check-in process, separate account payments are not allowed, therefore, it is
  assumed that all submitted accounts are paid. Their value will be empty array([]).

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.

Guest

These services send data that guests provide to the PMS during the check-in process.
They also provide files from the check-in process: captured images of documents, the pdf
that is generated in the entry registration, or the pdf of the property contract.

Data Submission

Send the guest data to the PMS. In the response, the PMS returns, for each guest
(idCheckinGuest), the unique identifier in the system (pmsId).

Headers

- "Civitfun-Standard3-Request: guest-sendData"
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **bookingIdentifier\***: [String] is the unique booking identifier in the PMS.
- **guests\***: [Array] of guest type objects.
  - **idCheckinGuest\***: [String] is the unique guest identifier in Civitfun.
  - **id\***: [String] unique guest identifier in the PMS.
  - **position\***: [Integer] is the position in the booking. The first position (0) is
    associated with the holder.
  - **email\***: [String] guest email.
  - **lang\***: [Enum] guest language code.
  - **name\***: [String] is the guest name.
  - **surname\***: [String] is the guest surname.
  - **secondSurname\***: [String] is the guest second surname.
  - **gender\***: [Enum] is the guest gender.
  - **birthDate\***: [String] is the guest date of birth.
  - **nationality\***: [Enum] is the guest nationality.
  - **documentType\***: [Enum] is the document type.
  - **documentNumber\***: [String] is the document number.
  - **expeditionDate\***:[String] is the document issue date.
  - **expirationDate\***: [String] is the document expiration date.
  - **assignedRoom\***: [Object] if the guest has been pre-assigned a room or has
    selected a room during the check-in process, it is different from null.
    - id: [String] unique identifier in the PMS of the specific room assigned to the
      guest.
    - name: [String] name in the PMS of the specific room assigned to the guest.
  - **customFields\***: [Object] only requested fields in the guest data form are sent.
    These fields must be previously configured in Civitfun and must follow the
    nomenclature included herein. In order to add a field that is not included in this
    list, request it to support. The integrated system must make the mapping between the
    "customField" in Civitfun and its homonym in the PMS.
    - phone [String]
    - address [String]
    - postalCode [String]
    - city [String]
    - province [String]
    - state [String]
    - country [String]
    - allergy [String]
    - noCommonAllergy [String]
    - maritalStatus [String]
    - occupation [String]
    - mobilityProblems [String]
    - plateNumber [String]
    - firstTime [String]
    - paymentType [String]
    - environmentalTax [String]
    - hotelInsurance [String]
    - arrivalTime [String]
    - arrivalFlight [String]
    - arrivalFlightTime [String]
    - departureTime [String]
    - departureFlight [String]
    - departureFlightTime [String]
    - howMeet [String]
    - customerNotes [String]
    - As the name suggests, these fields are customised and not all properties include
      them in the guest data form. It should not be assumed that all the fields are
      always sent, nor that they are sent in the same order, since it depends on the
      creation of the fields in each property, in the same property the order is
      maintained.
  - **legalFields\***: [Object]
    - dataPrivacyPolicy**\***: [Enum] is the acceptance of the hotel's data policy.
    - dataCommercialUse**\***: [Enum] is the acceptance of the commercial use of data by
      the hotel.
    - loyaltyProgram**\***: [Enum] is the acceptance to join the hotel loyalty program.
  - **files\***: [Array] of file type objects.
    - code**\***: [Enum] is the code that defines the type of file: documentFront,
      documentBack, guestPhoto, signature, registrationCard, propertyContract, survey.
    - type**\***: [Enum] is the type of file: jpeg, blob, pdf.
    - token**\***: [String] is the identifier of the file used to download the resource.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **guestIds**: [Array] of objects:
- **idCheckinGuest\***: [String] is the unique guest identifier in Civitfun.
- **pmsId\***: [String] is the unique identifier of the guest in the PMS.

Download File

In this type of request, the integrated PMS takes the initiative and requests to
download a file linked to the check-in process of a guest by using a token.

The token corresponding to each of the guest's files is sent in the "Send data" service,
in the "files" field, and the PMS then requests the files from Civitfun, one per
request.

In the request headers must add a token, _[JWT_](https://jwt.io/)\*, with this format:

- In the Token _payload_, a "publicKey" field will be added. That value will be provided
  by Civitfun (public key)
- Sample:

{“**publicKey**”: “ODTeMMzjIOImp78P”}

- The _signature_ must include a secret key that Civitfun will provide too.
- Sample:

**secretKey** = “bYSaTQ17AOl7a1Pn” HMACSHA256( base64UrlEncode(header) + "." +
base64UrlEncode(payload), **secretKey**)

Url

- https://integration-hub.civitfun.com/pms/standard3/guest/get-file

Headers

- "Civitfun-Standard3-Request: guest-getFile"
- “Authorization: token”

Request

- **propertyId\***: [String] property identifier in Civitfun
- **bookingIdentifier\***: [String] unique booking identifier in the PMS.
- **token\***: [String] identifier of the file used to download the resource.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **file**\*: [String] base64 encoded file.

Get Legal Texts

It is advisable to use the Civitfun tool to configure the legal texts corresponding to
the property contract and registration card as standard. However, this service should
only be used to obtain the plain text or HTML if the property has a highly customized
contract and/or entry registration for each booking and guest, and if it is strictly
necessary to collect them from the PMS.

These texts or HTML will be displayed during the check-in process in the legal texts
screen prior to the signature screen, as well as in the PDF files generated for the
property contract and entry registration.

Headers

- "Civitfun-Standard3-Request: guest-contract"
- “Authorization: token”

Request

- **propertyId\***: [String] property identifier in Civitfun.
- **bookingIdentifier\***: [String] unique booking identifier in the PMS.
- **guest\***: [Object] guest type object.
- The object does not include the "files" field.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.
- **propertyContract**\*: [Object] if empty, its value should be null.
  - type: [Enum] indicates whether the "content" field is plain text or HTML.
  - content: [String] plain text or HTML.
- **registrationCard**\*: [Object] if empty, its value should be null.
- type: [Enum] indicates whether the "content" field is plain text or HTML.
- content: [String] plain text or HTML.

Check-In

Confirmation

This functionality notifies the integrated system that all required guests have checked
in through Civitfun.

Headers

- “Civitfun-Standard3-Request: checkin-confirm”
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **bookingIdentifier\***: [String] unique booking identifier in the PMS.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.

Check-out

Confirmation

This functionality notifies the integrated system that the booking has been checked out
through Civitfun. The booking check-out is deemed complete when there are no outstanding
accounts to be paid.

Headers

- “Civitfun-Standard3-Request: checkout-confirm”
- “Authorization: token”

Request

- **propertyId\***: [Integer] property identifier in Civitfun.
- **bookingIdentifier\***: [String] unique booking identifier in the PMS.

Response

- **success**\*: [Boolean] If there is an error, it returns false, otherwise it returns
  true.
- **message**\*: [String] information regarding the error that has occurred. If none has
  occurred, it can return an empty text.

Data Format

Do not enter and send values, whatever their data type, such as the following:

- JSON
  - If it is Integer/Float/Object: Null.
    - Example: "assignedRoom": null
  - If it is a String: Empty string ("").
    - If it is a date or time: include a value.
  - If it is a Boolean: false is taken as default value.
  - If it is an Array: Empty Array ([]).
- SOAP
  - Irrespective of type: Empty string ("")
  - Example: <assignedRoom></assignedRoom>

Data types

String

- Date
  - Format: YYYY-MM-DD (<https://en.wikipedia.org/wiki/ISO_8601>)
- Time
- Format: hh:mm (<https://en.wikipedia.org/wiki/ISO_8601>)
- 12:00 - 11:59
- Currency
- Format: <https://en.wikipedia.org/wiki/ISO_4217>

Integer Float

- Number of decimal places: maximum 2.
- 0
- 15.99

Boolean

- true
- false

Enum

- Booking status
  - canceled
  - noShow
  - confirmed
  - checkedIn
  - checkedOut
- Gender
  - M: Male
  - F: Female
  - U: Undefined
- Nationality
  - Format: <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3>
- Language
  - Format: <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>
- Document type
  - passport: passport
  - idCard: identity document or card
  - residencePermit: residence permit
  - drivingLicence: driving licence
  - other: other
- Legal fields: checkbox fields.
  - 0: not marked
  - 1: marked
- File code
  - documentFront
  - documentBack
  - guestPhoto
  - signature
  - registrationCard
  - propertyContract
  - survey
- File type
  - jpeg
  - blob
  - pdf
- Process
  - check-in
  - check-out
- Card type
  - visa
  - mastercard
  - amex
  - discover
  - diners
  - jcb
  - other
- Type of contract content
  - text
  - html

Object Array

Additional documentation

Additional documentation is available, where detailed examples for the set of requests
and responses of the **Civitfun Standard3 Check-in & Check-out API** can be found. Click
on the following link to access it:

- [Postman documentation](https://documenter.getpostman.com/view/2136281/Tz5s5wr1)

● 35
