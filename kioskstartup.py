#!/usr/bin/env python

import feedparser
import os
import ping, socket
import time
import subprocess
import httplib


def checkConnection(ip):
    success = False
    proc = subprocess.Popen('ping -c 1 ' + ip, shell=True, stdout=subprocess.PIPE)
    proc.wait()
    
    lines = proc.stdout.readlines()
    for line in lines:
        if (line.find("packets received") != -1) and (line.find("0 packets received") == -1):
            success = True
    
    return success


def feedExists(host, feedpath):
    connection = httplib.HTTPConnection(host)
    connection.request('HEAD', feedpath)
    response = connection.getresponse()
    connection.close()
    return response.status == 200



done = False
connectionFound = False
repeatCount = 0

while not done:
    # Check the internet connection by pinging google, and making sure we get a response
    # If there is no response, we'll wait 30 seconds and try again. We'll do this a few times to give wireless a chance to set things up.
    print "Checking internet connection..."
    connectionFound = checkConnection('www.google.com')
    
    if connectionFound:
        print "Kiosk is connected to the internet."
        done = True
    else:
        if repeatCount > 0 and repeatCount < 3:
            print "Connection Problem: Still no internet connection detected. Trying again in 30 seconds..."
        elif repeatCount == 3:
            print "Connection Problem: Still no internet connection detected. Exiting."
        else:
            print "Connection Problem: This machine is either not connceted to the internet, or not registered with the network. Check to make sure it is connected to the internet, or registered with the network. This script will attempt to re-launch in 30 seconds..."
        repeatCount = repeatCount + 1
    
    if done:
        break
    else:
        time.sleep(30)

# Exit if there was no internet connection.
if not connectionFound:
    sys.exit()



# Check the possible hosts serving up our feed. We will use the first one available.
print "Checking rss feed..."

# To add a new feed host, simply add the hostname to the list below.
feedHosts = []
feedHosts.append('foss.rit.edu')
feedHosts.append('cs.rit.edu')

# Add the feed location to the respective map entry. Every hostname requires a feed location.
# Note: Values should start with a / because the host and path will concatenate later.
feedMap = {}
feedMap['foss.rit.edu'] = '/files/bookmarks.rss'
feedMap['cs.rit.edu'] = '/~ear7631/feed.rss'

connectionFound = False
acceptedHost = ''

for feedHost in feedHosts:
    connectionFound = checkConnection(feedHost)
    if connectionFound:
        print 'The host ' + feedHost + ' seems to be up. Attempting to access feed...'
        acceptedHost = feedHost
        break
    else:
        print 'The host ' + feedHost + ' seems to be down. Trying next possible host...'

if not connectionFound:
    print "No more candidate feed hosts. Exiting."
    sys.exit()



# A feed host has been found. Now let's try to grab and parse the feed
connectionFound = feedExists(acceptedHost, feedMap[acceptedHost])


"""
The live bookmark rss feed does things a little differently in formatting. Here's the algorithm:
Get the feed
Get all the subitems in the feed

For each item in the subitems
    Get a list of item links
    For each link in the list of links
        Add the link to our URL list (href property)
"""

pullLocation = 'http://' + acceptedHost + feedMap[acceptedHost]
print "Pulling feed from " + pullLocation + "..."

applecmd = []
applecmd.append("osascript")
applecmd.append("kioskcycle.scpt")
feedCapsule = feedparser.parse(pullLocation)
bookmarkitems = feedCapsule['items']
for item in bookmarkitems:
	for link in item.links:
		applecmd.append(link.href)


print applecmd
os.chdir("/Users/fossrit/Desktop")
subprocess.call(applecmd)
