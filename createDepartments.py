#!/usr/bin/python

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
import getpass
import random
import os


jss_host = ""
jss_port = ""
jss_path = ""
jss_username = ""
jss_password = ""
number_to_create = 0


def main():
    x = 0
    verify_jss_details()
    while x < number_to_create:
        x += 1
        create_department()
    print 'Finished creating ' + str(x) + ' departments.\n'



def verify_jss_details():

    global jss_host
    global jss_port
    global jss_path
    if jss_host == '':
            jss_host = prompt_user('JSS Hostname')
    if jss_port == '':
            jss_port = prompt_user('JSS Port')
    if jss_path == '':
            jss_path = prompt_user('JSS path (ex https://jss.com:8443/apple enter apple\n JSS path')
    global jss_username
    jss_username = prompt_user('JSS Username')
    global jss_password
    jss_password = getpass.getpass('Enter JSS Password: ')
    global number_to_create
    number_to_create = int(prompt_user('Enter number of departments to create: '))


def create_department():
    name_file = open(str(os.getcwd()) + '/resources/departments')
    name_list = name_file.readlines()
    name_file.close()
    department_name = name_list[random.randint(0, len(name_list) - 1)].strip()
    department_string = '<department><name>' + department_name + str(random.randint(999, 9999)) + '</name></department>'
    connect_jss('/JSSResource/departments', 'POST', department_string)


def prompt_user(variable):
    return raw_input('Enter ' + variable + ': ')



class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block,ssl_version=ssl.PROTOCOL_TLSv1)


def connect_jss(path, method, body):
    try:
        session = requests.Session()
        session.mount("https://" + str(jss_host) + ":" + str(jss_port), MyAdapter())
        session.auth = (jss_username, jss_password)
        session.headers.update({'Content-Type':'application/xml'})

        if method == 'GET':
            response = session.get("https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + str(path))
        elif method == 'POST':
            response = session.post("https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + str(path), data=body)
        elif method == 'PUT':
            response = session.put("https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + str(path), data=body)

        return response.text
    except requests.exceptions.RequestException as e:
        print "Connection exception: " + str(e)


main()
