#!/usr/bin/env python3
import argparse, datetime, io, json, os, sys, time

'''
Program to convert records from the database to tests that can be run against DNS servers
and clinets. These files can be used by a lab server as its base for responses to a DUT client, or
by a lab client as a set of requests to be sent to a DUT server or resolver. This is part of
the dns-test-server system.

The program takes two possible argments; see the --help for more info
'''

LSName = os.path.expanduser("~/lsrecords.conf")
MasterfileName = os.path.expanduser("~/masterfilerecords.conf")
NegativeName = os.path.expanduser("~/negativemasterfilerecords.conf")
TDUTStrings = ("None", "Client", "Server", "Masterfile", "Caching", "Proxy", "Recursive", "SecResolv", "Any",
	"StubResolv", "Validator",  "Signer", "SecStub")

# Get the command-line options
DescText = '''
This command reads the conformance database, searching for tests of particular
types and dumping three files: commands for the lab system (LS), commands in
masterfile format for testing servers, and commands in masterfile format that
should not work in an authoritative server.

The --teststring argument is required. That value needs to be the concatenation
of the values for the tdut column in the database.
Those values that can be combined are:

{}

For example: --teststring=ServerMasterfileRecursive
'''.format(" ".join(TDUTStrings))
CmdParse = argparse.ArgumentParser(usage=DescText)
CmdParse.add_argument("--teststring", dest="TestString", help="The DUT types to be searched", default="")
Opts = CmdParse.parse_args()
if Opts.TestString == "":
	exit(DescText)

# Determine the tests that were specified for finding in the database
TestsToFind = []
for ThisString in TDUTStrings:
	if ThisString in Opts.TestString:
		TestsToFind.append(ThisString)
		Opts.TestString = Opts.TestString.replace(ThisString, "")
if (len(TestsToFind) == 0):
	exit("The value of the --teststring option was '{}'\n".format(Opts.TestString) \
		+ "That value needs to be the concatenation of the values for the tdut column in the database.\n" \
		+ "Those values that can be combined are:\n" + " ".join(TDUTStrings) + "\nFor example: --teststring=ServerMasterfileRecursive")
if (len(Opts.TestString) > 0):
	BadTestMsg = "The value of the --teststring option had an unknown string '{}'\n".format(Opts.TestString) \
		+ "That value needs to be the concatenation of the values for the tdut column.\n" \
		+ "Those values that can be combined are:\n" + " ".join(TDUTStrings) + "\nFor example: --teststring=ServerMasterfileRecursive"
	exit(BadTestMsg)
print("Extracting for tests: {}".format(" ".join(TestsToFind)))

# Return a JSON object of the whole database
from conformdb import Conformdb
def ReturnDBReport():
	db = Conformdb("")
	FullReportReturn = db.fulldatabase(where="prompt")
	return(FullReportReturn[1])

# Get all the "LS command" and "Master file entry" lines from the database
print("Starting database dump.")
try:
	TheDBJSON = ReturnDBReport()
except:
	exit("The MySQL database could not be accessed; Exiting.")
TheDB = json.loads(TheDBJSON)
if not(TheDB.get("basedoc")):
	exit("The report came back without the right JSON:\n{}\nExiting.".format(str(TheDB)))
# Holders for the found records
FoundLS = {}
FoundMasterfile = {}
FoundNegativeMasterfile = {}
for ThisBaseDoc in TheDB["basedoc"]:
	for ThisReq in TheDB["requirement"]:
		if ThisBaseDoc["bdseqno"] == ThisReq["bdseqno"]:
			for ThisTest in TheDB["tests"]:
				if ThisReq["rseqno"] == ThisTest["rseqno"]:
					# Check that the bdrfcno existsn, and see if it is > 0
					if ThisBaseDoc["bdrfcno"] and ThisBaseDoc["bdrfcno"] > 0:
						DocNum = "RFC " + str(ThisBaseDoc["bdrfcno"])
					else:
						DocNum = "Doc " + str(ThisBaseDoc["bdseqno"])
					# Is it one of the types of tests we want?
					if ThisTest["tdut"] in TestsToFind:
						# Does it have a LS command or masterfile content?
						if (ThisTest["tlscommand"] or ThisTest["tmasterfile"]):
							ThisKey = (DocNum, str(ThisReq["rseqno"]), str(ThisTest["tseqno"]))
							# Get the LS commands
							if ThisTest["tlscommand"]:
								# If the test starts with a "^", strip that and add a comment saying it is for IPv6
								if (ThisTest["tlscommand"]).startswith("^"):
									ThisKey = (DocNum, str(ThisReq["rseqno"]), str(ThisTest["tseqno"]) + "   Note that this test is run over IPv6")
									ThisTest["tlscommand"] = ThisTest["tlscommand"][1:]
								FoundLS[ThisKey] = ThisTest["tlscommand"]
							# Get the positive Masterfile records
							if ThisTest["tneg"] == "None":
								if ThisTest["tmasterfile"]:
									FoundMasterfile[ThisKey] = ThisTest["tmasterfile"]
							else: # Get the negative tests
								if ThisTest["tmasterfile"]:
									FoundNegativeMasterfile[ThisKey] = ThisTest["tmasterfile"]

FileHeader = ";; File created from request with '{}' at {}\n".format(" ".join(TestsToFind), time.strftime("%Y-%m-%d-%H-%M-%S"))

try:
	LSFile = open(LSName, mode="w")
except:
	exit("Could not open '{}' for writing. Exiting.".format(LSName))
LSFile.write(FileHeader)
for ThisKey in sorted(FoundLS):
	LSFile.write("\n;; {}, Requirement {}, Test {}\n".format(ThisKey[0], ThisKey[1], ThisKey[2]))
	LSFile.write(FoundLS[ThisKey] + "\n")
LSFile.close()

try:
	MasterfileFile = open(MasterfileName, mode="w")
except:
	exit("Could not open '{}' for writing. Exiting.".format(MasterfileName))
MasterfileFile.write(FileHeader)
MasterfileFile.write("$TTL 60\n")
for ThisKey in sorted(FoundMasterfile):
	MasterfileFile.write("\n;; {}, Requirement {}, Test {}\n".format(ThisKey[0], ThisKey[1], ThisKey[2]))
	MasterfileFile.write(FoundMasterfile[ThisKey] + "\n")
MasterfileFile.close()

try:
	NegativeMasterfileFile = open(NegativeName, mode="w")
except:
	exit("Could not open '{}' for writing. Exiting.".format(NegativeName))
NegativeMasterfileFile.write(FileHeader)
for ThisKey in sorted(FoundNegativeMasterfile):
	NegativeMasterfileFile.write("\n;; {}, Requirement {}, Test {}\n".format(ThisKey[0], ThisKey[1], ThisKey[2]))
	NegativeMasterfileFile.write(FoundNegativeMasterfile[ThisKey] + "\n")
NegativeMasterfileFile.close()

print("Finished database dump successfully.")
exit()
