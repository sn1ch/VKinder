from pprint import pprint
from urllib.parse import urlencode
import time
import vk
import operator
from collections import Counter


class VK:
    def get_token(self):
        VK_API = 7054934
        BASE_URL = 'https://oauth.vk.com/authorize'
        authorization = {
            'client_id': VK_API,
            'display': 'popup',
            'scope': 'friends, groups',
            'response_type': 'token',
            'v': '5.101'
        }
        pprint('?'.join((BASE_URL, urlencode(authorization))))
        token = input('Вставьте сюда access_token: ')
        self.token = token

    def get_info(self):
        session = vk.Session(access_token=self.token)
        api = vk.API(session)
        self.age_from, self.age_to = map(str, input(
            'Введите через пробел возрат ОТ которого и ДО которого искать: ').split())
        user = api.users.get(v='5.101', fields='interests, sex, city, books, music')
        groups = api.groups.get(v='5.101')
        self.city = user[0]['city']['id']
        if user[0]['sex'] == 1:
            self.sex = 2
        else:
            self.sex = 1
        interests = \
            (user[0]['music'] + ' ' + user[0]['interests'] + ' ' + user[0]['books']).replace(',', '').split(' ')
        self.filter_interests = [item for item in interests if item != '']
        print(self.filter_interests)
        self.groups = groups['items']

    def get_interests(self):
        session = vk.Session(access_token=self.token)
        api = vk.API(session)
        user = api.users.get(v='5.101', fields='interests, books, music')
        interests = \
            (user[0]['music'] + ' ' + user[0]['interests'] + ' ' + user[0]['books']).replace(',', '').split(' ')
        self.interests = [item for item in interests if item != '']

    def search(self):
        session = vk.Session(access_token=self.token)
        api = vk.API(session)
        res = api.users.search(v='5.101', city=self.city, sex=self.sex, age_from=self.age_from, age_to=self.age_to,
                               count=1000)
        print('...')
        time.sleep(0.34)
        offset = 0
        users_list = []
        while offset < res['count']:
            api.users.search(v='5.101', city=self.city, sex=self.sex, age_from=self.age_from, age_to=self.age_to,
                             count=20, offset=offset)
            print('...')
            time.sleep(0.34)
            for user in res['items']:
                users_list.append(user['id'])
            offset += 1000
        self.users_list = users_list

    def count_groups_match_points(self):
        session = vk.Session(access_token=TOKEN)
        api = vk.API(session)
        group_matches = {}
        for id in self.users_list:
            try:
                groups = api.groups.get(v='5.101', user_id=str(id))
                print('...')
                time.sleep(0.34)
                group_matches[id] = len(set(self.groups).intersection(set(groups['items'])))
            except vk.exceptions.VkAPIError:
                print('...ops')
                time.sleep(0.34)
                continue
        group_matches = sorted(group_matches.items(), key=operator.itemgetter(1), reverse=True)
        self.group_matches = dict(group_matches)

    def count_interests_match_points(self):
        session = vk.Session(access_token=TOKEN)
        api = vk.API(session)
        interests_matches = {}
        for id in self.users_list:
            try:
                user = api.users.get(v='5.101', user_id=str(id), fields='interests, books, music')
                print('...')
                time.sleep(0.34)
                try:
                    interests = \
                        (user[0]['music'] + ' ' + user[0]['interests'] + ' ' + user[0]['books'])\
                            .replace(',', '').split(' ')
                    interests_filter = [item for item in interests if item != '']
                except KeyError:
                    continue
                interests_matches[id] = len(set(self.filter_interests).intersection(set(interests_filter)))
            except vk.exceptions.VkAPIError:
                print('...ops')
                time.sleep(0.34)
                continue
        interests_matches = sorted(interests_matches.items(), key=operator.itemgetter(1), reverse=True)
        self.interests_matches = dict(interests_matches)
        print(interests_matches)
        print(self.interests_matches)

    def count_total_match_points(self):
        groups_and_interests_match = (self.interests_matches, self.group_matches)
        total_match_points = Counter()
        for item in groups_and_interests_match:
            total_match_points.update(item)
        self.total_match_points = total_match_points


if __name__ == '__main__':
    user = VK()
    user.get_token()
    user.get_info()
    user.search()
    user.count_groups_match_points()
    user.count_interests_match_points()
    user.count_total_match_points()
