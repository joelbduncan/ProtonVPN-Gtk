import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk
import subprocess
from threading import Thread
import socket
import time
from ConfigParser import SafeConfigParser
import os
import sys


from time import sleep
from subprocess import Popen, PIPE

# OpenVPN Gateway IP Address for connection status
remoteServer = "10.8.8.1"

# Checks for root execution
if not os.geteuid() == 0:
	sys.exit("Root access is required to use ProtonVPN-Gtk...")

missingDependencies = False
modulesRequired = ""

# Checks that protonvpn-cli is installed
try:
	subprocess.check_output(['which', 'protonvpn-cli'])
except subprocess.CalledProcessError, e:
	modulesRequired += "protonvpn-cli needs to be installed.\n"
	missingDependencies = True

# Checks for the python-schedule module
try:
	import schedule
except ImportError:
	missingDependencies = True
	modulesRequired += "python-schedule needs to be installed.\n"

# Checks for the python-requests module
try:
	import requests
except ImportError:
	missingDependencies = True
	modulesRequired += "python-requests needs to be installed.\n"

# Checks for the python-json module
try:
	import json
except ImportError:
	missingDependencies = True
	modulesRequired += "python-json needs to be installed.\n"

# Exits ProtonVPN.py execution with missing dependencies
if(missingDependencies):
	sys.exit(modulesRequired)

# Setup GUI Handlers
class Handler():

	def __init__(self):
		# Connect GUI components
		self.browseServer = builder.get_object('browseServer')
		self.protocolSelection = builder.get_object('protocolSelection')
		self.statusLabel = builder.get_object('statusLabel')
		self.locationLabel = builder.get_object('locationLabel')
		self.ipAddressLabel = builder.get_object('ipAddressLabel')
		self.connectionProgress = builder.get_object('connectionProgress')
		self.progressBar = builder.get_object('progressBar')

		# Server selection radio Button group
		self.radioBtnStandard = builder.get_object('radioBtnStandard')
		self.radioBtnSecureCore = builder.get_object('radioBtnSecureCore')
		self.radioBtnTor = builder.get_object('radioBtnTor')
		self.radioBtnP2P = builder.get_object('radioBtnP2P')

		builder.connect_signals(self)

		global protonVPNTier
		global protonVPNData

		# Load ProtonVPN server details into variable
		protonServerReq = requests.get("https://api.protonmail.ch/vpn/logicals")
		protonServerReq.text

		# Convert it to a Python dictionary
		protonVPNData = json.loads(protonServerReq.text)

		# Open/Read/Close ProtonVPN Tier config file
		currentUser =  os.environ['SUDO_USER']
		with open("/home/" + currentUser + "/.protonvpn-cli/protonvpn_tier",'r') as f:
			protonVPNTier = f.read()

		# Populate Server list
		self.radioBtnSelection(radioSelected="0")

		# Populate potocol selection
		self.protocolSelection.insert(0, "tcp", "TCP")
		self.protocolSelection.insert(0, "udp", "UDP")

		# Read Config file
		parser = SafeConfigParser()
		parser.read('config.ini')

		# Set last connected server as default
		self.browseServer.set_active_id(parser.get('globalVars', 'lastConnection'))
		self.protocolSelection.set_active_id(parser.get('globalVars', 'protocol'))

		global currentConnectionStatus
		currentConnectionStatus = False

		# Start thread for connectionStatus
		self.thread = Thread(target=self.connectionStatus)
		self.thread.daemon = True
		self.thread.start()

	# Check VPN connection status & upadte location infomation
	def connectionStatus(self):
		global currentConnectionStatus
		while True:
			print "Updating"
			try:
				time.sleep(2)

				self.fetchIP()
				
				send_url = 'http://dl.slethen.io/api.php'
				r = requests.get(send_url)
				j = json.loads(r.text)

				if str(j) != currentConnectionStatus:
					currentConnectionStatus = str(j)

					if "True" in str(j):
						print 'True'
						GObject.idle_add(self.statusLabel.set_text, str("Connected"))
						self.connectionProgress.stop()
					if "False" in str(j):
						print 'False'
						GObject.idle_add(self.statusLabel.set_text, str("Disconnected"))

			except Exception as e: print(e), "Error in currentConnectionStatus"

	# Get current IP address/Location
	def fetchIP(self):
		try:
			send_url = 'https://api.protonmail.ch/vpn/location'
			r = requests.get(send_url)
			j = json.loads(r.text)
			countryName = j['Country']
			ipAddress = j['IP']			# Update Location & IP Address labels on Gtk window
			GObject.idle_add(self.locationLabel.set_text, str(countryName))
			GObject.idle_add(self.ipAddressLabel.set_text, str(ipAddress))

		except Exception as e: print(e), "Error in fetchIP"

	def connectionTimeout(self):
		print "Connection Timeout"
		time.sleep(30)
		self.connectionProgress.stop()
		pass

	# Populate browserServer based on Toggle switch selected
	def radioBtnSelection(self, radioSelected):
		global protonVPNTier
		global protonVPNData

		self.browseServer.remove_all()

		# Temp used to display load (Future feature)
		self.progressbar = Gtk.ProgressBar()

		for item in protonVPNData['LogicalServers'][::-1]:
			if str(radioSelected) in str(item['Features']):

				# Loop through the result.
				# Free users protonTier = 1
				if "0" in protonVPNTier:
					if "0" in str((item['Tier'])):
						self.browseServer.insert(0, (item['Name']), (item['Domain']))

				# Basic users protonTier = 2
				if "1" in protonVPNTier:
					if str((item['Tier'])) == "1" or str((item['Tier'])) == "2":
						self.browseServer.insert(0, (item['Name']), (item['Domain']))

				# Plus & Visionary users protonTier = 3
				if "2" in protonVPNTier:
					if str((item['Tier'])) == "1" or str((item['Tier'])) == "2" or str((item['Tier'])) == "3":
						self.browseServer.insert(0, (item['Name']), (item['Domain']))

