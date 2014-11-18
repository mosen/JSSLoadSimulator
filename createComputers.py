#!/usr/bin/python
__author__ = 'matthewfjerstad'

import random
import re
import uuid
import getpass
import base64
import xml.dom.minidom
import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl

jss_host = ""
jss_port = ""
jss_path = ""
jss_username = ""
jss_password = ""
number_to_create = 0


def main():
    verify_jss_details()
    base_computer = get_initial_computer()
    x = 0
    while x < number_to_create:
        x += 1
        c = Computer(base_computer, x)
        print "Successfully created computer with ID: " + str(c.computer_id)


class Computer():
    def __init__(self, detail_string, index):
        self.serial_number = random.randint(9999999999, 99999999999)
        clean_string = re.sub(r'<serial_number></serial_number>',
                          '<serial_number>' + str(self.serial_number) + '</serial_number>',
                          detail_string, )
        self.udid = uuid.uuid1()
        clean_string = re.sub(r'<udid></udid>', '<udid>' + str(self.udid) + '</udid>',
                          clean_string, )
        self.mac_address = random_mac()
        clean_string = re.sub(r'<mac_address></mac_address>',
                          '<mac_address>' + str(self.mac_address) + '</mac_address>', clean_string, )
        self.alt_mac_address = random_mac()
        clean_string = re.sub(r'<alt_mac_address></alt_mac_address>',
                        '<alt_mac_address>' + str(self.alt_mac_address) + '</alt_mac_address>', clean_string, )
        name_file = open(str(os.getcwd()) + '/resources/names')
        name_list = name_file.readlines()
        name_file.close()
        username = name_list[random.randint(0, len(name_list) - 1)].strip()
        computer_name = username \
                        + "'s MacBook Air"
        clean_string = re.sub(r'COMPUTERNAME', '<name>' + str(computer_name) + '</name>', clean_string, )
        location = '<username>' + username + str(random.randint(999, 9999)) + '</username><realname/><email_address>' + \
                   username.lower() + '@jamf.com</email_address>'
        clean_string = re.sub(r'LOCATIONINFO', location, clean_string, )
        self.detail_string = clean_string
        self.index = index
        device_response = connect_jss("/JSSResource/computers", "POST", self.detail_string)
        device_response = re.sub('"','\"',device_response,)
        try:
            device = xml.dom.minidom.parseString(str(device_response))
            self.computer_id = device.getElementsByTagName('id')[0].childNodes[0].data
        except:
            print "Computer Creation failed"


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
    number_to_create = int(prompt_user('Enter number of computers to create: '))


def prompt_user(variable):
    return raw_input('Enter ' + variable + ': ')


def get_initial_computer():
    computer_file = open(str(os.getcwd()) + "/resources/computerXML")
    computer_string = computer_file.read()
    computer_file.close()
    return computer_string


def random_mac():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def get_auth_header(u, p):
    token = base64.b64encode('%s:%s' % (u, p))
    return "Basic %s" % token


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