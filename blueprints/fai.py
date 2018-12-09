import requests
from urllib.parse import urlencode
import base64
from flask import Blueprint, current_app as app, request, Response, abort, jsonify
from ext.auth.decorators import require_token
from ext.auth.clients import FAI_USERNAME, FAI_PASSWD, FAI_URL
from ext.app.eve_helper import eve_response, eve_abort

Fai = Blueprint('FAI resources', __name__)


def make_params():
    params = {'auth_username': FAI_USERNAME,
              'auth_password': base64.b64encode(FAI_PASSWD), 'country': 'NOR'}
    return params


@Fai.route("/licenses", methods=['GET'])
@require_token()
def get_licenses():
    response = requests.get('{}/licences?{}'.format(FAI_URL, urlencode(make_params())))

    return eve_response(response.json(), response.status_code)


def search_licenses():
    """
    GET licences?auth_username=&auth_password=&nac_org=&country=&valid_from=&valid_to=&search_name=&search_number=&discipline=&include_invalid=&limit_start=&limit_length=
    auth_username sportinglicences2.fai.org username String
    auth_password password, base64 encoded String
    nac_org licences-lic.idissue-lic String
    country utilisateur.iPaysUtilisateur or 3 Letter IOC Code eg. FIN,SWE String
    valid_from licences-lic.dateissued-lic String
    valid_to licences-lic.validuntil-lic String
    search_name licencee-lip.givenname-lip, licencee-lip.surname-lip String
    search_number licences-lic.idlicencee-lic , licences-lic.licencenumber-lic , licences-lic.idlicence String
    discipline licences-lic.idsport-lic or discipline text as shown in http://sl-test.fai.org/sl/search String
    include_invalid 1, if include expired licenes, 0 if NOT to include expired licenes, ignored when either valid-from or valid-to is passed String
    limit_start Db select limit start String
    limit_length Db select limit lengthString

    :return:
    """

def get_details():
    """
    GET licence/idlicence?auth_username=&auth_password=

    idlicence licence id String
    auth_username sportinglicences2.fai.org username String
    auth_password password, base64 encoded String
    :return:
    """

def create():
    """
    GET create?auth_username=&auth_password=&idlicencee=&licencee_firstname=&licencee_middlename=&licencee_lastname=&licencee_gender=&licencee_birthdate=&licencee_nationality=&licencee_residencecountry=&address1=&address2=&address3=&address_country=&licencee_email=&phone_home=&phone_office=&phone_mobile=&licence_number=&dateissued=&validuntil=&discipline=

    auth_username sportinglicences2.fai.org username String
    auth_password password, base64 encoded String
    idlicencee If empty, new pilot will be created. Otherwise pilot with idlicencee id be updated String
    licencee_firstname String
    licencee_middlename String
    licencee_lastname String
    licencee_gender M or F String
    licencee_birthdate Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    licencee_nationality Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_residencecountry Country ID or 3 Letter IOC Code eg. FIN,SWE String
    address1 Address text 1 String
    address2 Address text 2 String
    address3 Address text 3 String
    address_country Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_email String
    phone_home String
    phone_office String
    phone_mobile String
    licence_number Licence Number, String
    dateissued Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    validuntil Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    discipline Sport ID or discipline text as shown in http://sl-test.fai.org/sl/search
    :return:
    """

def update():
    """
    GET create?auth_username=&auth_password=&idlicence=&idlicencee=&licencee_firstname=&licencee_middlename=&licencee_lastname=&licencee_gender=&licencee_birthdate=&licencee_nationality=&licencee_residencecountry=&address1=&address2=&address3=&address_country=&licencee_email=&phone_home=&phone_office=&phone_mobile=&licence_number=&dateissued=&validuntil=&discipline=
    auth_username sportinglicences2.fai.org username String
    auth_password password, base64 encoded String
    idlicencee If empty, new pilot will be created. Otherwise pilot with idlicencee id be updated String
    licencee_firstname String
    licencee_middlename String
    licencee_lastname String
    licencee_gender M or F String
    licencee_birthdate Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    licencee_nationality Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_residencecountry Country ID or 3 Letter IOC Code eg. FIN,SWE String
    address1 Address text 1 String
    address2 Address text 2 String
    address3 Address text 3 String
    address_country Country ID or 3 Letter IOC Code eg. FIN,SWE String
    licencee_email String
    phone_home String
    phone_office String
    phone_mobile String
    licence_number Licence Number, String
    dateissued Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    validuntil Date in the format YYYY-MM-DD [ example: 2016-01-18 ] String
    discipline Sport ID or discipline text as shown in http://sl-test.fai.org/sl/search
    """
