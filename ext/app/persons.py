from eve.methods.patch import patch_internal
from eve.methods.get import get_internal
from flask import current_app as app
from datetime import datetime


def deregister_person(person: dict) -> bool:
    """ Deregister a person by setting
    :param person_id: ID of the person to deregister
    :return: None
    """
    app.logger.info(f"Deregistering person {person['_id']}")

    end_competences(person)
    end_functions(person)

    # Hard deregister
    new_person = {}
    if 'functions' in person:
        new_person['functions'] = []
    if 'licenses' in person:
        new_person['licenses'] = []
    if 'competences' in person:
        new_person['competences'] = []
    if 'activities' in person:
        new_person['activities'] = []
    if 'clubs' in person:
        new_person['clubs'] = []
    if 'memberships' in person:
        new_person['memberships'] = []
    if 'magazines' in person:
        new_person['magazines'] = []
    if 'federation' in person:
        new_person['federation'] = []

    if len(new_person.keys()) > 0:
        lookup = {'_id': person['_id']}
        resp, _, _, status = patch_internal('persons_process',
                                            new_person,
                                            False,
                                            True,
                                            **lookup)
        if status in [200, 201, 204]:
            return True

    app.logger.error(f"Failed to deregister person {person['_id']}: {resp}")
    return False
    # raise Exception(f"Failed to deregister person {person['_id']}: {resp}")


def end_functions(person: dict) -> bool:
        """ End all functions of a person by setting their end date to today
        :param person_id: ID of the person to end competences for
        :return: None
        """
        app.logger.info(f"Ending functions for person {person['_id']}")
        lookup = {'person_id': person['_id'], "$or": [{"to_date": {"$gt": datetime.utcnow().isoformat() + 'Z'}}, {"to_date": {"$exists": False}}]}
        functions, _, _, status, _ = get_internal('functions', **lookup)

        if status == 200:
            for func in functions['_items']:
                pld = {'to_date': datetime.utcnow().date().isoformat() + 'Z', 'is_passive': True}
                resp, _, _, status = patch_internal('functions_process',
                                                    pld,
                                                    False,
                                                    True,
                                                    **{'_id': func['_id']})
                del pld
                if status not in [200, 204]:
                    app.logger.error(f"Failed to end competence {func['_id']} for person {person['_id']}: {resp}")

            return True

        return False


def end_competences(person: dict) -> bool:
    """ End all competences of a person by setting their end date to today
    :param person_id: ID of the person to end competences for
    :return: None
    """
    app.logger.info(f"Ending competences for person {person['_id']}")
    lookup = {'person_id': person['_id'], "passed": True, "valid_until": {"$gt": datetime.utcnow().isoformat() + 'Z'}}
    competences, _, _, status, _ = get_internal('competences', **lookup)

    if status == 200:
        for competence in competences['_items']:
            pld = {'valid_until': datetime.utcnow().date().isoformat() + 'Z'}
            resp, _, _, status = patch_internal('competences_process',
                                                pld,
                                                False,
                                                True,
                                                **{'_id': competence['_id']})
            del pld
            if status not in [200, 204]:
                app.logger.error(f"Failed to end competence {competence['_id']} for person {person['_id']}: {resp}")

        return True

    return False
