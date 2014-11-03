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
checkin_or_update = ''
jss_host = ""
jss_port = ""
jss_path = ""
jss_username = ""
jss_password = ""


def main(argv):
    verify_variables(argv)
    verify_jss_details()
    computer_record = get_initial_computer()
    checkin_string = get_checkin_string()
    computers = []
    x = 0
    while x < int(number_of_new_computers):
        c = Computer(computer_record, checkin_string, x)
        computers.append(SubmitThread(c))
        x += 1
    for comp in computers:
        comp.start()
    x = 0
    while x < int(number_of_times_to_update):
        print "Waiting " + str(time_between_updates) + " seconds before next update."
        time.sleep(int(time_between_updates))
        for comp in enrolledComputers:
            c = SubmitThread(comp)
            c.start()
        x += 1
    write_settings_to_plist()


class Computer():
    def __init__(self, detail_string, check_in_string, index):
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
        name_file = open('/Users/matthewfjerstad/Documents/LoadSimulator/names')
        name_list = name_file.readlines()
        name_file.close()
        username = name_list[random.randint(0, len(name_list) - 1)].strip()
        computer_name = username \
                        + "'s MacBook Air"
        clean_string = re.sub(r'COMPUTERNAME', '<name>' + str(computer_name) + '</name>', clean_string, )
        location = '<username>' + username + str(random.randint(999, 9999)) + '</username><realname/><email_address>' + username.lower() + \
            '@jamf.com</email_address>'
        clean_string = re.sub(r'LOCATIONINFO', location, clean_string, )
        self.detail_string = clean_string
        clean_checkin = re.sub(r'UDID', '<uuid>' + str(self.udid) + '</uuid>', check_in_string, )
        clean_checkin = re.sub(r'MACADDRESS', '<macAddress bsdName="en0">' + str(self.mac_address) + '</macAddress>', clean_checkin, )
        self.checkin_string = clean_checkin
        self.index = index
        self.computer_id = 0
        global enrolledComputers
        enrolledComputers.append(self)

    def submit(self):
        global checkin_or_update
        if self.computer_id == 0:
            print "Starting to create computer: " + str(self.index)
            device_response = connect_jss("/JSSResource/computers", "POST", self.detail_string)
            device_response = re.sub('"','\"',device_response,)
            try:
                device = xml.dom.minidom.parseString(str(device_response))
                self.computer_id = device.getElementsByTagName('id')[0].childNodes[0].data
            except:
                print "Computer Creation failed"
        elif checkin_or_update == 'u':
            print "Starting to update computer: " + str(self.computer_id)
            update_response = connect_jss("/JSSResource/computers/id/" + str(self.computer_id), "PUT", self.detail_string)
            if xml.dom.minidom.parseString(update_response) == self.computer_id:
                print "Finished updating computer: " + str(self.computer_id)
        elif checkin_or_update == 'c':
            print "Starting to check in computer: " + str(self.computer_id)
            checkin_response = connect_jss_client("/client", "POST", self.checkin_string)
            try:
                response_parse = xml.dom.minidom.parseString(checkin_response.read())
                response_id = response_parse.getElementsByTagName('code')[0].childNodes[0].data
                if str(response_id) == "1501":
                    print "Check in failed for computer: " + self.computer_id + \
                        "\tMake sure Cert Based Communication is disabled"
                elif str(response_id) == "0":
                    print "Check in successful for computer: " + self.computer_id
            except:
                print "failed"
        else:
            print 'Didn\'t create or update'


class SubmitThread(threading.Thread):
    def __init__(self, computer_record):
        threading.Thread.__init__(self)
        self.computer_record = computer_record

    def run(self):
        self.computer_record.submit()


def verify_variables(argv):
    try:
        opts, args = getopt.getopt(argv, "n:u:d:o:", ["n=", "u=", "d=", "o="])
    except getopt.GetoptError:
        print "Incorrect syntax\n" \
              "jssLoadSimulator -n <number of new computers>\n" \
              "\t-u <number of times to update>\n" \
              "\t-d <time in seconds between delay>\n" \
              "\t-o <option for update 'u' or check in 'c'>"
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
        elif opt == "-o":
            global checkin_or_update
            checkin_or_update = arg
    if number_of_times_to_update == '' or number_of_times_to_update == '' or time_between_updates == '' \
            or checkin_or_update == '':
        print "Incorrect syntax\n" \
              "jssLoadSimulator -n <number of new computers>\n" \
              "\t-u <number of times to update>\n" \
              "\t-d <time in seconds between delay>\n" \
              "\t-o <option for update 'u' or check in 'c'>"
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


def get_auth_header(u, p):
    token = base64.b64encode('%s:%s' % (u, p))
    return "Basic %s" % token


def get_initial_computer():
    computer_file = open("/Users/matthewfjerstad/Documents/LoadSimulator/computerXML")
    computer_string = computer_file.read()
    computer_file.close()
    return computer_string

def get_checkin_string():
    checkin_file = open("/Users/matthewfjerstad/Documents/LoadSimulator/computerCheckin")
    checkin_string = checkin_file.read()
    checkin_file.close()
    return checkin_string


def write_settings_to_plist():
    global jss_host
    global jss_port
    global jss_path
    file_path = os.path.expanduser("~/Library/Preferences/com.jamfsoftware.jssloadsimulator.plist")
    plist = { 'jss_host': jss_host,
              'jss_port': jss_port,
              'jss_path': jss_path}
    try:
        print "Saving JSS settings"
        plistlib.writePlist(plist, file_path)
    except TypeError as inst:
        print "\tError writing plist: %s" % inst


def random_mac():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def connect_jss(path, method, body):
    try:
        url = "https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + str(path)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, body)
        request.add_header("Authorization", get_auth_header(jss_username, jss_password))
        request.add_header('Content-Type', 'application/xml')
        request.get_method = lambda: str(method)
        response = opener.open(request)
        return response.read()
    except httplib.HTTPException as inst:
        print "\tException: %s" % inst
    except ValueError as inst:
        print "\tException submitting " + str(method) + " XML: " + str(inst)
    except urllib2.HTTPError as inst:
        print "\tException submitting " + str(method) + " XML: " + str(inst)
    except:
        print "\tUnknown error submitting " + str(method) + " XML"


def connect_jss_client(path, method, body):
    try:
        url = "https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + str(path)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, body)
        request.add_header('Content-Type', 'application/xml')
        request.get_method = lambda: str(method)
        response = opener.open(request)
        return response
    except httplib.HTTPException as inst:
        print "\tException: %s" % inst
    except ValueError as inst:
        print "\tException submitting " + str(method) + " XML: " + str(inst)
    except urllib2.HTTPError as inst:
        print "\tException submitting " + str(method) + " XML: " + str(inst)
    except:
        print "\tUnknown error submitting " + str(method) + " XML"

if __name__ == "__main__":
    main(sys.argv[1:])
