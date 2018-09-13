 
import ka_clubs, ka_competence, ka_members, ka_orgs, ka_licenses, ka_org_activity
import organizations, organization_types, functions, function_types, integration, changes, changes_stream, persons

DOMAIN = {
    "ka/clubs": ka_clubs.definition,
    "ka/members": ka_members.definition,
    "ka/orgs": ka_orgs.definition,
    "ka/orgs/activity": ka_org_activity.definition,
    "ka/competences": ka_competence.definition,
    "ka/licenses": ka_licenses.definition,
    "organizations": organizations.definition,
    "organizations/types": organization_types.definition,
    "functions": functions.definition,
    "functions/types": function_types.definition,
    "integration": integration.definition,
    "integration/changes": changes.definition,
    "integration/changes/stream": changes_stream.definition,
    "persons": persons.definition,
    #"values/aggregation": aggregation.minmax
}
