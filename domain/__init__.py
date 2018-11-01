import ka_clubs, ka_competence, ka_members, ka_orgs, ka_licenses, ka_org_activity
import persons
import integration_users, integration_changes
import organizations, organization_types, functions, function_types, competences, competences_types, licenses, \
    licenses_types

DOMAIN = {
    "ka/clubs": ka_clubs.definition,
    "ka/members": ka_members.definition,
    "ka/orgs": ka_orgs.definition,
    "ka/orgs/activity": ka_org_activity.definition,
    "ka/competences": ka_competence.definition,
    "ka/licenses": ka_licenses.definition,
    "organizations": organizations.definition,
    "organizations/types/count": organizations.agg_count_types,
    "organizations/types": organization_types.definition,
    "functions": functions.definition,
    "functions/types": function_types.definition,
    "competences": competences.definition,
    "competences/types": competences_types.definition,
    "licenses": licenses.definition,
    "licenses/types": licenses_types.definition,
    "integration/users": integration_users.definition,
    "integration/users/clubs": integration_users.agg_count_clubs,
    "integration/changes": integration_changes.definition,
    "integration/changes/types": integration_changes.agg_count_entity_types,
    "integration/changes/clubs": integration_changes.agg_count_clubs,
    "persons": persons.definition,
    # "values/aggregation": aggregation.minmax
}
