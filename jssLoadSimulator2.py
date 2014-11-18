#!/usr/bin/python
#
# This script will gather all computers in the JSS and simulate check ins based on intervals

import getopt
import sys
import os
import plistlib
import getpass
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
import xml.dom.minidom
import threading
import re
import time


computers = []
number_of_times_to_update = ''
number_per_batch = ''
time_between_updates = ''
time_between_batches = ''
checkin_or_update = ''
jss_host = ""
jss_port = ""
jss_path = ""
jss_username = ""
jss_password = ""
checkin_string = ""


def main(argv):
    verify_variables(argv)
    verify_jss_details()
    get_checkin_string()
    get_all_computers()
    n = 0
    while n < int(number_of_times_to_update):
        n += 1
        i = 0
        while i < len(computers):
            if (i + int(number_per_batch)) < len(computers):
                x = 0
                print 'Checking in ' + str(number_per_batch) + ' computers...'
                while x < int(number_per_batch):
                    c = SubmitThread(computers[i])
                    c.start()
                    i += 1
                    x += 1
                time.sleep(int(time_between_batches))
            else:
                print 'Checking in ' + str((len(computers)) - i) + ' computers...'
                while i < len(computers):
                    c = SubmitThread(computers[i])
                    c.start()
                    i += 1
                time.sleep(int(time_between_batches))
        if n < int(number_of_times_to_update):
            print 'Sleeping ' + str(time_between_updates) + ' before next check in'
            time.sleep(int(time_between_updates))






def get_all_computers():
    global computers
    print 'Gathering computers from JSS...'
    computer_list = xml.dom.minidom.parseString(connect_jss('/JSSResource/computers', 'GET', ''))
    total_computers = int(computer_list.getElementsByTagName('size')[0].childNodes[0].data)
    i = 0
    computer_nodes = computer_list.getElementsByTagName('computer')
    for node in computer_nodes:
        i += 1
        show_progress(i, total_computers)
        try:
            computer = xml.dom.minidom.parseString(node.toxml())
            comp = Computer(computer.getElementsByTagName('id')[0].childNodes[0].data)
            computers.append(comp)
        except:
            print 'failed'


class Computer():
    def __init__(self, computer_id):
        global checkin_string
        self.raw_xml = connect_jss('/JSSResource/computers/id/' + str(computer_id), 'GET', '')
        computer_parse = xml.dom.minidom.parseString(self.raw_xml)
        self.udid = computer_parse.getElementsByTagName('udid')[0].childNodes[0].data
        self.mac_address = computer_parse.getElementsByTagName('mac_address')[0].childNodes[0].data
        clean_checkin = re.sub(r'UDID', '<uuid>' + str(self.udid) + '</uuid>', checkin_string, )
        clean_checkin = re.sub(r'MACADDRESS', '<macAddress bsdName="en0">' + str(self.mac_address) + '</macAddress>', clean_checkin, )
        self.check_in_string = clean_checkin

    def submit(self):
        checkin_response = connect_jss_client("/client", "POST", self.check_in_string)
        try:
            response_parse = xml.dom.minidom.parseString(checkin_response)
            response_id = response_parse.getElementsByTagName('code')[0].childNodes[0].data
            if str(response_id) == "1501":
                print "Check in failed for computer: " + self.udid + \
                     "\tMake sure Cert Based Communication is disabled"
        except:
            print "failed"


class SubmitThread(threading.Thread):
    def __init__(self, computer_record):
        threading.Thread.__init__(self)
        self.computer_record = computer_record

    def run(self):
        self.computer_record.submit()


def get_checkin_string():
    global checkin_string
    checkin_file = open(str(os.getcwd()) + "/resources/computerCheckin")
    checkin_string = checkin_file.read()
    checkin_file.close()
    return checkin_string


def verify_variables(argv):
    try:
        opts, args = getopt.getopt(argv, "n:b:d:t:", ["n=", "b=", "d=", "t="])
    except getopt.GetoptError:
        print "Incorrect syntax\n" \
              "jssLoadSimulator -n <number of check ins>\n" \
              "\t-b <number of computers per batch>\n" \
              "\t-d <time in seconds between check ins>\n" \
              "\t-t <time in seconds between batches>"
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-n":
            global number_of_times_to_update
            number_of_times_to_update = arg
        elif opt == "-b":
            global number_per_batch
            number_per_batch = arg
        elif opt == "-d":
            global time_between_updates
            time_between_updates = arg
        elif opt == "-t":
            global time_between_batches
            time_between_batches = arg
    if number_of_times_to_update == '' or number_per_batch == '' or time_between_updates == '' \
            or time_between_batches == '':
        print "Incorrect syntax\n" \
              "jssLoadSimulator -n <number of check ins>\n" \
              "\t-b <number of computers per batch>\n" \
              "\t-d <time in seconds between check ins>\n" \
              "\t-t <time in seconds between batches>"
        sys.exit(2)


def verify_jss_details():

    global jss_host
    global jss_port
    global jss_path
    file_path = os.path.expanduser("~/Library/Preferences/com.jamfsoftware.jssloadsimulator.plist")
    if os.path.isfile(file_path):
        jss_info = plistlib.readPlist(file_path)
        jss_host = jss_info['jss_host']
        jss_port = jss_info['jss_port']
        jss_path = jss_info['jss_path']
    if jss_host == '':
            jss_host = prompt_user('JSS Hostname')
    if jss_port == '':
            jss_port = prompt_user('JSS Port')
    if jss_path == '' and not os.path.isfile(file_path):
            jss_path = prompt_user('JSS path (ex https://jss.com:8443/apple enter apple\n JSS path')
    global jss_username
    jss_username = prompt_user('JSS Username')
    global jss_password
    jss_password = getpass.getpass('Enter JSS Password: ')


def prompt_user(variable):
    return raw_input('Enter ' + variable + ': ')


def show_progress(index, total):
    sys.stdout.write('%d / %d\r' % (index, total))
    sys.stdout.flush()


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


def connect_jss_client(path, method, body):
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

if __name__ == "__main__":
    main(sys.argv[1:])