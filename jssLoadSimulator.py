#!/usr/bin/python
#EULA


import httplib
import base64
import urllib2
import uuid
import re
import random
import xml.dom.minidom
import threading
import time
import sys
import getopt
import os
import plistlib
import getpass


enrolledComputers = []
number_of_new_computers = ''
number_of_times_to_update = ''
time_between_updates = ''
jss_host = ""
jss_port = ""
jss_path = ""
jss_username = ""
jss_password = ""
initial_computer_id = ""


def main(argv):
    verify_variables(argv)
    verify_jss_details()
    computer_record = get_initial_computer()
    computer_record = computer_record.replace("<id>" + str(initial_computer_id) + "</id>", "")
    computers = []
    x = 0
    while x < int(number_of_new_computers):
        c = Computer(computer_record, x)
        computers.append(SubmitThread(c))
        x += 1
    for comp in computers:
        comp.start()
    x = 0
    while x < int(number_of_times_to_update):
        for comp in enrolledComputers:
            c = SubmitThread(comp)
            c.start()
        print "Waiting " + str(time_between_updates) + " seconds before next update."
        time.sleep(int(time_between_updates))
        x += 1
    write_settings_to_plist()

class Computer():
    def __init__(self, detail_string, index):
        self.detail_string = randomize_computer(detail_string)
        self.index = index
        self.computer_id = 0

    def submit(self):
        if self.computer_id == 0:
            print "Starting to create computer: " + str(self.index)
            try:
                url = "https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + "/JSSResource/computers"
                opener = urllib2.build_opener(urllib2.HTTPHandler)
                request = urllib2.Request(url, self.detail_string)
                request.add_header("Authorization", get_auth_header(jss_username, jss_password))
                request.add_header('Content-Type', 'application/xml')
                request.get_method = lambda: 'POST'
                response = opener.open(request)
                try:
                    device = xml.dom.minidom.parseString(response.read())
                    self.computer_id = device.getElementsByTagName('id')[0].childNodes[0].data
                except:
                    print "Failure parsing computer POST response"
                enrolledComputers.append(self)
                print "Finished creating computer: " + str(self.computer_id)
            except httplib.HTTPException as inst:
                print "\tException: %s" % inst
            except ValueError as inst:
                print "\tException submitting POST XML: %s" % inst
            except urllib2.HTTPError as inst:
                print "\tException submitting POST XML: %s" % inst
            except:
                print "\tUnknown error submitting POST XML"
        else:
            print "Starting to update computer: " + str(self.computer_id)
            try:
                url = "https://" + str(jss_host) + ":" + str(jss_port) + str(
                    jss_path) + "/JSSResource/computers/id/" + str(self.computer_id)
                opener = urllib2.build_opener(urllib2.HTTPHandler)
                request = urllib2.Request(url, self.detail_string)
                request.add_header("Authorization", get_auth_header(jss_username, jss_password))
                request.add_header('Content-Type', 'application/xml')
                request.get_method = lambda: 'PUT'
                opener.open(request)
                print "Finished updating computer: " + str(self.computer_id)
            except httplib.HTTPException as inst:
                print "\tException: %s" % inst
            except ValueError as inst:
                print "\tException submitting PUT XML: %s" % inst
            except urllib2.HTTPError as inst:
                print "\tException submitting PUT XML: %s" % inst
            except:
                print "\tUnknown error submitting PUT XML"


class SubmitThread(threading.Thread):
    def __init__(self, computer_record):
        threading.Thread.__init__(self)
        self.computer_record = computer_record

    def run(self):
        self.computer_record.submit()


def verify_variables(argv):
    try:
        opts, args = getopt.getopt(argv, "n:u:d:", ["n=", "u=", "d="])
    except getopt.GetoptError:
        print "Incorrect syntax\n" \
              "jssLoadSimulator -n <number of new computers>\n" \
              "\t-u <number of times to update>\n" \
              "\t-d <time in seconds between delay>\n"
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-n":
            global number_of_new_computers
            number_of_new_computers = arg
        elif opt == "-u":
            global number_of_times_to_update
            number_of_times_to_update = arg
        elif opt == "-d":
            global time_between_updates
            time_between_updates = arg
    if number_of_times_to_update == '' or number_of_times_to_update == '' or time_between_updates == '':
        print "Incorrect syntax\n" \
              "jssLoadSimulator -n <number of new computers>\n" \
              "\t-u <number of times to update>\n" \
              "\t-d <time in seconds between delay>\n"
        sys.exit(2)


def verify_jss_details():

    global jss_host
    global jss_port
    global jss_path
    global initial_computer_id
    file_path = os.path.expanduser("~/Library/Preferences/com.jamfsoftware.jssloadsimulator.plist")
    if os.path.isfile(file_path):
        jss_info = plistlib.readPlist(file_path)
        jss_host = jss_info['jss_host']
        jss_port = jss_info['jss_port']
        jss_path = jss_info['jss_path']
        initial_computer_id = jss_info['initial_computer_id']
    if jss_host == '':
            jss_host = prompt_user('JSS Hostname')
    if jss_port == '':
            jss_port = prompt_user('JSS Port')
    if jss_path == '' and not os.path.isfile(file_path):
            jss_path = prompt_user('JSS path (ex https://jss.com:8443/apple enter apple\n JSS path')
    if initial_computer_id == '':
            initial_computer_id = prompt_user("initial computer's JSS ID")
    global jss_username
    jss_username = prompt_user('JSS Username')
    global jss_password
    jss_password = getpass.getpass('Enter JSS Password: ')


def prompt_user(variable):
    return raw_input('Enter ' + variable + ': ')


def get_auth_header(u, p):
    token = base64.b64encode('%s:%s' % (u, p))
    return "Basic %s" % token


def get_initial_computer():
    headers = {"Authorization": get_auth_header(jss_username, jss_password), "Accept": "application/xml"}
    try:
        conn = httplib.HTTPSConnection(jss_host, jss_port)
        conn.request("GET", jss_path + "/JSSResource/computers/id/" + str(initial_computer_id), None, headers)
        data = conn.getresponse().read()
        conn.close()
        return data
    except httplib.HTTPException as inst:
        print "Could not get first computer's details. Exception: %s" % inst


def write_settings_to_plist():
    global jss_host
    global jss_port
    global jss_path
    global initial_computer_id
    file_path = os.path.expanduser("~/Library/Preferences/com.jamfsoftware.jssloadsimulator.plist")
    plist = { 'jss_host': jss_host,
              'jss_port': jss_port,
              'jss_path': jss_path,
              'initial_computer_id': initial_computer_id}
    try:
        print "Saving JSS settings"
        plistlib.writePlist(plist, file_path)
    except TypeError as inst:
        print "\tError writing plist: %s" % inst


def randomize_computer(computer_string):
    clean_string = re.sub(r'<serial_number>...........</serial_number>',
                          '<serial_number>' + str(random.randint(9999999999, 99999999999)) + '</serial_number>',
                          computer_string, )
    clean_string = re.sub(r'<udid>....................................</udid>', '<udid>' + str(uuid.uuid1()) + '</udid>',
                          clean_string, )
    clean_string = re.sub(r'<mac_address>.................</mac_address>',
                          '<mac_address>' + str(random_mac()) + '</mac_address>', clean_string, )
    clean_string = re.sub(r'<alt_mac_address>.................</alt_mac_address>',
                          '<alt_mac_address>' + str(random_mac()) + '</alt_mac_address>', clean_string, )
    return clean_string


def random_mac():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


if __name__ == "__main__":
    main(sys.argv[1:])
