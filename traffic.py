#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # print() python2
from getpass import getpass
from threading import Thread
from datetime import datetime
import base64
import json
import sys
import os

PY_VERSION = sys.version_info[0]

if PY_VERSION < 3:
    from Queue import Queue
    from urlparse import urljoin
    import urllib2
elif PY_VERSION >= 3:
    from queue import Queue
    from urllib.parse import urljoin
    import urllib.request as urllib2


def main():
    credentials = get_credentials()
    print(Style.style("[INFO]", 'green'), 'FETCHING DATA...\n')
    repos = get_repos(credentials)
    traffic = get_traffic(credentials, repos)
    if not traffic:
        print("NO DATA")
    else:
        print_data(traffic)


def get_repos(credentials):
    repos = []
    url = urljoin(Api.BASE_URL, Api.repos(credentials[0]))
    data = request(url, credentials)
    for repo in data:
        if repo['owner']['login'] == credentials[0]:  # source repos
            repos.append(repo['name'])

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
    queue = Queue()
    for repo in repos:
        url = urljoin(Api.BASE_URL, Api.clones(credentials[0], repo))
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
    request = build_request(url, credentials)
    try:
        resp = urllib2.urlopen(request).read()
        if resp is None:
            print("NO DATA")
            quit()
        else:
            return json.loads(resp)
            # print(json.dumps(json.loads(resp), indent=2, ensure_ascii=False))  # debug
    except Exception as e:
        print('Exception:', e)
        quit()


def build_request(url, credentials):
    request = urllib2.Request(url)
    c = credentials[0] + ':' + credentials[1]
    b64auth = base64.b64encode(c.encode()).decode()
    request.add_header("Authorization", "Basic %s" % b64auth)

    return request


def get_credentials():
    abs_path = os.path.dirname(__file__)
    file = os.path.join(abs_path, '.credentials')
    # if no .credentials file
    if not os.path.isfile(file):
        try:
            if PY_VERSION < 3:
                username = raw_input('USERNAME: ')
            elif PY_VERSION >= 3:
                username = input('USERNAME: ')

            token = getpass("PERSONAL ACCESS TOKEN %s%s " %
                            (Style.style(Utils.LINK, None, ['dim']), ":"))
        except ValueError as e:
            print("ValueError:", e.reason)

        credentials = [username, token]
        # save login credentials
        save_credentials(credentials, file)
    else:
        credentials = read_credentials(file)

    return credentials


def save_credentials(credentials, file):
    try:
        f = open(file, "w")
        for c in credentials:
            f.write(c)
            f.write('\n')
        f.close()
    except OSError as eos:
        print('OSError:', eos)
    except IOError as eio:
        print("IOError:", eio)


def read_credentials(file):
    credentials = []
    try:
        f = open(file, "r")
        lines = f.readlines()
        f.close()
        for line in lines:
            credentials.append(line.strip())
    except IOError as eio:
        print("IOError:", eio)

    return credentials


class Api:
    BASE_URL = 'https://api.github.com'

    @staticmethod
    def repos(username):
        return 'users/{}/repos'.format(username)

    @staticmethod
    def clones(username, repo):
        return 'repos/{}/{}/traffic/clones'.format(username, repo)


class Utils:
    LINK = "(https://github.com/settings/tokens)"

    @staticmethod
    def format(arg):
        return {
            'YmdHMSZ': '%Y-%m-%dT%H:%M:%SZ',
            'md': '%m-%d'
        }[arg]


class Style:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    DIM = '\033[2m'

    @staticmethod
    def style(output, color, styles=[]):
        if color is not None:
            output = {
                'green': Style.GREEN + '%s',
                'blue': Style.BLUE + '%s',
            }[color] % output

        for style in styles:
            output = {
                'dim': Style.DIM + '%s'
            }[style] % output

        return output + Style.DEFAULT


# -----------------------------------------------------------------
# PRINT
# -----------------------------------------------------------------
def print_data(traffic):
    num_of_clones = 0
    today = datetime.today().date()
    # print repos
    for key, value in traffic.items():
        if len(value) > 0:
            print(Style.style(key, 'blue'))
            # print date
            for k, v in sorted(value.items()):
                date = datetime.strptime(k, Utils.format('YmdHMSZ'))
                fdate = datetime.strftime(date, Utils.format('md'))
                num_of_clones += 1
                # print new clones
                if date.date() == today:  # new clone
                    print('%s: %s' % (fdate, Style.style(v, 'green')))
                # print older clones
                else:
                    print('%s: %s' % (fdate, v))
            print()
    print('TOTAL CLONES: %s\n' % num_of_clones)


if __name__ == '__main__':
    main()
