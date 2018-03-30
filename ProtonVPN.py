import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk
import subprocess
from threading import Thread
import socket
import time
import requests
import json
from ConfigParser import SafeConfigParser
from serverList import serverList
import os

# Temp import for testing
import thread

# OpenVPN Gateway IP Address for connection status
remoteServer = "10.8.8.1"

# Setup GUI Handlers
class Handler():

	def __init__(self):
		# Connect GUI components
		self.usernameInput = builder.get_object('usernameInput')
		self.passwordInput = builder.get_object('passwordInput')
		self.browseServer = builder.get_object('browseServer')
		self.protocolSelection = builder.get_object('protocolSelection')
		self.statusLabel = builder.get_object('statusLabel')
		self.locationLabel = builder.get_object('locationLabel')
		self.ipAddressLabel = builder.get_object('ipAddressLabel')
		self.connectionProgress = builder.get_object('connectionProgress')

		# Populate Server list
		for index in range(len(serverList)):
			self.browseServer.insert(0, serverList[index][0], serverList[index][1])

		self.protocolSelection.insert(0, "tcp", "TCP")
		self.protocolSelection.insert(0, "udp", "UDP")

		# On Startup
		# Read Config file
		parser = SafeConfigParser()
		parser.read('config.ini')

		# Set last connected server as default
		self.browseServer.set_active_id(parser.get('globalVars', 'lastConnection'))
		self.protocolSelection.set_active_id(parser.get('globalVars', 'protocol'))

		# Start threading timeout for connectionStatus()
		GObject.timeout_add_seconds(1, self.statusThread)

	def statusThread(self):
		thread = Thread(target=self.connectionStatus)
		thread.start()
		return True

	# Check VPN connection status & upadte location infomation
	def connectionStatus(self):

		try:
			# Update IP Address/Location
			self.fetchIP()

			# Get VPN Connection status
			host = socket.gethostbyname(remoteServer)
			s = socket.create_connection((host, 53), 2)
			GObject.idle_add(self.statusLabel.set_text, str("Connected"))
			self.connectionProgress.stop()
		except:
			pass
			GObject.idle_add(self.statusLabel.set_text, str("Disconnected"))
			#self.connectionProgress.stop()

	# Get current IP address/Location
	def fetchIP(self):
		send_url = 'http://freegeoip.net/json'
		r = requests.get(send_url)
		j = json.loads(r.text)
		countryName = j['country_name']
		ipAddress = j['ip']
		
		self.locationLabel.set_text(countryName)
		self.ipAddressLabel.set_text(ipAddress)

	# Connect to selected server
	def connectBtn(self, button):
		self.connectionProgress.start()
		subprocess.Popen(["protonvpn-cli", "--connect", str(self.browseServer.get_active_id()), str(self.protocolSelection.get_active_id())])
		parser = SafeConfigParser()
		parser.read('config.ini')
		parser.set('globalVars', 'lastConnection', self.browseServer.get_active_id())
		parser.set('globalVars', 'protocol', self.protocolSelection.get_active_id())


		with open('config.ini', 'w') as configfile:    # save
		    parser.write(configfile)

	# Disconnect from VPN
	def disconnectBtn(self, button):
		subprocess.Popen(["protonvpn-cli", "--disconnect"])
		print 'Done...'

	def fastestServerBtn(self, button):
		subprocess.Popen(["protonvpn-cli", "--fastest-connect"])

	def randomServerBtn(self, button):
		subprocess.Popen(["protonvpn-cli", "--random-connect"])

# Connect glade GUI
builder = Gtk.Builder()
builder.add_from_file("proton-ui.glade")
builder.connect_signals(Handler())

# Draw window
window = builder.get_object("ui")
window.show_all()
window.connect("delete-event", Gtk.main_quit)

Gtk.main()