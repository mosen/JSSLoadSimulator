#!/usr/bin/python
#EULA
jss_host = "matt.sup.jamfsw.corp"
jss_port = 8443
jss_path = ""
jss_username = "admin"
jss_password = "jamf1234"
initial_computer_id = 25

import httplib
import base64
import urllib2
import uuid
import re
import random
import xml.dom.minidom
import threading
import time


enrolledComputers = []


def main():
    x = 0
    computer_record = getInitialComputer()
    computer_record = computer_record.replace("<id>" + str(initial_computer_id) + "</id>", "")
    computers = []
    while x < 10:
        c = Computer(computer_record, x)
        computers.append(SubmitThread(c))
        x += 1
    for comp in computers:
        comp.start()
    time.sleep(20)
    for comp in enrolledComputers:
        c = SubmitThread(comp)
        c.start()


class Computer():
    def __init__(self, detail_string, index):
        self.detail_string = randomizeComputer(detail_string)
        self.index = index
        self.computer_id = 0

    def submit(self):
        if self.computer_id == 0:
            print "Starting to create computer: " + str(self.index)
            try:
                url = "https://" + str(jss_host) + ":" + str(jss_port) + str(jss_path) + "/JSSResource/computers"
                opener = urllib2.build_opener(urllib2.HTTPHandler)
                request = urllib2.Request(url, self.detail_string)
                request.add_header("Authorization", getAuthHeader(jss_username, jss_password))
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
                request.add_header("Authorization", getAuthHeader(jss_username, jss_password))
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


def getAuthHeader(u, p):
    token = base64.b64encode('%s:%s' % (u, p))
    return "Basic %s" % token


def getInitialComputer():
    headers = {"Authorization": getAuthHeader(jss_username, jss_password), "Accept": "application/xml"}
    try:
        conn = httplib.HTTPSConnection(jss_host, jss_port)
        conn.request("GET", jss_path + "/JSSResource/computers/id/" + str(initial_computer_id), None, headers)
        data = conn.getresponse().read()
        conn.close()
        return data
    except httplib.HTTPException as inst:
        print "Could not get first computer's details. Exception: %s" % inst


def randomizeComputer(computer_string):
    clean_string = re.sub(r'<serial_number>...........</serial_number>',
                         '<serial_number>' + str(random.randint(9999999999, 99999999999)) + '</serial_number>',
                         computer_string, )
    clean_string = re.sub(r'<udid>....................................</udid>', '<udid>' + str(uuid.uuid1()) + '</udid>',
                         clean_string, )
    clean_string = re.sub(r'<mac_address>.................</mac_address>',
                         '<mac_address>' + str(randomMAC()) + '</mac_address>', clean_string, )
    clean_string = re.sub(r'<alt_mac_address>.................</alt_mac_address>',
                         '<alt_mac_address>' + str(randomMAC()) + '</alt_mac_address>', clean_string, )
    return clean_string


def randomMAC():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


main()
