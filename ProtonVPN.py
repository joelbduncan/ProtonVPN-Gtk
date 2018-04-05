import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk
import subprocess
from threading import Thread
import socket
import time
from ConfigParser import SafeConfigParser
from serverList import serverList
import os
import sys

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

		# Server selection radio Button group
		self.radioBtnStandard = builder.get_object('radioBtnStandard')
		self.radioBtnSecureCore = builder.get_object('radioBtnSecureCore')
		self.radioBtnTor = builder.get_object('radioBtnTor')
		self.radioBtnP2P = builder.get_object('radioBtnP2P')

		builder.connect_signals(self)

		global protonVPNTier

		# Open/Read/Close ProtonVPN Tier config file
		with open(os.environ['HOME'] + '/.protonvpn-cli/protonvpn_tier','r') as f:
			protonVPNTier = f.read()

		# Populate Server list
		self.radioBtnSelection(radioSelected=1)

		# Populate potocol selection
		self.protocolSelection.insert(0, "tcp", "TCP")
		self.protocolSelection.insert(0, "udp", "UDP")

		# Read Config file
		parser = SafeConfigParser()
		parser.read('config.ini')

		# Set last connected server as default
		self.browseServer.set_active_id(parser.get('globalVars', 'lastConnection'))
		self.protocolSelection.set_active_id(parser.get('globalVars', 'protocol'))

		# Setup scheduler
		schedule.every(0.03).minutes.do(self.connectionStatus)

		# Start thread for scheduler
		self.thread = Thread(target=self.scheduleThread)
		self.thread.daemon = True
		self.thread.start()

	# Run scheduler in thread
	def scheduleThread(self):
		while True:
			schedule.run_pending()
			time.sleep(1)

	# Check VPN connection status & upadte location infomation
	def connectionStatus(self):
		try:
			# Update IP Address/Location
			self.fetchIP()

			# Get VPN Connection status
			host = socket.gethostbyname(remoteServer)
			s = socket.create_connection((host, 53), 2)

			# Update statusLabel on Gtk window
			GObject.idle_add(self.statusLabel.set_text, str("Connected"))
			self.connectionProgress.stop()
		except:
			pass
			GObject.idle_add(self.statusLabel.set_text, str("Disconnected"))

	# Get current IP address/Location
	def fetchIP(self):
		send_url = 'http://freegeoip.net/json'
		r = requests.get(send_url)
		j = json.loads(r.text)
		countryName = j['country_name']
		ipAddress = j['ip']

		# Update Location & IP Address labels on Gtk window
		GObject.idle_add(self.locationLabel.set_text, str(countryName))
		GObject.idle_add(self.ipAddressLabel.set_text, str(ipAddress))

	# Populate browserServer based on Toggle switch selected
	def radioBtnSelection(self, radioSelected):
		global protonVPNTier
		self.browseServer.remove_all()
		for index in range(len(serverList)-1, 0, -1):
			if str(radioSelected) in serverList[index][0]:

				# Free users protonTier = 1
				if "0" in protonVPNTier:
					if serverList[index][1] == "1":
						self.browseServer.insert(0, serverList[index][2], serverList[index][3])

				# Basic users protonTier = 2
				if "1" in protonVPNTier:
					if serverList[index][1] == "1" or serverList[index][1] == "2":
						self.browseServer.insert(0, serverList[index][2], serverList[index][3])

				# Plus & Visionary users protonTier = 3
				if "2" in protonVPNTier or "3" in protonVPNTier:
					if serverList[index][1] == "1" or serverList[index][1] == "2" or serverList[index][1] == "3":
						self.browseServer.insert(0, serverList[index][2], serverList[index][3])

		# Set item one in browseServer as active
		self.browseServer.set_active(0)

	# Populate browseServer with standard servers
	def standardRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnStandard.get_active() == True:
			self.radioBtnSelection(radioSelected=1)

	# Populate browseServer with Secure Core servers
	def secureCoreRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnSecureCore.get_active() == True:
			self.radioBtnSelection(radioSelected=2)

	# Populate browseServer with Tor servers
	def torRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnTor.get_active() == True:
			self.radioBtnSelection(radioSelected=3)

	# Populate browseServer with P2P servers
	def p2pRadioBtnToggle(self, widget):
		global protonVPNTier
		if self.radioBtnP2P.get_active() == True:
			self.radioBtnSelection(radioSelected=4)

	# Connect to selected server
	def connectBtn(self, button):
		self.reconnect()
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "-c", str(self.browseServer.get_active_id()), str(self.protocolSelection.get_active_id())])
		parser = SafeConfigParser()
		parser.read('config.ini')
		parser.set('globalVars', 'lastConnection', self.browseServer.get_active_id())
		parser.set('globalVars', 'protocol', self.protocolSelection.get_active_id())

		# Read config file
		with open('config.ini', 'w') as configfile:
			parser.write(configfile)

	# Disconnect from VPN
	def disconnectBtn(self, button):
		subprocess.Popen(["protonvpn-cli", "-d"])
		print('Done...')

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
			subprocess.check_call(["protonvpn-cli", "-d"])

	# Kill thread on Gtk destory
	def killThread(self):
		self.thread.join(0.1)

# Runs when windows closed
def destroy(destroy):
	Handler().killThread()
	Gtk.main_quit()

# Connect glade GUI
builder = Gtk.Builder()
builder.add_from_file("proton-ui.glade")
builder.connect_signals(Handler())

# Draw window
window = builder.get_object("ui")
window.show_all()
window.connect("destroy", destroy)

Gtk.main()