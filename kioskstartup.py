#!/usr/bin/env python

import feedparser
import os
from subprocess import call

"""
The live bookmark rss feed does things a little differently in formatting
Get the feed
Get all the subitems in the feed

For each item in the subitems
    Get a list of item links
    For each link in the list of links
        Add the link to our URL list (href property)

Launch Safari
Open a new window
While we're still willing to loop
    For each URL in our URL list
        Set the current URL to the next item in our list
        Sleep for some time
"""

applecmd = []
applecmd.append("osascript")
applecmd.append("kioskcycle.scpt")
d = feedparser.parse("http://cs.rit.edu/~ear7631/feed.rss")
bookmarkitems = d['items']
for item in bookmarkitems:
	for link in item.links:
		applecmd.append(link.href)


os.chdir("/Users/fossrit/Desktop")
call(applecmd)
