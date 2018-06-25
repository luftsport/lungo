 
import ka_clubs, ka_competence, ka_members, ka_orgs, organizations, organization_types, ka_licenses

DOMAIN = {
    "ka/clubs": ka_clubs.definition,
    "ka/members": ka_members.definition,
    "ka/orgs": ka_orgs.definition,
    "ka/competences": ka_competence.definition,
    "ka/licenses": ka_licenses.definition,
    "organizations": organizations.definition,
    "organization/types": organization_types.definition,
    #"values/aggregation": aggregation.minmax
}
