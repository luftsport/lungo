import ka_clubs, ka_competence, ka_members, ka_orgs, ka_licenses, ka_org_activity
import persons, persons_search
import integration_users, integration_changes
import organizations, organization_types
import functions, function_types
import competences, competences_types
import licenses, licenses_types

# import test, test_ref

DOMAIN = {
    # Tests Only local
    # "test": test.definition,
    # testref": test_ref.definition,
    # KA
    "ka/clubs": ka_clubs.definition,
    "ka/members": ka_members.definition,
    "ka/orgs": ka_orgs.definition,
    "ka/orgs/activity": ka_org_activity.definition,
    "ka/competences": ka_competence.definition,
    "ka/licenses": ka_licenses.definition,

    # Persons
    "persons": persons.definition,
    "persons/process": persons.process_definition,
    "persons/search": persons_search.definition,
    "persons/gender": persons.agg_count_gender,
    # Organization
    "organizations": organizations.definition,
    "organizations/process": organizations.process_definition,
    "organizations/types": organization_types.definition,
    "organizations/types/count": organizations.agg_count_types,
    # Functions
    "functions": functions.definition,
    "functions/process": functions.process_definition,
    "functions/types": function_types.definition,
    "functions/types/count": functions.agg_count_types,
    # Competences
    "competences": competences.definition,
    "competences/process": competences.process_definition,
    "competences/types": competences_types.definition,
    "competences/codes": competences.agg_count_codes,
    # Licenses
    "licenses": licenses.definition,
    "licenses/process": licenses.process_definition,
    "licenses/types": licenses_types.definition,
    # Integration
    "integration/users": integration_users.definition,
    "integration/users/clubs": integration_users.agg_count_clubs,
    "integration/changes": integration_changes.definition,
    "integration/changes/entity/types": integration_changes.agg_count_entity_types,
    "integration/changes/clubs": integration_changes.agg_count_clubs,
    "integration/changes/status": integration_changes.agg_count_statuses,
    "integration/changes/change/types": integration_changes.agg_count_change_types,

    # "values/aggregation": aggregation.minmax
}
