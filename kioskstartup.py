#!/usr/bin/env python

from ConfigParser import SafeConfigParser
import feedparser
import os
import ping, socket
import time
import subprocess
import httplib
import sys


def check_connection(ip):
    success = False
    proc = subprocess.Popen('ping -c 1 ' + ip, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    
    lines = proc.stdout.readlines()
    for line in lines:
        if (line.find("packets received") != -1) and (line.find("0 packets received") == -1):
            success = True
    
    return success


def feed_exists(host, feedpath):
    connection = httplib.HTTPConnection(host)
    connection.request('HEAD', feedpath)
    response = connection.getresponse()
    connection.close()
    return response.status == 200


# get our variables from a configuration file    
parser = SafeConfigParser()
parser.read('kiosk_config')
file_location = parser.get('kiosk_cycler', 'file_location')
ping_host = parser.get('kiosk_cycler', 'ping_host')
ping_counter = int(parser.get('kiosk_cycler', 'ping_counter'))
ping_timer = int(parser.get('kiosk_cycler', 'ping_timer'))
feed_hosts_dirty = parser.get('kiosk_cycler', 'feed_hosts')


done = False
connection_found = False
repeat_count = 0

while not done:
    # Check the internet connection by pinging google, and making sure we get a response
    # If there is no response, we'll wait 30 seconds and try again. We'll do this a few times to give wireless a chance to set things up.
    print "Checking internet connection..."
    connection_found = check_connection('www.google.com')
    
    if connection_found:
        print "Kiosk is connected to the internet."
        done = True
    else:
        if repeat_count > 0 and repeat_count < ping_counter:
            print "Connection Problem: Still no internet connection detected. Trying again in 30 seconds..."
        elif repeat_count == 3:
            print "Connection Problem: Still no internet connection detected. Exiting."
        else:
            print "Connection Problem: This machine is either not connceted to the internet, or not registered with the network. Check to make sure it is connected to the internet, or registered with the network. This script will attempt to re-launch in 30 seconds..."
        repeat_count = repeat_count + 1
    
    if done:
        break
    else:
        time.sleep(ping_timer)

# Exit if there was no internet connection.
if not connection_found:
    sys.exit()



# Check the possible hosts serving up our feed. We will use the first one available.
print "Checking rss feed..."


# Create our list of hosts and map of feed locations.
feedhosts = []
feedmap = {}
hostpairs = feed_hosts_dirty.split(',')

# Add the feed location to the respective map entry. Every hostname requires a feed location.
# Note: Values should start with a / because the host and path will concatenate
for line in hostpairs:
    line = line.strip()
    pair = line.split(':')
    if(len(pair) != 2):
        continue
    
    pair[0] = pair[0].strip()
    pair[1] = pair[1].strip()
    feedhosts.append(pair[0])
    feedmap[pair[0]] = pair[1]

if len(feedhosts) == 0:
    print "No given hosts for feeds. Check the configuration file."
    sys.exit()


# Check our connections quickly...
connection_found = False
accepted_host = ''

for feedhost in feedhosts:
    connection_found = check_connection(feedhost)
    if connection_found:
        print 'The host ' + feedhost + ' seems to be up. Attempting to access feed...'
        accepted_host = feedhost
        break
    else:
        print 'The host ' + feedhost + ' seems to be down. Trying next possible host...'

if not connection_found:
    print "No more candidate feed hosts. Exiting."
    sys.exit()



# A feed host has been found. Now let's try to grab and parse the feed.
connection_found = feed_exists(accepted_host, feedmap[accepted_host])


"""
The live bookmark rss feed does things a little differently in formatting. Here's the algorithm:
Get the feed
Get all the subitems in the feed

For each item in the subitems
    Get a list of item links
    For each link in the list of links
        Add the link to our URL list (href property)
"""

pull_location = 'http://' + accepted_host + feedmap[accepted_host]
print "Pulling feed from " + pull_location + "..."

applecmd = []
applecmd.append("osascript")
applecmd.append("kioskcycle.scpt")
feed_capsule = feedparser.parse(pull_location)
bookmark_items = feed_capsule['items']
for item in bookmark_items:
	for link in item.links:
		applecmd.append(link.href)


print "Locating and launching applescript..."
try:
    os.chdir(file_location)
    subprocess.call(applecmd)
except OSError:
    print "Error when moving to " + file_location + " and running the script. Check the file_location field in the configuration file, and make sure Opera 10.0 or higher is installed."
    sys.exit()