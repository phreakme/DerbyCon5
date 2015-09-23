############################################################
# 			Change History
# 2015-09-21 - Initial DerbyCon Release
############################################################
#!/usr/bin/env python

# These are required fields
from src.core.setcore import *
import sys
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import os
import urlparse
import re
import getpass
import json
from src.core.menu import text
from src.core import setcore as core
from time import sleep
import warnings


############################################################
# Global Variables
############################################################
debug = False # Set to True for some extra debugging output
HTMLCODES = [
	['&lt;', '<'],
	['&gt;', '>'],
]

MAIN="PhreakMe"
AUTHOR = "Phreakme - Owen (Snide) & Patrick (Unregistered436)"

PHONE = re.compile("^[0-9]{10}$")

#############################################################################
# Site data class
#############################################################################
class siteData:
   def __init__(self, url):
	self.url = url

#############################################################################
# Print cool banner :) 
#############################################################################
# Note that backslashes have to be escaped so this looks odd
def printBanner():
	print("   ___ _                    _                ")
	print("  / _ \\ |__  _ __ ___  __ _| | __ /\\/\\   ___ ")
	print(" / /_)/ '_ \\| '__/ _ \\/ _` | |/ //    \\ / _ \\")
	print("/ ___/| | | | | |  __/ (_| |   </ /\\/\\ \\  __/")
	print("\\/    |_| |_|_|  \\___|\\__,_|_|\\_\\/    \\/\\___|")

#############################################################################
# Send an authentication request to the server 
#############################################################################
def serverAuth(site):
	site.auth = False

	try:
	   auth_request = requests.get(site.url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)

	   if auth_request.status_code == requests.codes.ok:
		site.auth = True
		print("\r\nConnection test to PhreakMe server succeeded ...\r\n")
	   else:
		print_warning ("\r\nPhreakMe server authentication failed. Server URL, username, or password are incorrect. Verify server status or reset server info.") 
	   return True

	except Exception, e:
	   errormsg = str(e)
	   if "CERTIFICATE_VERIFY_FAILED" in errormsg:
	      print_warning("\r\nInvalid Server Certificate!: Verify certificate is valid or disable certificate validation in PhreakMe URL setup.")
	   elif "Connection aborted" in errormsg:
	      print_warning("\r\nPhreakMe server URL not available. Verify server is up and URL was formatted correctly.")
	   else:
	      print_warning("\r\nException: " + errormsg)

	   return False


#############################################################################
# Get the URL of the Phreak Me server
#############################################################################
def getURL(site):
	site.auth = False
	site.user = ""
	site.passwd = ""
	site.certverify = False
  	site.url = raw_input("Enter the PhreakMe site URL (ex: https://www.phreakme.com): ")
	if not site.url:
	   site.url = "https://www.phreakme.com"
	   print ("\r\nUsing Default: " + site.url + "\r\n")
	# enter some URL validation code here
	if debug: print (site.url)

	if "https:" in site.url:
  	   site.certverify_input = raw_input("Verify site certificate? (Leave default if self-signed or snake-oil certificate is in use) (Y/N)[N]: ")
	   if site.certverify_input.lower() == "y": site.certverify = True

	auth_input = "N"
  	auth_input = raw_input("Is authentication required? (Y/N)[Y]: ")
	if auth_input.lower() == "n":
		site.auth = False
	else:
		site.auth = True
		while not site.user:
		    site.user = raw_input("Enter the PhreakMe username: ")

		passwd = lambda: (getpass.getpass("Enter the password for [" + site.user + "]:"), getpass.getpass("Retype password for verification: "))
		
		site.passwd, p2 = passwd()
		while site.passwd != p2:
		    print("Passwords do not match. Try again")
		    site.passwd, p2 = passwd()

	if not serverAuth(site):
		print_warning ("Server Authentication failed. Please re-run Phreakme Server URL Setup.")
		site.url = None

	return

#############################################################################
# Retrieve the target list for a calling campaign 
#############################################################################
def getTargets(site):
	if debug: print("get targets " + site.url)
	get_url = site.url + "/service/setup/targets/"   
	if debug: print("get_url " + get_url)
   	request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	if request.status_code != requests.codes.ok:
	   print_warning("** Call target list not retrieved. Server error code received") 
	else:
	   print ("\r\nNumbers to be exploited are: " + str(request.text) + "\r\n")

