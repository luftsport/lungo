import ka_clubs, ka_competence, ka_members, ka_orgs, ka_licenses, ka_org_activity
import persons
import integration_users, integration_changes
import organizations, organization_types
import functions, function_types
import competences, competences_types
import licenses, licenses_types
import countries, counties
import licenses_status
import licenses_types
import activities

# import test, test_ref

DOMAIN = {
    # Tests Only local
    # "test": test.definition,
    # testref": test_ref.definition,

    # KA
    "ka_clubs": ka_clubs.definition,
    "ka_members": ka_members.definition,
    "ka_members_activities": ka_members.agg_count_activities,
    "ka_members_activities_member": ka_members.agg_count_member_activities,
    "ka_orgs": ka_orgs.definition,
    "ka_orgs_activity": ka_org_activity.definition,
    "ka_competences": ka_competence.definition,
    "ka_licenses": ka_licenses.definition,

    # Persons
    "persons": persons.definition,
    "persons_process": persons.process_definition,
    "persons_search": persons.search_definition,
    "persons_gender": persons.agg_count_gender,

    # Organization
    "organizations": organizations.definition,
    "organizations_process": organizations.process_definition,
    "organizations_types": organization_types.definition,
    "organizations_types_count": organizations.agg_count_types,

    # Functions
    "functions": functions.definition,
    "functions_process": functions.process_definition,
    "functions_types_count": functions.agg_count_types,
    "functions_types": function_types.definition,

    # Competences
    "competences": competences.definition,
    "competences_process": competences.process_definition,
    "competences_types": competences_types.definition,
    "competences_codes": competences.agg_count_codes,

    # Licenses
    "licenses": licenses.definition,
    "licenses_process": licenses.process_definition,
    "licenses_types": licenses_types.definition,

    # Integration Users
    "integration_users": integration_users.definition,
    "integration_users_clubs": integration_users.agg_count_clubs,

    # Integration Changes
    "integration_changes": integration_changes.definition,
    "integration_changes_entity_types": integration_changes.agg_count_entity_types,
    "integration_changes_clubs": integration_changes.agg_count_clubs,
    "integration_changes_status": integration_changes.agg_count_statuses,
    "integration_changes_change_types": integration_changes.agg_count_change_types,
    "integration_changes_aggregate_day": integration_changes.agg_count_change_day,
    "integration_changes_aggregate_hour": integration_changes.agg_count_change_hour,

    # Resources
    "activities": activities.definition,
    "countries": countries.definition,
    "counties": counties.definition,
    "licenses_status": licenses_status.definition,
}
