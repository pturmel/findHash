#! /usr/bin/python2
# -*- coding: utf-8 -*-
#
# Locate 4k fragments of a subject file in one or more other files or
# devices.  Only reports two or more consecutive matches.
#
# Copyright (C) 2016, Philip J. Turmel <philip@turmel.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS 
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON 
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY 
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.

import hashlib, sys, datetime

# Read the known file 4k at a time, building a dictionary of
# md5 hashes vs. offset.  Use a large buffer for speed.
# Drops any partial block at the end of the file.
d = {}
pos = long(0)
f = open(sys.argv[1], 'r', 1<<20)
b = f.read(4096)
while len(b)==4096:
	md5 = hashlib.md5()
	md5.update(b)
	h = md5.digest()
	hlist = d.get(h)
	if not hlist:
		hlist = []
		d[h] = hlist
	hlist.append(pos)
	pos += 4096
	b = f.read(4096)
f.close()

print "%d Unique hashes in %s" % (len(d), sys.argv[1])

def checkAndPrint(match):
	if match[2]>4096:
		print "%20s @ %12.12x:%12.12x ~= %8.8x:%8.8x" % (fname, match[1], match[1]+match[2]-1, match[0], match[0]+match[2]-1)

# Read the candidate files/devices, looking for possible matches.  Match
# entries are vectors of known file offset, candidate file offset, and
# length.
for fname in sys.argv[2:]:
	print "\nSearching for pieces of %s in %s:..." % (sys.argv[1], fname)
	pos = long(0)
	f = open(fname, 'r', 1<<24)
	matches = []
	b = f.read(4096)
	lastts = None
	while len(b)==4096:
		if not (pos & 0x7ffffff):
			ts = datetime.datetime.now()
			if lastts:
				print "@ %12.12x %.1fMB/s   \r" % (pos, 128.0/((ts-lastts).total_seconds())),
			else:
				print "@ %12.12x...\r" % pos,
			sys.stdout.flush()
			lastts = ts
		md5 = hashlib.md5()
		md5.update(b)
		h = md5.digest()
		if h in d:
			i = 0
			while i<len(matches):
				match = matches[i]
				target = match[0]+match[2]
				continuations = [x for x in d[h] if x==target]
				if continuations:
					match[2] += 4096
					i += 1
				else:
					del matches[i]
					checkAndPrint(match)
			if not matches:
				matches = [[x, pos, 4096] for x in d[h]]
		else:
			for match in matches:
				checkAndPrint(match)
			matches = []
		pos += 4096
		b = f.read(4096)
	print "End of %s at %12.12x" % (fname, pos)
	# show matches that continue to the end of the candidate file/device.
	for match in matches:
		checkAndPrint(match)

# kate: tab-width 4; indent-width 4; tab-indents on; dynamic-word-wrap off; indent-mode python; line-numbers on;
