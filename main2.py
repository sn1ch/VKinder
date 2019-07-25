from pprint import pprint
from urllib.parse import urlencode
import time
import json
import vk
import operator
from collections import Counter
from pymongo import MongoClient
from bson import json_util


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
        self.age_from, self.age_to = map(str, input(
            'Введите через пробел возраст ОТ которого и ДО которого искать: ').split())
        self.token = token
        session = vk.Session(access_token=self.token)
        self.api = vk.API(session)

    def get_info(self):
        user = self.api.users.get(v='5.101', fields='interests, sex, city, books, music')
        groups = self.api.groups.get(v='5.101')
        try:
            self.city = user[0]['city']['id']
        except KeyError:
            city_input = input('В каком городе будем искать: ')
            city = self.api.database.getCities(v='5.101', country_id=1, q=city_input)
            self.city = city['items'][0]['id']
        if user[0]['sex'] == 1:
            self.sex = 2
        else:
            self.sex = 1
        interests = (user[0]['music'] + ' ' + user[0]['interests'] + ' ' + user[0]['books']).replace(',', '').split(' ')
        self.filter_interests = [item for item in interests if item != '']
        self.groups = groups['items']

    def search(self):
        res = self.api.users.search(v='5.101', city=self.city, sex=self.sex, age_from=self.age_from, age_to=self.age_to,
                                    count=1000)
        print('...')
        offset = 0
        users_list = []
        while offset < res['count']:
            try:
                users = self.api.users.search(v='5.101', city=self.city, sex=self.sex, age_from=self.age_from,
                                              age_to=self.age_to,
                                              count=10, offset=offset)
                print('...')
            except vk.exceptions.VkAPIError:
                time.sleep(1)
                continue
            for user in users['items']:
                users_list.append(user['id'])
            offset += 1000
        self.users_list = users_list

    def count_groups_match_points(self):
        group_matches = {}
        for id in self.users_list:
            try:
                groups = self.api.groups.get(v='5.101', user_id=str(id))
                print('...')
                group_matches[id] = len(set(self.groups).intersection(set(groups['items'])))
            except vk.exceptions.VkAPIError:
                print('...ops')
                time.sleep(1)
                continue
        group_matches = sorted(group_matches.items(), key=operator.itemgetter(1), reverse=True)
        self.group_matches = dict(group_matches)

    def count_interests_match_points(self):
        interests_matches = {}
        for id in self.users_list:
            try:
                user = self.api.users.get(v='5.101', user_id=str(id), fields='interests, books, music')
                print('...тут')
                time.sleep(0.34)
                try:
                    interests = \
                        (user[0]['music'] + ' ' + user[0]['interests'] + ' ' + user[0]['books']) \
                            .replace(',', '').split(' ')
                    interests_filter = [item for item in interests if item != '']
                except KeyError:
                    continue
                except vk.exceptions.VkAPIError:
                    time.sleep(1)
                interests_matches[id] = len(set(self.filter_interests).intersection(set(interests_filter)))
            except vk.exceptions.VkAPIError:
                print('...ops')
                time.sleep(1)
                continue
        interests_matches = sorted(interests_matches.items(), key=operator.itemgetter(1), reverse=True)
        self.interests_matches = dict(interests_matches)

    def count_total_match_points(self):
        groups_and_interests_match = (self.interests_matches, self.group_matches)
        total_match_points = Counter()
        for item in groups_and_interests_match:
            total_match_points.update(item)
        total_match_points = dict(total_match_points)
        total_match_points = sorted(total_match_points.items(), key=operator.itemgetter(1), reverse=True)
        self.total_match_points = total_match_points

    def get_top10users(self):
        self.top_10_users = []
        for user in self.total_match_points:
            try:
                for id in skip_ids.find_one()['ID']:
                    if user[0] != id and len(self.top_10_users) != 10 and user[0] not in self.top_10_users:
                        self.top_10_users.append(user[0])
                        skip_ids.update_one({'ID': skip_ids.find_one()['ID']}, {'$push': {'ID': user[0]}})
            except TypeError:
                skip_ids.insert_one({'ID': [0]})
                continue

    def get_photos(self):
        self.to_write = []
        for id in self.top_10_users:
            top_likes_list = []
            photo = self.api.photos.get(v='5.101', owner_id=id, album_id='profile', extended='likes')
            time.sleep(0.34)
            user = self.api.users.get(v='5.101', user_ids=id)
            print('...photo')
            time.sleep(0.34)
            top_3_photo = []
            for i in photo['items']:
                top_likes_list.append(i['likes']['count'])
                top_likes_list.sort(reverse=True)
            for i in photo['items']:
                if i['likes']['count'] in top_likes_list[:3]:
                    top_3_photo.append(i['sizes'][-1]['url'])
            self.to_write.append({'id': id, 'first_name': user[0]['first_name'], 'last_name': user[0]['last_name'],
                                  'url': top_3_photo})

    def write_top10users(self):
        with open('data/top10users.json', 'w', encoding='utf-8') as file:
            json.dump(self.to_write, file, ensure_ascii=False, indent=2)
        with open('data/top10users.json', 'r', encoding='utf-8') as file:
            data = json_util.loads(file.read())
            top10users.insert_one({'users': data})
            print(data)


if __name__ == '__main__':
    client = MongoClient()
    VK_db = client['VK_db']
    skip_ids = VK_db['skip_ids103']
    top10users = VK_db['top10users103']

    user = VK()
    user.get_token()
    user.get_info()
    user.search()
    user.count_groups_match_points()
    user.count_interests_match_points()
    user.count_total_match_points()
    user.get_top10users()
    user.get_photos()
    user.write_top10users()
