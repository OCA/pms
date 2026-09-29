INE occupancy surveys
~~~~~~~~~~~~~~~~~~~~~

The INE runs a monthly occupancy survey per kind of establishment. Two of
them accept an XML questionnaire and are the ones this module builds, the
hotel establishments survey (EOH) and the tourist apartments one (EOAP).
Which of the two is built comes from the INE category of the property, so
there is nothing else to choose.

On the property, under the INE settings:

#. **Tourism number**: the registration number in the tourism registry.
#. **Category**: the type and category the establishment is listed under in
   the INE directory. Its survey type decides the questionnaire.
#. **Beds available excluding extra beds**: the places of the directory,
   counting fixed beds only.
#. **Staff**: permanent, temporary and unpaid.
#. **Order number**: eleven characters, printed on the questionnaire. It is
   fixed for the establishment, so it is kept here once filled in. The
   control code is single use and is never stored.
#. **Informant**: name, job position, phone and email. Only the tourist
   apartments survey carries them, where they are mandatory.

The property lists what is still missing in *INE configuration warnings*,
so the whole configuration can be completed before trying to build a file.

Rooms reported to the survey are the ones flagged *In INE*. For the tourist
apartments survey each of them also carries a typology (studio, 2-4 pax,
4-6 pax or other); left empty, it is inferred from the capacity of the room.

Provinces and countries are taken from the lists the INE publishes next to
the survey schemas, which do not always match the ones of Odoo:

* ``res.country.state`` carries the province literal of the specification,
  limited to 25 characters, seeded for the 52 Spanish provinces.
* ``res.country`` carries a code of its own for the countries the INE does
  not code as ISO 3166-1 alpha-3 does.

Files are built after the schema the INE publishes, which declares no
namespace. A questionnaire asking for the namespace-qualified variant
instead is served by setting the namespace in the system parameters
``pms_l10n_es.ine_xml_namespace_hotel`` or
``pms_l10n_es.ine_xml_namespace_apartments``.
