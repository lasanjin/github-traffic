#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # print() python2
import requests
import six
import json
from getpass import getpass
from threading import Thread
from datetime import datetime

import os
import sys
ABS_PATH = os.path.dirname(__file__)
sys.path.append(os.path.join(ABS_PATH, 'modules'))


if six.PY2:  # python2
    from urlparse import urljoin
    import Queue as q
elif six.PY3:  # python3
    import queue as q
    from urllib.parse import urljoin


def main():
    file = os.path.join(ABS_PATH, '.credentials')
    credentials = get_auth(file)

    print(color.info(), 'FETCHING DATA...\n')

    repos = get_repos(credentials)
    traffic = get_traffic(credentials, repos)
    print_data(traffic)


def get_repos(credentials):
    url = urljoin(
        api.BASE_URL,
        api.repos(credentials[0]))

    data = request(url, credentials)
    repos = []

    for key in data:
        if key['owner']['login'] == credentials[0]:  # source repos
            repos.append(key['name'])

    return repos


def get_traffic(credentials, repos):
    traffic = dict()
    # add each repository url in queue
    queue = build_queue(credentials, repos)
    # build threads for requests to each repository
    for i in range(queue.qsize()):
        thread = Thread(target=get_clones_thread,
                        args=(traffic, queue))
        thread.daemon = True
        thread.start()

    queue.join()

    return traffic


def build_queue(credentials, repos):
    queue = q.Queue()
    for repo in repos:
        url = urljoin(
            api.BASE_URL,
            api.clones(credentials[0], repo))

        queue.put((url, repo, credentials))

    return queue


def get_clones_thread(traffic, queue):
    # get clones for each repository
    while not queue.empty():
        q = queue.get()  # (url, repo, credentials)

        data = request(url=q[0], credentials=q[2])
        if len(data) > 0:

            traffic[q[1]] = {}
            for clone in data['clones']:
                # {repo: {timestamp: clones}}
                traffic[q[1]][clone['timestamp']] = clone['count']

        queue.task_done()


def request(url, credentials):
    try:
        res = requests.get(url, auth=(credentials[0], credentials[1]))
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
    def repos(username):
        return 'users/{}/repos'.format(username)

    @staticmethod
    def clones(username, repo):
        return 'repos/{}/{}/traffic/clones'.format(username, repo)


##################################################
# READ/WRITE USERNAME/TOKEN
##################################################
def get_auth(file):
    if not os.path.isfile(file):  # if no .credentials file
        try:
            if six.PY2:
                username = raw_input('USERNAME: ')
            elif six.PY3:
                username = input('USERNAME: ')

            token = getpass(
                'PERSONAL ACCESS TOKEN (https://github.com/settings/tokens): ')
        except ValueError as e:
            print("ValueError:", e.reason)

        credentials = [username, token]
        save_passw(credentials, file)  # save login credentials
    else:
        credentials = read_passw(file)

    return credentials


def save_passw(credentials, file):
    try:
        f = open(file, "w")  # write

        for c in credentials:
            f.write(c)
            f.write('\n')

        f.close()
    except OSError as eos:
        print('OSError:', eos)

    except IOError as eio:
        print("IOError:", eio)


def read_passw(file):
    credentials = []

    try:
        f = open(file, "r")  # read
        lines = f.readlines()
        f.close()

        for line in lines:
            credentials.append(line.strip())
    except IOError as eio:
        print("IOError:", eio)

    return credentials


##################################################
# PRINT
##################################################
def print_data(traffic):
    if not traffic:
        print(C.NO_DATA)
    else:
        today = datetime.today().date()

        for key, value in traffic.items():
            if len(value) > 0:
                print(color.blue(key))

                for k, v in sorted(value.items()):
                    date = datetime.strptime(k, C.format('YmdHMSZ'))
                    fdate = datetime.strftime(date, C.format('md'))

                    if date.date() == today:  # new clone
                        print('{}: {}'.format(fdate, color.green(v)))
                    else:
                        print('{}: {}'.format(fdate, v))

                print()


class C:
    @staticmethod
    def format(arg):
        return {
            'YmdHMSZ': '%Y-%m-%dT%H:%M:%SZ',
            'md': '%m-%d'
        }[arg]


class color:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'

    @staticmethod
    def green(output):
        return color.GREEN + str(output) + color.DEFAULT

    @staticmethod
    def blue(output):
        return color.BLUE + str(output) + color.DEFAULT

    @staticmethod
    def info():
        return color.green("[INFO]")


if __name__ == '__main__':
    main()
