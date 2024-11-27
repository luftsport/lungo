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
import test
import payments
import translate_persons
import translate_organizations
# Airports OurAirports
import aip_airports
import aip_frequencies
import aip_runways
import aip_navaids
import aip_countries
import aip_regions
# import openaip_airports
import aip_airspaces
# Geo
import geo_countries
import geo_admin
# ADS data from flightradar24
# import ads
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
    "persons_merged_from": persons.agg_merged_from,
    "persons_age_distribution": persons.agg_age_distribution,
    "persons_age_gender_bucket_distribution": persons.agg_age_gender_bucket_distribution,

    # Custom Persons

    # Persons test for error id
    # "test": test.definition,

    # Organization
    "organizations": organizations.definition,
    "organizations_process": organizations.process_definition,
    "organizations_search": organizations.search_definition,
    "organizations_types": organization_types.definition,
    "organizations_types_count": organizations.agg_count_types,
    "organizations_get_children": organizations.agg_get_children,
    "organizations_get_parents": organizations.agg_get_parents,
    "organizations_get_by_activity": organizations.agg_get_org_by_activity_and_org_types,

    # Functions
    "functions": functions.definition,
    "functions_process": functions.process_definition,
    "functions_search": functions.search_definition,
    "functions_types_count": functions.agg_count_types,
    "functions_types_org_count": functions.agg_count_types_org,
    "functions_types_activity_count": functions.agg_count_types_activity,
    "functions_get_persons_by_type_and_orgs": functions.agg_get_persons_by_type_and_orgs,
    "functions_memberships_count": functions.agg_count_members_on_date,
    "functions_memberships_disciplines_count": functions.agg_count_members_in_disciplines,
    # Functions types
    "functions_types": function_types.definition,
    "functions_types_search": function_types.search_definition,

    # Competences
    "competences": competences.definition,
    "competences_process": competences.process_definition,
    "competences_codes": competences.agg_count_codes,
    "competences_types_count": competences.agg_count_types,
    "competences_count_types_by_year": competences.agg_count_types_by_year,
    "competences_persons_count": competences.agg_count_persons,
    # Competences Types
    "competences_types": competences_types.definition,
    "competences_types_search": competences_types.search_definition,
    "competences_types_meta_count": competences_types.agg_count_meta_types,

    # Licenses
    "licenses": licenses.definition,
    "licenses_process": licenses.process_definition,
    "licenses_types": licenses_types.definition,
    "licenses_types_search": licenses_types.search_definition,

    # Payments
    "payments": payments.definition,
    "payments_process": payments.process_definition,
    "payments_total_per_year": payments.payments_total_per_year,

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
    "integration_changes_aggregate_day_hour": integration_changes.agg_count_change_day_hour,
    "integration_changes_aggregate_errors_group": integration_changes.agg_count_and_sort_errors,

    # Resources
    "activities": activities.definition,
    "activities_search": activities.search_definition,
    "countries": countries.definition,
    "countries_search": countries.search_definition,
    "counties": counties.definition,
    "counties_search": counties.search_definition,
    "licenses_status": licenses_status.definition,

    # Translations Melwin to NIF Id's
    "translate_persons": translate_persons.definition,
    "translate_persons_process": translate_persons.process_definition,
    "translate_organizations": translate_organizations.definition,
    "translate_organizations_process": translate_organizations.process_definition,

    # Airports and stuff
    "aip_airports": aip_airports.definition,
    "aip_airspaces": aip_airspaces.definition,
    "aip_frequencies": aip_frequencies.definition,
    "aip_runways": aip_runways.definition,
    "aip_navaids": aip_navaids.definition,
    "aip_countries": aip_countries.definition,
    "aip_regions": aip_regions.definition,
    # "openaip_airports": openaip_airports.definition,

    # Geo
    "geo_countries": geo_countries.definition,
    "geo_admin": geo_admin.definition,

    # ADS Data
    #"ads": ads.definition,
    #"ads_process": ads.process_definition,

}
