#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # print() python2
from datetime import datetime
from threading import Thread
from getpass import getpass
import requests
import json
import six
import os

if six.PY2:  # python2
    from urlparse import urljoin
    import Queue as q
elif six.PY3:  # python3
    import queue as q
    from urllib.parse import urljoin


def main():
    path = os.path.dirname(__file__)  # abs path of script
    file = os.path.join(path, C.FILE)
    auth = get_auth(file)

    print(C.FETCHING)

    repos = get_repos(auth)
    traffic = get_traffic(auth, repos)

    print_data(traffic)


def get_auth(file):
    if not os.path.isfile(file):  # if no .passw file
        try:
            if six.PY2:
                user = raw_input(C.USER)
            elif six.PY3:
                user = input(C.USER)

            passw = getpass(C.PASSW)

        except ValueError as e:
            print("ValueError", e.reason)

        auth = [user, passw]
        save_passw(auth, file)  # save login credentials

    else:
        auth = read_passw(file)

    return auth


def save_passw(auth, file):
    try:
        f = open(file, "w")  # write

        for i in auth:
            f.write(i)
            f.write('\n')

        f.close()

    except OSError as eos:
        print('OSError:', eos)

    except IOError as eio:
        print("IOError:", eio)


def read_passw(file):
    auth = []

    try:
        f = open(file, "r")  # read
        out = f.readlines()
        f.close()

        for i in out:
            auth.append(i.strip())

    except IOError as eio:
        print("IOError:", eio)

    return auth


def get_repos(auth):
    url = urljoin(
        api.BASE_URL,
        api.REPOS_URL(auth[0]))

    data = request(url, auth)
    repos = []

    for key in data:
        if key['owner']['login'] == auth[0]:  # source repos
            repos.append(key['name'])

    return repos


def get_traffic(auth, repos):
    traffic = {}
    # add each repository url in queue
    queue = build_queue(auth, repos)
    # build threads for requests to each repository
    for i in range(queue.qsize()):
        thread = Thread(target=get_clones_thread,
                        args=(traffic, queue))
        thread.daemon = True
        thread.start()

    queue.join()

    return traffic


def build_queue(auth, repos):
    queue = q.Queue()
    for repo in repos:
        url = urljoin(
            api.BASE_URL,
            api.CLONES_URL(auth[0], repo))

        queue.put((url, repo, auth))

    return queue


def get_clones_thread(traffic, queue):
    # get clones for each repository
    while not queue.empty():
        q = queue.get()  # (url, repo, auth)

        data = request(url=q[0], auth=q[2])
        if len(data) > 0:

            traffic[q[1]] = {}
            for clone in data['clones']:
                # {repo: {timestamp: clones}}
                traffic[q[1]][clone['timestamp']] = clone['count']

        queue.task_done()


def request(url, auth):
    try:
        res = requests.get(url, auth=(auth[0], auth[1]))

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

    @staticmethod
    def REPOS_URL(user):
        return 'users/' + user + '/repos'

    @staticmethod
    def CLONES_URL(user, repo):
        return 'repos/' + user + '/' + repo + '/traffic/clones'


class C:
    FILE = '.passw'
    USER = 'Username: '
    PASSW = 'Password: '
    FETCHING = "\nFETCHING DATA...\n"
    NO_DATA = "NO DATA"
    BLUE = '\033[94m'
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'


def print_data(traffic):
    if not traffic:
        print(C.NO_DATA)
    else:
        for key, value in traffic.items():

            if len(value) > 0:
                print(C.BLUE + key + C.DEFAULT)

                for k, v in sorted(value.items()):
                    date = datetime.strptime(k, "%Y-%m-%dT%H:%M:%SZ")
                    fdate = datetime.strftime(date, "%m-%d")

                    if date.date() == datetime.today().date():  # new clone
                        print(
                            fdate + ': ',
                            C.GREEN + str(v) + C.DEFAULT)
                    else:
                        print(fdate + ': ', v)

                print()


if __name__ == '__main__':
    main()
