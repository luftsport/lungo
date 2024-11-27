# - *- coding: utf- 8 - *-

class ProductChecker:

    def __init__(self, ka=None, print_msg=False):
        """
        :parameter object ka: supply an already instantiated instance of KA
        """

        if ka is None:
            from ka import KA
            self.ka = KA()
        else:
            self.ka = ka

        self._messages = []
        self.print_msg = print_msg

        self.log = []  # Everything
        self.corrections = []  # Only corrections made

        self.modellmedlem_age = range(26, 66)

    def get_log(self):

        return self.log

    def log(self, msg, what, action, because):

        self.log.append(msg)

    def get_corrections(self):

        return self.corrections

    def correction(self, msg):

        self.corrections.append(msg)

    def add_message(self, msg):
        if self.print_msg is True:
            print(msg)
        self._messages.append(msg)

    def get_person_activities(self, person_id, org_id):
        """Uses ka to get activities then assigns to activity_id/gren

        :parameter integer person_id: NIF Person Id
        :parameter integer org_id: NIF Organization Id
        :returns list grens: List of activity_ids already selected
        :returns list grens_not_selected: List of activity_ids not currently selected
        """

        grens = []
        grens_not_selected = []
        orgs = []
        sa, activities = self.ka.get_person_activities(person_id)

        s, av = self.ka.select_person_activities(person_id, org_id, activities)
        # print(s)
        # pprint(av)
        if s == 200:

            # @TODO kan om ingen selected kjøre ny loop og ta de som ikke er selected?
            for a in av['AvailableOrgs']:
                # print('####',a,'####')
                if a['OrgTypeId'] == 14 and a['Selected']:
                    if a['ShortName'] == 'Seilfly':
                        grens.append(111)
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 111})
                    elif a['ShortName'] == 'Motorfly':
                        grens.append(238)
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 238})
                    elif a['ShortName'] == 'Ballongflyging':
                        grens.append(235)
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 235})
                    elif a['ShortName'] == 'Mikrofly':
                        grens.append(237)
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 237})
                    elif a['ShortName'] == 'Modellfly':
                        grens.append(236)
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 236})
                    elif a['ShortName'] == 'Fallskjerm':
                        grens.append(109)
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 109})
                    else:
                        grens.append(110)  # HPG
                        orgs.append({'org_id': a['OrgId'], 'activity_id': 110})

                elif a['OrgTypeId'] == 14:
                    if a['ShortName'] == 'Seilfly':
                        grens_not_selected.append(111)
                    elif a['ShortName'] == 'Motorfly':
                        grens_not_selected.append(238)
                    elif a['ShortName'] == 'Ballongflyging':
                        grens_not_selected.append(235)
                    elif a['ShortName'] == 'Mikrofly':
                        grens_not_selected.append(237)
                    elif a['ShortName'] == 'Modellfly':
                        grens_not_selected.append(236)
                    elif a['ShortName'] == 'Fallskjerm':
                        grens_not_selected.append(109)
                    else:
                        grens_not_selected.append(110)  # HPG

            grens = list(set(grens))
            grens_not_selected = list(set(grens_not_selected))
        return grens, grens_not_selected  # , orgs

    def check_activities_org(self, person_id, org_id, fix=False):
        """Check activities for sanity
        """

        try:
            s, a = self.ka.get_person_activities(person_id)
            if s != 200:
                self.add_message(' [A] Kunne ikke hente aktiviteter')
                return False

            s, sa = self.ka.select_person_activities(person_id, org_id, a)
            if s != 200:
                self.add_message(' [A] Kunne ikke velge aktiviteter for gitt organisasjon')
                return False
            # 5 klubb, 6 gruppe, 14 gren
            org_needed = [5, 6, 14]
            org_nums = 0
            org_types = []
            org_types_selected = []
            org_types_not_selected = []

            for o in sa['AvailableOrgs']:
                org_nums += 1
                org_types.append(o['OrgTypeId'])
                if o['Selected']:
                    org_types_selected.append(o['OrgTypeId'])
                else:
                    org_types_not_selected.append(o['OrgTypeId'])

            org_types = list(set(org_types))
            org_types_selected = list(set(org_types_selected))
            org_types_not_selected = list(set(org_types_not_selected))

            if all(x in org_types_selected for x in org_needed):
                return True
            elif 14 in org_types_selected:
                self.add_message('?[A] Gren valgt')
                if org_nums == 3:
                    self.add_message('V[A] Mangler i klubb og gruppe - men kan fikses')
                return True
            elif org_nums == 3 and all(x in org_types for x in org_needed):
                self.add_message('V[A] Mangler i valg av gren - men kan fikses')

                if fix:
                    status, result = self.ka.save_person_activities(org_id, sa)

                    if status == 200:
                        self.add_message('V[A] Lagret endringer i aktiviteter')
                    else:
                        self.add_message('X[A] Feil under lagring av endringer i aktiviteter')

                return True
            else:
                self.add_message(' [A] Mangler i valg av gren - kan ikke fikses')
                return False
        except Exception as e:
            self.add_message(' [A] Error: {}'.format(e))

        return False

    def check(self, person_id, dry_run=False, abort=False):
        """Check products for person
        Needs to check activities to get correct grens.

        :parameter integer person_id: NIF Person Id
        :parameter boolean dry_run: Dry run if True, else make changes to products
        :returns boolean or products products: Returns false if failed, products if successfull
        """

        matrix_descr = {0: 'Medlem',
                        1: 'Æresmedlem',
                        2: 'Støttemedlem',
                        3: 'Ufør',
                        4: 'Tandemmedlem',
                        13: 'Kroppsfyker',
                        14: 'Modellmedlem',
                        17: 'Familiemedlem',
                        'real': 'Fullt medlem'
                        }

        matrix = {
            109: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'Fallskjerm'},
            111: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'Seilfly'},
            238: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'Motorfly'},
            237: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'Mikrofly'},
            110: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'HPG'},
            235: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'Ballong'},
            236: {0: False, 1: False, 2: False, 3: False, 4: False, 13: False, 14: False, 17: False, 'real': False,
                  'name': 'Modell'},
        }

        nomagz = [2, 4, 13, 17]

        """
        Unntak:
        Æresmedlem 1
        Støttemedlem 2
        Ufør 3
        Tandemmedlem 4
        Kroppsfyker 13
        Modellmedlem 14
        Familie 17
                                         
        "Blader"
        Flynytt 9
        Modellinformasjon 15
        Nordic Gliding 16
        HPS Grunnforsikring 20455
        HPS utvidelse død 20456
        HPS utvidelse invaliditet 20457
        HPS utvidelse begge 20458
        NLF reise individuell 20459
        HPS reise familie 20460
        HPS reise tillegg individuell - familie 20461
        Fallskjerm basisforsikring 20462
        Fallskjerm utvidet forsikring 20463
        NLF reise individuell - 2.halvår 20464
        NLF reise familie - 2.halvår 20465
        NLF reise tillegg individuell - familie - 2.halvår 20466
        HPS Grunnforsikring - 2.halvår 26001
        HPS utv død - 2.halvår 26002
        HPS utv invaliditet - 2.halvår 26003
        HPS utv begge - 2.halvår 26004
        
        
            20455: [111],
            20456: [111],
            20457: [111],
            20458: [111],
            20459: [111],
            20456: [111],
            20456: [111],
            26001: [111],
            26002: [111],
            26003: [111],
            26004: [111]
            
            
        """

        # Activity Id vs Product Id
        magz = {238: 9,  # Motor Flynytt
                237: 9,  # Mikro
                110: 10,  # HPG
                109: 11,  # Fallskjerm
                236: 15,  # Modell
                111: 16}  # Seil
        # Omvendt!
        zmag = {
            9: [238, 237],
            10: [110],
            11: [109],
            15: [236],
            16: [111]
        }

        # Unntak vs medlemsskap!
        unntak = {
            1: [235, 109, 110, 237, 236, 238, 111],  # Æresmedlem
            2: [235, 109, 110, 237, 236, 238, 111],  # Støttemedlem
            3: [235, 109, 110, 237, 236, 238, 111],  # Ufør
            4: [109],  # Tandemmedlem
            13: [109],  # Kroppsfyker
            14: [236],  # Modellmedlem
            17: [235, 109, 110, 237, 236, 238, 111]  # Familie
        }

        # Kroppsfykarlaug => not "real skydivers"
        not_real_clubs = [763224]
        kroppsfykarklubber = [763224]

        status, products = self.ka.get_person_products(person_id)

        if status == 200:

            self.add_message(' [C] Checking products for {} ({})'.format(products['PersonName'], person_id))

            cat_i = -1
            cat_blad_i = -1
            cat_unntak_i = -1

            for cat in products['Categories']:

                cat_i += 1

                if cat['CategoryName'] == 'Unntak':

                    cat_unntak_i += 1
                    cat_orgs_i = -1

                    for org in cat['Orgs']:

                        if not self.check_activities_org(person_id=person_id, org_id=org['ClubOrgId'], fix=not dry_run):

                            if abort:
                                self.add_message('X[A] Failed activity check for {} ({}) in {}, aborting'.format(
                                    products['PersonName'], person_id, org['ClubName']))
                                return False, None
                            else:
                                self.add_message('![A] Failed activity check for {} ({}) in {}, continuing with next'.format(
                                    products['PersonName'], person_id, org['ClubName']))
                                continue

                        cat_orgs_i += 1
                        cat_details_i = -1

                        # Activity id's for this org_id
                        activity_ids, non_activity_ids = self.get_person_activities(person_id, org['ClubOrgId'])
                        # activities = list(set(activities + activity_ids))

                        if len(activity_ids) > 0 or (len(activity_ids) == 0 and len(non_activity_ids) == 1):

                            # Hand over to not selected but single gren:
                            if len(activity_ids) == 0 and len(non_activity_ids) == 1:
                                self.add_message('?[A] Ingen valgte gren(er), men en ikke valgt gren - bruker den ikke valgte')
                                activity_ids = non_activity_ids

                            # Make member!
                            for i in activity_ids:
                                if i in matrix.keys():
                                    matrix[i][0] = True

                            # Counting first
                            selected = 0
                            for c in org['Details']:
                                if c['Selected']:
                                    selected += 1

                            # Unntak - loop all
                            for d in org['Details']:

                                cat_details_i += 1

                                # Unntak selected
                                if d['Selected'] is True:

                                    # Unntak allowed for org_id
                                    if len([i for i in activity_ids if i in unntak[d['ProductDetailId']]]) > 0:

                                        # For all activity_ids in seksjon check!
                                        for activity_id in activity_ids:
                                            matrix[activity_id][d['ProductDetailId']] = True

                                            self.add_message(' [U] ' + org['ClubName'] + ' ' + d['Name'] + ' ' + 'Unntak ER tillatt')

                                    else:
                                        self.add_message('-[U]' + ' ' + org['ClubName'] + ' ' + d['Name'] + ' ' + 'Unntak IKKE tillatt')
                                        # deselect unntak
                                        products['Categories'][cat_i]['Orgs'][cat_orgs_i]['Details'][cat_details_i][
                                            'Selected'] = False
                                        selected -= 1

                                # Unntak modellfly, kroppsfykar NOT selected - select!
                                else:
                                    if selected == 0 and 236 in activity_ids and d['ProductDetailId'] == 14 \
                                            and self.ka.get_age(person_id) in self.modellmedlem_age:
                                        self.add_message('+[U]' + ' ' + org['ClubName'] + ' ' + d['Name'] + ' ' + 'mangler: Modellmedlem!')
                                        matrix[236][14] = True
                                        products['Categories'][cat_i]['Orgs'][cat_orgs_i]['Details'][cat_details_i][
                                            'Selected'] = True
                                        selected += 1

                                    if selected == 0 and 109 in activity_ids and d['ProductDetailId'] == 13 and org[
                                        'ClubOrgId'] in kroppsfykarklubber:
                                        self.add_message('+[U]' + ' ' + org['ClubName'] + ' ' + d['Name'] + ' ' + 'mangler: Kroppsfykar!')
                                        matrix[109][13] = True
                                        products['Categories'][cat_i]['Orgs'][cat_orgs_i]['Details'][cat_details_i][
                                            'Selected'] = True
                                        selected += 1

                            # END loop Selected UNNTAK
                            # Real skydiver, not only tandem
                            if selected == 0:

                                for activity_id in activity_ids:
                                    self.add_message(' [U] Fullverdig medlem i {} ({})'.format(org['ClubName'],
                                                                                    matrix[activity_id]['name']))
                                    if org['ClubOrgId'] not in not_real_clubs:
                                        matrix[activity_id]['real'] = True

                            if selected > 1:
                                self.add_message('?[U] Flere valgt i' + ' ' + org['ClubName'])

            # Loop entire again now that we know all unntaks etc
            # Need to deselect tandem and kroppsfykar if real skydiver
            i = 0
            for category in products['Categories']:

                if category['CategoryName'] == 'Unntak':
                    j = 0
                    for org in category['Orgs']:
                        x = 0
                        for unntak in org['Details']:
                            if unntak['Selected'] is True and unntak['ProductDetailId'] in [13, 4] and matrix[109][
                                'real'] is True:
                                self.add_message('-[U] Delecting ' + ' ' + unntak['Name'] + ' ' + ' is real skydiver')
                                products['Categories'][i]['Orgs'][j]['Details'][x]['Selected'] = False
                                matrix[109][unntak['ProductDetailId']] = False
                            x += 1
                        j += 1
                i += 1

            # Fix magazines based on matrix
            if cat['CategoryName'] == 'Blad':

                cat_blad_i += 1
                cat_orgs_i = -1

                for o in cat['Orgs']:

                    cat_orgs_i += 1
                    cat_details_i = -1

                    if o['ClubOrgId'] == 376:

                        for m in o['Details']:

                            cat_details_i += 1

                            # Seksjonsmedlem?
                            # if matrix[zmag[m['ProductDetailId']]][0]:

                            # print('Sjekken', 'm', m['ProductDetailId'], 'sjekk', [x for x in range(0, len(zmag[m['ProductDetailId']]))
                            #        if matrix[zmag[m['ProductDetailId']][x]][0]])
                            self.add_message('[DEBUG] {}'.format(m))
                            if len([x for x in range(0, len(zmag.get(m['ProductDetailId'], []))) if
                                    matrix[zmag[m['ProductDetailId']][x]][0]]) > 0:

                                self.add_message(' [B] Medlem av seksjon, skal ha' + ' ' + m['Name'])

                                if m['Selected']:
                                    self.add_message(' [B]' + ' ' + m['Name'] + ' ' + 'already selected')
                                else:
                                    self.add_message('+[B] Selecting ' + ' ' + m['Name'])
                                    products['Categories'][cat_i]['Orgs'][cat_orgs_i]['Details'][cat_details_i][
                                        'Selected'] = True

                                # Unntak - skal ikke ha
                                for nomag in nomagz:
                                    # @TODO make oneliner!

                                    # Fallskjerm
                                    if magz[109] == m['ProductDetailId'] and matrix[109]['real'] and not \
                                            matrix[109][17]:
                                        self.add_message(' [B] Er fullverdig Fallskjerm medlem, skal ha Frittfall')
                                        break
                                    # Motor
                                    elif magz[238] == m['ProductDetailId'] and matrix[238]['real'] and not \
                                            matrix[238][17]:
                                        self.add_message(' [B] Er fullverdig Motorfly medlem, skal ha Flynytt')
                                        break
                                    # Mikro
                                    elif magz[237] == m['ProductDetailId'] and matrix[235]['real'] and not \
                                            matrix[235][17]:
                                        self.add_message(' [B] Er fullverdig Mikrofly medlem, skal ha Flynytt')
                                        break
                                    # Seil
                                    elif magz[111] == m['ProductDetailId'] and matrix[111]['real'] and not \
                                            matrix[111][17]:
                                        self.add_message(' [B] Er fullverdig Seilfly medlem, skal ha Nordic Gliding')
                                        break
                                    # Modell
                                    elif magz[236] == m['ProductDetailId'] and matrix[236]['real'] and not \
                                            matrix[236][17]:
                                        self.add_message(' [B] Er fullverdig Modell medlem, skal ha Modellinfo')
                                        break
                                    # HPG
                                    elif magz[110] == m['ProductDetailId'] and matrix[110]['real'] and not \
                                            matrix[110][17]:
                                        self.add_message(' [B] Er fullverdig HPG medlem, skal ha Fri Flukt')
                                        break
                                    elif len([x for x in range(0, len(zmag[m['ProductDetailId']]))
                                              if matrix[zmag[m['ProductDetailId']][x]][nomag]]) > 0:

                                        self.add_message(' [B] Unntak' + ' ' + matrix_descr[nomag] + ' ' + 'skal ikke ha ' + ' ' + m['Name'])

                                        if m['Selected']:
                                            self.add_message('-[B] Deselecting ' + ' ' + m['Name'])
                                            products['Categories'][cat_i]['Orgs'][cat_orgs_i]['Details'][
                                                cat_details_i][
                                                'Selected'] = False
                                        else:
                                            self.add_message(' [B]' + ' ' + m['Name'] + ' ' + 'not selected')

                            else:
                                if m['Selected']:
                                    self.add_message('-[B] IKKE medlem av seksjon, skal ikke ha' + ' ' + m['Name'])
                                    # deselect magazine
                                    products['Categories'][cat_i]['Orgs'][cat_orgs_i]['Details'][cat_details_i][
                                        'Selected'] = False

        else:
            self.add_message(' [E] Could not find any products, aborting for {}'.format(person_id))

        if dry_run is True:
            self.add_message(' [!] Dry run, no changes saved')
            return False, {'products': products, 'messages': self._messages}
        else:
            status, save = self.ka.save_person_products(products)
            if status in [200, 201]:
                return True, {'products': products, 'messages': self._messages}
            else:
                return False, {'products': products, 'messages': self._messages}

        # return zmag, matrix
