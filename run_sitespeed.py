#!/usr/bin/env python3

import json
import re
import requests
import subprocess

CONTAINER_IP = TRIALS_PER_URL = None
DEFAULT_USER = DEFAULT_PASSWORD = None
AUTH_ENDPOINT = None


def read_config():
    with open('./config.json', 'r') as f:
        return json.loads(f.read())


def get_auth_token(auth_url, user='test_ocan1', password='password',
                   headers=None):
    """
    Retrieves an auth token from an auth endpoint given credentials.
    There is no standardized way to do auth across the internet.
    So you will need to use a different version of this function for
    each site you want to target.
    """
    if auth_url is None:
        return ""

    data = json.dumps({'username': user, 'password': password})

    if headers is None:
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
    else:
        headers = {**headers,
                   **{'Content-Type': 'application/json'},
                   **{'Accept': 'application/json'}}

    response = requests.post(auth_url, data=data, headers=headers)
    return re.search('session=(.+?);', response.headers['Set-Cookie']).group(1)


def run_sitespeed(url, auth_url, headers=None, user='test_ocan1',
                  password='password', key='', browser='chrome'):
    """
    Accepts commandline configuration options for sitespeed and translates
    them to a bash one-liner to test a single page.

    :param urls: string urls for pages to test.
     separate different urls with whitespace,
    :param body: dict containing request body data
    :param headers: dict containing header data
    :param cookies: dict of cookies to send with request
    """
    if headers is None:
        headers = {}

    # Get auth token
    token = get_auth_token(auth_url, user, password, headers)
    cookies = {
      'session': token
    }

    urlstr = ' {}'.format(url)

    headerstr = ''
    for h in headers:
        headerstr += ' --requestHeader {}:{}'.format(key, headers[h])

    cookiestr = ''
    for c in cookies:
        cookiestr += ' --cookie {}={}'.format(c, cookies[c])

    browserstr = ' -b {}'.format(browser)

    # n argument specifies number of times to test each url
    cmd = "/usr/bin/docker-compose run sitespeed.io {} {} {} {} -n {}"\
          .format(headerstr, cookiestr, urlstr, browserstr, TRIALS_PER_URL)
    cmd += " --graphite.host={} --graphite.port=2003".format(CONTAINER_IP)
    if key:
        cmd += " --graphite.namespace {}".format(key)

    # CPU metrics work only for chrome
    if browser == 'chrome':
        cmd += " --chrome.timeline"

    print(cmd)
    subprocess.run(re.split(r'\s+', cmd))


# Get config options
config = read_config()
CONTAINER_IP = config['CONTAINER_IP']
TRIALS_PER_URL = config['TRIALS_PER_URL']

# Run a test per config user in the config url
for browser in config['browsers']:
    for page in config['pages']:
        for user in page['users']:
            run_sitespeed(page['url'],
                          auth_url=page.get('auth_url'),
                          headers={'User-Agent': browser['user-agent']},
                          user=user['user'],
                          password=user['password'],
                          key=page['series_key'],
                          browser=browser['name'])


# Clean up exitted containers
get_stopped_containers = 'docker ps -aq -f name=sitespeed -f status=exited'
container_ids = subprocess.run(get_stopped_containers.split(' '),
                               stdout=subprocess.PIPE)
container_ids = container_ids.stdout.decode().replace('\n', ' ')
clean = 'docker rm -v {}'.format(container_ids)
print('RUNNING CLEANUP: {}'.format(clean))
subprocess.run(clean.split(' '))
