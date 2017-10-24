#!/usr/bin/env python3
import re, sys

'''
Small script to prepare a file for converting RFC text files into
HTML files used in the test harness.
The command takes one argument, one or more files to be processed.
'''

TagRE = re.compile(r'<\S+>')

if len(sys.argv) <= 1:
	exit("Need to specify one or more files to process on the command line.")
TheFiles = sys.argv[1:]

DontNeedProcessing = [ "rfc3363.html" ]

for ThisFile in TheFiles:
	# Get all the text
	InF = open(ThisFile, mode="r")
	InText = InF.read()
	InF.close()
	OutText = InText
	# Strip off any existing <pre>...</pre>; they will be added again later
	if OutText.startswith("<pre>\n"):
		OutText = OutText[6:]
	if OutText.endswith("</pre>\n"):
		OutText = OutText[:-7]
	if len(TagRE.findall(OutText)) > 0:
		if not (ThisFile in DontNeedProcessing):
			print("Not processing %s" % ThisFile)
			print("\n".join(TagRE.findall(OutText)))
	else:
		# De-escape everything first
		OutText = OutText.replace("&amp;", "&")
		OutText = OutText.replace("&lt;", "<")
		OutText = OutText.replace("&gt;", ">")
		# Then escape, maybe again
		OutText = OutText.replace("&", "&amp;")
		OutText = OutText.replace("<", "&lt;")
		OutText = OutText.replace(">", "&gt;")
		# Then write it out, overwriting the input file
		OutF = open(ThisFile, mode="w")
		OutF.write("<pre>\n" + OutText + "</pre>\n")
		OutF.close()
