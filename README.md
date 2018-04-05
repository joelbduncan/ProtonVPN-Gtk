# ProtonVPN-Gtk
GTK3 ProtonVPN Client using offical ProtonVPN-CLi

# Features
- Connect to Server
- Connect to Fastest Server
- Connect to Random Server
- Update protonvpn-cli
- Live status of IP Address, Location & Connection Status
- Servers listed based on ProtonVPN tier unavailable servers won't be listed

**Please remember this is a work in progress in very early stages of development.**

![alt text](https://i.imgur.com/vrPhI6J.png "ProtonVPN-GTK Screenshot")

# Dependencies
- python
- python-requests
- python-json
- python-schedule
- GNOME 3.20
- protonvpn-cli

# Run Application
1. Install protonvpn-cli
```
$ sudo bash -c "git clone https://github.com/ProtonVPN/protonvpn-cli.git ; ./protonvpn-cli/protonvpn-cli.sh --install"
$ protonvpn-cli --init
```

More detailed instructions
[protonvpn-cli Github](https://github.com/ProtonVPN/protonvpn-cli)

2. Clone repository
`git clone https://github.com/Slethen/ProtonVPN-Gtk.git`

3. Run application with sudo
`sudo python ProtonVPN.py`

# Current Issues
- No installable package would like to use Flatpak
- ~~TCP/UDP Selection missing~~
- ~~Server List incomplete~~
- ~~Server list not filtered for free/paid users~~

# Report Bugs
I'm sure there's plenty of bugs please feel free to report them here.
Or even better have a go at fixing one!

# Contribute
Conbributions more then welcome!
