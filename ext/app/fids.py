from flask import current_app as app

from ext.app.eve_helper import eve_response, eve_error_response
from eve.methods.post import post_internal
from eve.methods.get import getitem_internal, get_internal
from eve.methods.patch import patch_internal
from eve.methods.put import put_internal

from dateutil import parser
from ext.app.helpers import _get_merged_from

FIDS = ['fai', 'flydrone', 'mwl', 'tms']


def fid_exists(person_id, fid_type):
    r = get_fid(person_id, fid_type)
    if r is not None:
        return True

    return False


def get_fid(person_id, fid_type):
    try:
        person_ids = list(set(_get_merged_from(person_id) + [person_id]))
        response, _, _, status = getitem_internal(resource='persons_fids', **{'person_id': {'$in': person_ids}, 'fid_type': fid_type})
        if status == 200:
            return response

    except:
        pass

    return None


def get_fids(person_id):
    person_ids = list(set(_get_merged_from(person_id) + [person_id]))
    response, _, _, status, _ = get_internal(resource='persons_fids', **{'person_id': {'$in': person_ids}})
    if status == 200:
        fids = {}

        for fid in response.get('_items', []):
            fids[fid['fid_type']] = fid['data']

        return fids
    return None


def _create_fid(person_id, fid_type, data):
    data = {'person_id': person_id, 'fid_type': fid_type, 'data': data}
    response, _, _, status, _ = post_internal(resource='persons_fids',
                                              payl=data,
                                              skip_validation=True)

    return status, response


def create_fid(person_id, fid_type, data):
    """
    Add new fid_type to existing fid
    :param person_id:
    :param fid_type:
    :param data:
    :return:
    """
    return update_fid(person_id, fid_type, data)


def update_fid(person_id, fid_type, data):
    fid = get_fid(person_id, fid_type)

    if fid is None:
        return _create_fid(person_id, fid_type, data)

    else:
        lookup = {'_id': fid['_id']}
        resp, _, _, status = patch_internal('persons_fids', {'data': data}, False, True, **lookup)
        return status, resp

    return 500, None