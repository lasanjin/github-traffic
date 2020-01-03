#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # print() python2
from datetime import datetime
import json
import requests
from getpass import getpass
import six

if six.PY2:
    from urlparse import urljoin
elif six.PY3:
    from urllib.parse import urljoin


def main():
    try:
        if six.PY2:
            user = raw_input('username: ')
        elif six.PY3:
            user = input('username: ')

        passw = getpass('password: ')

    except ValueError:
        print("ValueError")

    auth = (user, passw)

    print("\nfetching data...\n")
    repos = get_repos(auth)
    traffic = get_traffic(auth, repos)

    print_data(traffic)


def get_repos(auth):
    url = urljoin(
        api.BASE_URL,
        api.REPOS_URL)
    data = request(url, auth)

    repos = []
    for key in data:
        if key['owner']['login'] == auth[0]:  # source repos
            repos.append(key['name'])

    return repos


def get_traffic(auth, repos):
    traffic = {}
    for repo in repos:
        url = urljoin(
            api.BASE_URL,
            api.CLONE_URL(auth[0], repo))
        data = request(url, auth)

        traffic[repo] = {}
        for clone in data['clones']:
            traffic[repo][clone['timestamp']] = clone['count']

    return traffic


def print_data(traffic):
    for key, value in traffic.items():

        if len(value) > 0:
            print(constant.BLUE + key + constant.DEFAULT)

            for k, v in value.items():
                date = datetime.strptime(k, "%Y-%m-%dT%H:%M:%SZ")
                formatted = datetime.strftime(date, "%m-%d")

                print(formatted + ': ', v)

            print()


def request(url, auth):
    try:
        res = requests.get(
            url,
            auth=auth)

        res.raise_for_status()

        return json.loads(res.text)

    except requests.exceptions.HTTPError as eh:
        print("HTTPError:", eh)

    except requests.exceptions.ConnectionError as ec:
        print("ConnectionError:", ec)

    except requests.exceptions.Timeout as et:
        print("Timeout:", et)

    except requests.exceptions.RequestException as er:
        print("RequestException:", er)


class api:
    BASE_URL = 'https://api.github.com'
    REPOS_URL = 'user/repos'

    @staticmethod
    def CLONE_URL(user, repo):
        return 'repos/' + user + '/' + repo + '/traffic/clones'


class constant:
    BLUE = '\033[94m'
    DEFAULT = '\033[0m'


if __name__ == '__main__':
    main()
