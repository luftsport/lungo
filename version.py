__version_info__ = ('1', '2', '1')

"""
VERSION HISTORY

1.2.1
- Removal of most legacy ka
- NEW nif-rest-api-client integration replaces ka
- FAI external license handling keeping sporting licenses in sync
- Added domain for ads data 
- NEW simpler markup for client resource access

1.1.6 hotfix
- missing auth req

1.1.5 hotfix
- person competences object completely empty if no competences

1.1.4 hotfix
- reenabled disabled chenge message generation

1.1.3
- NEW ads domain file
- Converted nif blueprint to use nif rest api as backend

1.1.2
- Backpedaling the type_id constraints in domain config which fails in some cases

1.1.1
- Adding nif blueprint using nif_tools to compare entities in KA to those in Lungo

1.0.12:
- Renaming 'mikrofly' to 'sportsfly'

1.0.7
- Backporting small fixes and correct redirect on _merged_to

1.0.6
- Adding 'secret_contact' whitelisting per client basis

1.0.5
- Correcting errors done with 1.0.3 vs 1.0.4 and hotfix vs feature branches

1.0.4
- Added support for merged persons' payments
- Do not process competences without expiry date

1.0.3
- rewrite to full url with https scheme
- seperate versioning file
"""
