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

if six.PY2:
    from urlparse import urljoin
    import Queue as q
elif six.PY3:
    import queue as q
    from urllib.parse import urljoin

fname = '.passw'


def main():
    if not os.path.isfile(fname):  # if not .passw
        try:
            if six.PY2:
                user = raw_input('username: ')
            elif six.PY3:
                user = input('username: ')

            passw = getpass('password: ')

        except ValueError:
            print("ValueError")

        auth = [user, passw]
        save_passw(auth)  # save in dir of script for next time

    else:
        auth = read_passw()

    print("\nfetching data...\n")
    repos = get_repos(auth)
    traffic = get_traffic(auth, repos)

    print_data(traffic)


def save_passw(auth):
    d = os.path.dirname(__file__)  # dir of script

    try:
        os.path.join(d, fname)

        f = open(fname, "w")
        for i in auth:
            f.write(i)
            f.write('\n')

        f.close()

    except OSError as eos:
        print('OSError:', eos)

    except IOError as eio:
        print("IOError:", eio)


def read_passw():
    auth = []

    try:
        f = open(fname, "r")
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


class constant:
    BLUE = '\033[94m'
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'


def print_data(traffic):
    for key, value in traffic.items():

        if len(value) > 0:
            print(constant.BLUE + key + constant.DEFAULT)

            for k, v in value.items():
                date = datetime.strptime(k, "%Y-%m-%dT%H:%M:%SZ")
                fdate = datetime.strftime(date, "%m-%d")

                if date.date() == datetime.today().date():  # new clone
                    print(
                        fdate + ': ',
                        constant.GREEN + str(v) + constant.DEFAULT)
                else:
                    print(fdate + ': ', v)

            print()


if __name__ == '__main__':
    main()