#############################################################################
# Replace HTML code values with printable chars. Chars to be replaced are
# defined as a global variable at top 
#############################################################################
def replaceHTMLCodes(string_input):
	for code in HTMLCODES:
		string_input = string_input.replace(code[0], code[1])
	return string_input

#############################################################################
# Ask the server what number is default for spoofed calls 
#############################################################################
def getSpoofedNum(site):
	get_url = site.url + "/service/setup/globalcid"   
   	request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	if request.status_code != requests.codes.ok:
	   print_warning("** Default spoofing number not set. Server error code received")
	else:
	   requestNum = str(request.text)
	   spoofedNum = replaceHTMLCodes(requestNum)
	   print ("\r\nNumber for spoofed calls: " + spoofedNum + "\r\n\r\n")

#############################################################################
# List current recording selection 
#############################################################################
# Recordings are returned in a list of pairs with a number and file name. 
# There are only three recording entries as of the latest version of phreakme
# and the current recording and it's human readable index is returned as a
# fourth entry in the list, thus a -1 is used to find the list index
############################################################################

def currentRecording(site, recording):

	get_url = site.url + "/service/setup/recordings"   
	request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
  	if request.status_code != requests.codes.ok:
	   print_warning("** Recording data retrieval failed. Server error code received")
	   return (recording)
	else:
		request_json = json.loads(request.text)
		cur_rec_name = request_json[3]['current_recording']
		cur_rec_index = int(request_json[3]['current_recording']) -1
		recording = request_json[cur_rec_index][cur_rec_name]
		return (recording)

	return (recording)

#############################################################################
# Print the list of the three recordings available 
#############################################################################
def recordingsList(site):

	get_url = site.url + "/service/setup/recordings"   
	request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
  	if request.status_code != requests.codes.ok:
   	   print_warning("** Recording data retrieval failed. Server error code received")
	   return(site)

	request_json = json.loads(request.text)
	print("************************************************")
	print("Recording  Filename                             ")
	print("************************************************")
	print("    1)     " + request_json[0]['1'])
	print("    2)     " + request_json[1]['2'])
	print("    3)     " + request_json[2]['3'])
	print("************************************************")
	return(site)