# I have no idea what this code does?
# This causes the VPN selection list to have duplicate entrys
# Removed for now.
#
#
#			if str(radioSelected) in str(item['Features']):
#				if "1" in protonVPNTier:
#					if str((item['Tier'])) == "1" or str((item['Tier'])) == "2":
#						self.browseServer.insert(0, (item['Name']), (item['Domain']))
#						print item['Name'], (item['Domain'])
#
#				if "2" in protonVPNTier:
#					if str((item['Tier'])) == "1" or str((item['Tier'])) == "2" or str((item['Tier'])) == "3":
#						self.browseServer.insert(0, (item['Name']), (item['Domain']))
#						print item['Name'], (item['Domain'])

		# Set item one in browseServer as active
		self.browseServer.set_active(0)

	# Populate browseServer with standard servers
	def standardRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnStandard.get_active() == True:
			self.radioBtnSelection(radioSelected="0")

	# Populate browseServer with Secure Core servers
	def secureCoreRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnSecureCore.get_active() == True:
			self.radioBtnSelection(radioSelected="1")

	# Populate browseServer with Tor servers
	def torRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnTor.get_active() == True:
			self.radioBtnSelection(radioSelected="2")

	# Populate browseServer with P2P servers
	def p2pRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnP2P.get_active() == True:
			self.radioBtnSelection(radioSelected="4")

	# Connect to selected server
	def connectBtn(self, button):
		self.reconnect()
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "-c", str(self.browseServer.get_active_id()), str(self.protocolSelection.get_active_id())])
		#t1 = Thread(target=self.connectionTimeout)
		#t1.start()

	def disconnectFunc(self):
		global disconnectThread
		GObject.idle_add(self.statusLabel.set_text, str("Disconnecting..."))
		p = subprocess.Popen(['protonvpn-cli', '-d'], stdout=subprocess.PIPE, shell=False)
		time.sleep(5)
		p.kill()
		self.connectionProgress.stop()
		self.connectionStatus()
		self.disconnectThread.should_abort_immediately = True

	# Disconnect from VPN
	def disconnectBtn(self, button):
		self.connectionProgress.start()
		global disconnectThread
		self.disconnectThread = Thread(target=self.disconnectFunc)
		self.disconnectThread.daemon = True
		self.disconnectThread.start()

	# Update protonvpn-cli
	def updateBtn(self, button):
		subprocess.Popen(["protonvpn-cli", "--update"])

	# Connect to fastest server
	def fastestServerBtn(self, button):
		self.reconnect()
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "-f"])

	# Connect to random server
	def randomServerBtn(self, button):
		self.reconnect()
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "-r"])

	# Allows connection to a server when a connection is already established
	def reconnect(self):
		if(self.statusLabel.get_text() == "Connected"):
			self.disconnectBtn(self)
			subprocess.check_call(["protonvpn-cli", "-d"])

	# Kill thread on Gtk destory
	def killThread(self):
		self.thread.should_abort_immediately = True

# Runs when windows closed
def destroy(destroy):
	Handler().killThread()
	Gtk.main_quit()

# Connect glade GUI
builder = Gtk.Builder()
builder.add_from_file("proton-ui.glade")
builder.connect_signals(Handler())

# Draw window
GObject.threads_init()
window = builder.get_object("ui")
window.show_all()
window.connect("destroy", destroy)

Gtk.main()