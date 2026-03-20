from datetime import datetime, date
from dateutil import parser, tz
from flask import current_app as app, g
from eve.methods.get import get_internal, getitem_internal
from operator import itemgetter
import re

LOCAL_TIMEZONE = "Europe/Oslo"  # UTC
tz_utc = tz.gettz('UTC')
tz_local = tz.gettz(LOCAL_TIMEZONE)


def _get_end_of_year():
    return datetime(datetime.utcnow().year, 12, 31, 23, 59, 59, 999999).replace(tzinfo=tz_local)


def _get_end_of_january():
    """End of jan next year"""
    return datetime(datetime.utcnow().year + 1, 1, 31, 23, 59, 59, 999999).replace(tzinfo=tz_local)


def _fix_naive(date_time):
    if date_time is not None and isinstance(date_time, datetime) is False:
        # if isinstance(date_time, str):
        try:
            date_time = parser.parse(date_time)
        except Exception as e:
            app.logger.error(f'Fixing naive date time failed: {date_time}')
            app.logger.exception(e)
            date_time = None

    if isinstance(date_time, datetime):
        #if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
        """self.org_created is naive, no timezone we assume UTC"""
        # date_time = date_time.replace(tzinfo=tz_local)
        # date_time = (date_time.replace(tzinfo=None) - date_time.utcoffset()).replace(tzinfo=tz_utc)
        # All datetime is local from nif
        offset = date_time.replace(tzinfo=tz_local).utcoffset()
        date_time = (date_time.replace(tzinfo=None) - offset).replace(tzinfo=tz_utc)

    return date_time


def _get_now():
    return datetime.utcnow().replace(tzinfo=tz_utc)


def _get_person(person_id) -> dict:
    """Get person from persons internal

    :param person_id: Person id
    :type person_id: int
    :return org: Returns the person given
    :rtype: dict
    """
    if person_id is not None:

        person, _, _, status, _ = get_internal('persons', **{'id': person_id})

        if status == 200:
            if '_items' in person and len(person['_items']) == 1:
                return person['_items'][0]

    return {}


def _get_merged_from(person_id) -> list:
    """Get person ids merged to this person id

    :param person_id:
    :return:
    """
    from domain.persons import agg_merged_from, RESOURCE_COLLECTION

    try:
        merged_from_ids = []

        pipeline = agg_merged_from.get('datasource', {}).get('aggregation', {}).get('pipeline', [])
        pipeline[0]["$match"]["id"] = person_id
        pipeline[2]["$graphLookup"]["startWith"] = person_id

        datasource = agg_merged_from.get('datasource', {}).get('source', RESOURCE_COLLECTION)

        persons = app.data.driver.db[datasource]

        result = list(persons.aggregate(pipeline))

        if len(result) == 1:
            result = result[0]
            merged_from_ids = result.get('merged_from', [])

    except Exception as e:
        app.logger.exception('Aggregation with database layer failed for person_id {}'.format(person_id))

    return merged_from_ids


def _compare_list_of_dicts(l1, l2, dict_id='id') -> bool:
    """Sorts lists then compares on the given id in the dicts
    :param l1: list of dicts
    :type l1: list(dict)
    :param l2: list of dicts
    :type l2: list(dict)
    :param dict_id: The id for the dicts
    :type dict_id: any
    :return: True if difference, False if not or can't decide
    """
    if len(l1) != len(l2):
        return True

    try:
        list_1, list_2 = [sorted(l, key=itemgetter(dict_id)) for l in (l1, l2)]
        pairs = zip(list_1, list_2)
        if any(x != y for x, y in pairs):
            return True
        else:
            return False  # They are equal
    except:
        return True  # We do not know if difference


def _compare_list_of_dicts_no_id(l1, l2):
    return [d for d in l1 if d not in l2] == []


def _compare_lists(l1, l2) -> bool:
    """Just compare set(list)
    :param l1: list
    :param l2: list
    :return: True if difference, False if """
    return set(l1) != set(l2)


def _get_org(org_id) -> dict:
    """Get org from organizations internal

    :param org_id: Organization id
    :type org_id: int
    :return org: Returns the organization
    :rtype: dict
    """

    org, _, _, status, _ = get_internal('organizations', **{'id': org_id})

    if status == 200:
        if '_items' in org and len(org['_items']) == 1:
            return org['_items'][0]

    return {}


def _get_functions_types(type_id) -> dict:
    """Get org from organizations internal

    :param org_id: Organization id
    :type org_id: int
    :return org: Returns the organization
    :rtype: dict
    """

    function_type, _, _, status, _ = get_internal('functions_types', **{'id': type_id})

    if status == 200:
        if '_items' in function_type and len(function_type['_items']) == 1:
            return function_type['_items'][0]

    return {}


class DateExtractor:

    DATE_REGEX = re.compile(
        r"""
        \b(
            # ISO / numeric formats
            \d{4}[-./]\d{1,2}[-./]\d{1,2} |
            \d{1,2}[-./]\d{1,2}[-./]\d{4} |
            \d{8} |
    
            # 9 Jan 2026 / 09 Jan 26
            \d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{2,4} |
    
            # January 9, 2026
            (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4}
        )\b
        """,
        re.IGNORECASE | re.VERBOSE,
    )


    def normalize_date_string(s: str) -> str:
        return s.replace(".", "-").replace("/", "-").strip()


    def try_parse_iso(s: str):
        try:
            parts = s.split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                y, m, d = map(int, parts)
                return date(y, m, d)
        except:
            pass
        return None


    def try_parse_eu(s: str):
        try:
            parts = s.split("-")
            if len(parts) == 3 and len(parts[2]) == 4:
                d, m, y = map(int, parts)
                return date(y, m, d)
        except:
            pass
        return None


    def try_parse_compact(s: str):
        try:
            if len(s) == 8 and s.isdigit():
                return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except:
            pass
        return None


    def try_parse_textual(s: str):
        """Handle '9 Jan 2026', 'January 9, 2026', etc."""
        try:
            dt = parser.parse(s, dayfirst=True, yearfirst=True, fuzzy=True)

            # Fix 2-digit year ambiguity (dateutil can guess weirdly)
            if dt.year < 100:
                dt = dt.replace(year=2000 + dt.year if dt.year < 50 else 1900 + dt.year)

            return dt.date()
        except:
            return None


    def extract_dates(text: str):
        matches = DATE_REGEX.findall(text)
        results = []

        for raw in matches:
            s = normalize_date_string(raw)

            parsed = (
                    try_parse_iso(s)
                    or try_parse_compact(s)
                    or try_parse_eu(s)
                    or try_parse_textual(raw)  # use original for text parsing
            )

            if parsed:
                results.append(parsed)

        return sorted(set(results))
