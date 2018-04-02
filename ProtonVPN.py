import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gtk
import subprocess
from threading import Thread
import socket
import time
import requests
import json
from ConfigParser import SafeConfigParser
from serverList import serverList
import os
import sys
import schedule

# OpenVPN Gateway IP Address for connection status
remoteServer = "10.8.8.1"

# Checks for root execution
if not os.geteuid() == 0:
    sys.exit("Root access is required to use ProtonVPN-Gtk...")

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

		# Open/Read/Close ProtonVPN Tier config file
		with open(os.environ['HOME'] + '/.protonvpn-cli/protonvpn_tier','r') as f:
			protonVPNTier = f.read()

		# Populate Server list
		for index in range(len(serverList)-1, 0, -1):
			# Free users protonTier = 1
			if "1" in protonVPNTier:
				if serverList[index][0] == "1":
					self.browseServer.insert(0, serverList[index][1], serverList[index][2])

			# Basic users protonTier = 2
			if "2" in protonVPNTier:
				if serverList[index][0] == "1" or serverList[index][0] == "2":
					self.browseServer.insert(0, serverList[index][1], serverList[index][2])

			# Plus & Visionary users protonTier = 3
			if "3" in protonVPNTier or "4" in protonVPNTier:
				if serverList[index][0] == "1" or serverList[index][0] == "2" or serverList[index][0] == "3":
					self.browseServer.insert(0, serverList[index][1], serverList[index][2])

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

	# Connect to selected server
	def connectBtn(self, button):
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
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "-f"])

	# Connect to random server
	def randomServerBtn(self, button):
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "-r"])

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