#
# Copyright (C) 2014 Cisco Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The following script check if vlans are consistant across different switches.
# If not, then this script will insert the missing vlans
# default cdv file is vlan-list.csv

import sys
from optparse import OptionParser
import json
import requests
import ast
import csv 
from string import Template


my_headers = {'content-type': 'application/json-rpc'}
os_ver = str("nada")

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="name of csv file", metavar="FILE", default="vlan-list.csv")
parser.add_option("-r", "--remove",
                  action="store_true", dest="removing", default=False,
                  help="also remove extra vlans found")
parser.add_option("-v", "--version",
                  action="store_true", dest="vercheck", default=False,
                  help="Compare Version")
parser.add_option("-l", "--vlan",
                  action="store_true", dest="vlancheck", default=False,
                  help="Compare Version")


(options, args) = parser.parse_args()
print "Vlans file is " +options.filename
if options.removing:
    print "removing vlans"
else:
    print "not removing vlans"
    
switches=[]
required_vlans=[]
vlan_names=[]
with open(options.filename, 'rU') as f:  #opens PW file
    reader = csv.reader(f)
    # Print every value of every row. 
    for row in reader:
        if row[0] == 'username':
            username=row[1]
        elif row[0] == 'password':
            password =row[1]
        elif row[0] == 'switches':
            for each in row:
                switches.append(each)
        elif row[0] == 'vlans':
            for each in row:
                if each != "vlans":
                    vlan=int(each)
                else:
                    vlan=each
                required_vlans.append(vlan)
        elif row[0] == 'names':
            for each in row:
                vlan_names.append(each)                
        elif row[0] == 'kickstart':
            expect_kickstart =row[1]
        elif row[0] == 'system_image':
            expect_system =row[1]

f.close()


switches.remove('switches')
switches.remove('')
required_vlans.remove('vlans')
vlan_names.remove('names')
switch=[]
for each in switches:
    if each !="":
        switch.append([each,username,password])
namelookup=dict(zip(required_vlans, vlan_names))
print (namelookup)



#######################################
req_vlans_sort = required_vlans.sort()
jsonrpc_template = Template("{'jsonrpc': '2.0', 'method': '$method', 'params': ['$params', 1], 'id': '$jrpc_id'}")


#conf_vlan_payload = 
def check_vlan_consistancy(row):
        vlans = []
        switch_ip = row[0]
        username = row[1]
        password = row[2]

        payload = [{'jsonrpc': '2.0', 'method': 'cli', 'params': ['show vlan',1], 'id': '1'}]
        my_data = json.dumps(payload)
        
        url = "http://"+switch_ip+"/ins"
        response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))

        #parse information of show vlan    
        vlan_table = response.json()['result']['body']['TABLE_mtuinfo']['ROW_mtuinfo']
        for iter in vlan_table:
            
            vlans.append(int(iter['vlanshowinfo-vlanid']))

        vlans.sort()

        missing_vlans = list(set(required_vlans)-set(vlans))
        extra_vlans = list(set(vlans)-set(required_vlans))
        if (vlans != required_vlans) and (missing_vlans != []):
            
            print ("is missing_vlans: "+str(sorted(missing_vlans)))
            config_vlans(row, missing_vlans)
            if extra_vlans !=[]:
                print ("has extra vlans: "+str(sorted(extra_vlans)))
                if options.removing:
                    removing_vlans (row,extra_vlans)
        elif (missing_vlans == []):
            print ("is NOT missing any of the required vlans")
            if extra_vlans !=[]:
                print ("has extra vlans: "+str(sorted(extra_vlans)))
                if options.removing:
                    removing_vlans (row,extra_vlans)
        else:
            return 1
        print "\n-----------"

def config_vlans(row, missing_vlans):   

    switch_ip = row[0]
    username = row[1]
    password = row[2]

    print ("Configuring the following vlans  "+str(sorted(missing_vlans)))

    url = "http://"+switch_ip+"/ins"
    
    batch_cmd = "["
    id_counter = 1
    
    command = "conf t"
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')
    
    for v in missing_vlans:
        batch_cmd += ','
        command = 'vlan ' + str(v)
        id_counter += 1
        batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')

        batch_cmd += ','
        command = 'name ' + str(namelookup.get(v))
        id_counter += 1
        batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')

    batch_cmd = batch_cmd + "]"
    my_data = json.dumps(ast.literal_eval(batch_cmd))

    response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))
    #print (response.text)
                                               
def removing_vlans(row, extra_vlans):   

    switch_ip = row[0]
    username = row[1]
    password = row[2]

    print ("Removing the following vlans  "+str(sorted(extra_vlans)))

    url = "http://"+switch_ip+"/ins"
    
    batch_cmd = "["
    id_counter = 1
    
    command = "conf t"
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')
    
    for v in extra_vlans:
        batch_cmd += ','
        command = 'no vlan ' + str(v)
        id_counter += 1
        batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')

    batch_cmd = batch_cmd + "]"
    my_data = json.dumps(ast.literal_eval(batch_cmd))

    response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))
    #print (response.text)
                                               
def compare_versions(row):
    global os_ver
    switch_ip = row[0]
    username = row[1]
    password = row[2]

    print ("Verify Version")

    url = "http://"+switch_ip+"/ins"

    
    payload=[{"jsonrpc": "2.0","method": "cli","params": {"cmd": "show version","version": 1.2},"id": 1}]
    my_data = json.dumps(payload)
    response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))
    
    #print (response.text)
    kick_start_image = response.json()['result']['body']['kickstart_ver_str']
    system_image = response.json()['result']['body']['sys_ver_str']
    host_name = response.json()['result']['body']['host_name']
    
    print ("")
    print ("===============================")
    print ('host name:'+ host_name)
    print ('kickstart image version :' + kick_start_image)
    print ('system image version :s' + system_image)
    print ("===============================")

    if os_ver == "nada" :
        print ("Marker Version")
        os_ver = system_image
    elif system_image == os_ver:
        print ("Compliant")
    else:
        print ("NON Compliant version")


def main():
    if options.vercheck:
           for row in switch:
               print "Version check for Switch ", row[0]
               compare_versions(row)
    if options.vlancheck:
        print ("**** Calling vlan consistency checker ***")
        print ("Expected VLANS:", required_vlans)
        for row in switch:
            print "Switch ",row[0]
            consistant = check_vlan_consistancy(row)

        print ("*** Vlan consistency checker complete ***")
if __name__ == "__main__":
    main()
 