#############################################################################
# Set up recording selection 
#############################################################################
def recordingsMenu(site):
	setup_menu = ['Display Current Recording', 'List Available Recordings', 'Select Default Recording for Calls', 'Exit Recording Menu']
	recording = None

	exit = False
	while not exit:
	    core.create_menu("\r\n==Recording Setup Menu==", setup_menu)
	    setup_menu_choice = (raw_input(setprompt("0", "")))
	    if setup_menu_choice == "1":
		recording = currentRecording(site, recording)
		if recording:
			print("\r\nThe current recording in use for all calls is: " + recording + "\r\n")
		else:
			print_warning("\r\nThere is no current recording found. Please set one.\r\n")

	    if setup_menu_choice == "2":
		recordingsList(site)
		
	    if setup_menu_choice == "3":
		selection = None
		recordingsList(site)

		regex = False
		while not selection:
	   	   selection = raw_input("Enter the number of the recording you wish to use and hit <Enter>: ")
		   pat = re.compile("^[1-3]{1}$") 
		   if pat.match(selection):
		   	selection = str(selection)
			regex = True

		post_url = site.url + "/service/setup/recordings/" + selection    
		request = requests.post(post_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
		if request.status_code != requests.codes.ok:
		      print_warning("** Default spoofing number not set. Server error code received")
		else:
		      print("Recording selection " + selection + " saved.\r\n")

	    if setup_menu_choice == "4":
		exit = True


#############################################################################
# Set up number to spoof 
#############################################################################
def spoofMenu(site):
	if debug: print ("Default Spoofing Number Setup Menu")
	setup_menu = ['Set Default Spoofing Number', 'Display Current Spoofing Number', 'Exit Spoofing Number Menu']

	exit = False
	while not exit:
	    core.create_menu("\r\n==Default Spoofing Number Setup Menu==", setup_menu)
	    setup_menu_choice = (raw_input(setprompt("0", "")))
	    if setup_menu_choice == "1":

		spoof_number = None
		regex = False
		while not regex:
  		   spoof_number = raw_input("Enter a ten digit number to use for spoofed calls: ")
		   if PHONE.match(spoof_number):
		   	spoof_number = str(spoof_number)
			regex = True

		spoof_name = None
		regex = False
		while not regex:
  		   spoof_name = raw_input("Enter a caller name up to 15 chars in case your trunking provider supports setting CNAM (though many don't): ")
		   pat = re.compile("^[a-zA-Z0-9 ]{1,15}$")
		   if pat.match(spoof_name):
		   	spoof_name = str(spoof_name)
			regex = True

	   	post_url = site.url + "/service/setup/globalcid/" + spoof_number + " <" + spoof_name + ">"    

		if debug: print ("Sending spoofed number request: " + post_url)
   		request = requests.post(post_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	if request.status_code != requests.codes.ok:
		   print_warning("** Default spoofing number not set. Server error code received")
		else:
		   getSpoofedNum(site)

	    elif setup_menu_choice == "2":
		getSpoofedNum(site)

	    elif setup_menu_choice == "3":
		exit = True


#############################################################################
# Set up numbers to exploit
#############################################################################

def setupMenu(site):
	if debug: print ("Setup Menu")
	setup_menu = ['Add Target', 'Remove Target', 'List Targets', 'Default Spoofed Number Setting', 'Default Recording Setting', 'Exit Setup Menu']

	exit = False
	while not exit:
	    core.create_menu("\r\n==Phreakme Setup Menu==", setup_menu)
	    setup_menu_choice = (raw_input(setprompt("0", "")))
	    if setup_menu_choice == "1":
		regex = False
		while not regex:
  		    new_number = raw_input("Enter a ten digit number to add to the target exploit list: ")
		    if PHONE.match(new_number):
		    	new_number = str(new_number)
			regex = True

	   	post_url = site.url + "/service/setup/targets/"	+ new_number    
   		request = requests.post(post_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	if request.status_code != requests.codes.ok:
		   print_warning("** Number not added. Server error code received")
		else:
		   getTargets(site)

	    elif setup_menu_choice == "2":
		regex = False
		while not regex:
  		    del_number = raw_input("Enter a ten digit number to remove from the target exploit list: ")
		    if PHONE.match(del_number):
		    	new_number = str(del_number)
			regex = True

	   	del_url = site.url + "/service/setup/targets/" + del_number    
   		request = requests.delete(del_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	if request.status_code != requests.codes.ok:
		   print_warning("** Number not removed. Server error code received")
		else:
		   getTargets(site)

	    elif setup_menu_choice == "3":
		getTargets(site)

	    elif setup_menu_choice == "4":
		spoofMenu(site)

	    elif setup_menu_choice == "5":
		recordingsMenu(site)

	    elif setup_menu_choice == "6":
		exit = True

#############################################################################
# Exploit one or more numbers
#############################################################################
def exploitMenu(site):
	if debug: print ("Exploit Menu")
	exploit_menu = ['Exploit Single Target', 'Exploit All Targets', 'Exit Exploit Menu']
	exit = False
	while not exit:
	    core.create_menu("\r\n==Exploit Selection Menu==", exploit_menu)
	    exploit_menu_choice = (raw_input(setprompt("0", "")))
	    if exploit_menu_choice == "1":

		regex = False
		while not regex:
  		    exp_number = raw_input("Enter a ten digit number to exploit: ")
		    if PHONE.match(exp_number): 
		        exp_number = str(exp_number)
			regex = True

		regex = False
		while not regex:
  		    cid_number = raw_input("Enter a ten digit number to spoof: ")
		    if PHONE.match(cid_number):
		    	cid_number = str(cid_number)
			regex = True

	   	get_url = site.url + "/service/exploit/" + exp_number + "/" + cid_number   
   		request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	if request.status_code != requests.codes.ok:
		   print_warning("** Exploit command failed. Server error code received")
		else:
		   print ("\r\nMaking the call, please wait a sec... \r\n")

	    elif exploit_menu_choice == "2":
	   	post_url = site.url + "/service/exploit/all"   
   		request = requests.post(post_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	if request.status_code != requests.codes.ok:
		   print_warning("** Exploit All command failed. Server error code received")
		else:
		   print ("\r\nMaking the calls, please wait a sec... \r\n")

	    elif exploit_menu_choice == "3":
		exit = True


#############################################################################
# Reporting Menu
#############################################################################
def reportingMenu(site):
	if debug: print ("Reporting Menu")
	reporting_menu = ['Calls With User Input', 'Calls With No User Input Received', 'Archive Call Data', 'Delete Call Data', 'Exit Reporting Menu']

	exit = False
	while not exit:
	    core.create_menu("\r\n==Reporting Menu==", reporting_menu)
	    reporting_menu_choice = (raw_input(setprompt("0", "")))
	    if reporting_menu_choice == "1":
	   	get_url = site.url + "/service/report"   
   		request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
		if debug: print(request.text)

	   	if request.status_code != requests.codes.ok:
		   print_warning("** Report data retrieval failed. Server error code received")

		request_json = json.loads(request.text)
		if debug: print(request_json)
		if len(request_json) > 0:
		   print("\r\n************************************************")
		   print("Date and Time        Number Dialed  User Input")
		   print("************************************************")
		   for i in range (0, len(request_json)):
			if request_json[i]['Input']:
			   print(request_json[i]['Created'] + "  " + request_json[i]['Dialed'] + "     " + request_json[i]['Input'])

		   print("************************************************\r\n")
		else:
		   print("\r\nNo call data found ...\r\n")

	    if reporting_menu_choice == "2":
	   	get_url = site.url + "/service/report"   
   		request = requests.get(get_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	if request.status_code != requests.codes.ok:
		   print_warning("** Report data retrieval failed. Server error code received")

		request_json = json.loads(request.text)
		if debug: print(request_json)
		if len(request_json) > 0:
		   print("\r\n************************************************")
		   print("Date and Time        Number Dialed")
		   print("************************************************")
		   for i in range (0, len(request_json)):
			if not request_json[i]['Input']:
			   print(request_json[i]['Created'] + "  " + request_json[i]['Dialed'])
		   print("************************************************\r\n")
		else:
		   print("\r\nNo call data found ...\r\n")

	    if reporting_menu_choice == "3":
	   	post_url = site.url + "/service/report/delete"   
		print_warning("WARNING: This option will archive data on the PhreakMe server. CLI access on the server is required to recover data.")
		warning_input = raw_input("Proceed with data archive? (Y/N)[N]: ")
		if warning_input.lower() == "y":
   		   request = requests.post(post_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	   if request.status_code == requests.codes.ok:
			print("** Report data archived")
		   else:
			print("** Report archive failed. Server error code received")
		else:
		   print("\r\nData archive skipped ...\r\n")

	    if reporting_menu_choice == "4":
	   	post_url = site.url + "/service/report/delete/noarchive"   
		print_warning("WARNING: This option will permanently DELETE report data on the PhreakMe server.")
		warning_input = raw_input("Proceed with data delete? (Y/N)[N]: ")
		if warning_input.lower() == "y":
   		   request = requests.post(post_url, auth=HTTPBasicAuth(site.user, site.passwd), verify = site.certverify)
	   	   if request.status_code == requests.codes.ok:
			print("** Report data deleted")
		   else:
			print("** Report delete failed. Server error code received")
		else:
			print("\r\nData delete skipped...\r\n")

	    elif reporting_menu_choice == "5":
		exit = True


#############################################################################
# Main method
#############################################################################
def main():

    printBanner()

    with warnings.catch_warnings():
	warnings.simplefilter("ignore")
	valid_ip = False
	phreak_menu = ['Setup PhreakMe Server URL', 'Setup', 'Exploit', 'Reporting', 'Exit']
	site = siteData("")
#	site.url = ""
	site.auth = False
	site.user = ""
	site.passwd = ""
	site.certverify = False

	exit = False
	while not exit:
	  try:
	    core.create_menu("\r\n==PhreakMe Menu==", phreak_menu)
	    if not site.url: print_warning ("	Make sure to enter a PhreakMe Server URL before selecting other options!")
	    phreak_menu_choice = (raw_input(setprompt("0", "")))
	
	    if phreak_menu_choice == "1":
	       getURL(site)
	    elif phreak_menu_choice == "2":
	       setupMenu(site)
	    elif phreak_menu_choice == "3":
	       exploitMenu(site)
	    elif phreak_menu_choice == "4":
	       reportingMenu(site)
	    elif phreak_menu_choice == "5":
	       exit = True
	    elif phreak_menu_choice == "hugs":
               print_warning("***********************************\r\n")
               print_warning("Hugs Are Now Mandatory \o/ \r\n")
               print_warning("***********************************\r\n")
	    elif phreak_menu_choice == "banner":
	       printBanner()
	    else:
	       print_warning ("Did you not get enough hugs as a child? Follow directions and enter a valid selection.\r\n")

	  except (KeyboardInterrupt):
	       exit = True
	       pause=raw_input("\r\n\r\nExiting Phreakme - press [enter] to return to SET main menu")
	       return

