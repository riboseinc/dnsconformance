#!/usr/bin/env python3
import json, operator, os, os.path, pprint, time
from bottle import BaseRequest, request, get, post, static_file, HTTPError
from conformdb import Conformdb

##### Log stuff, mostly for debugging

def LogThis(InStr):
	LogFileName = "/tmp/Common-log.txt"
	if not(os.path.exists(LogFileName)):
		try:
			CreateF = open(LogFileName, mode="w")
			CreateF.close()
		except:
			return("Failed to create log file %s." % LogFileName)
		try:
			os.chmod(LogFileName, 0o0666)
		except:
			return("Failed to chmod 0666 on log file %s." % LogFileName)
	try:
		LogF = open(LogFileName, mode="a")
	except:
		return("Was not able to append to %s." % LogFileName)
	if isinstance(InStr, str):
		LogF.write("%s %s\n" % (time.strftime("%Y-%m-%d-%H-%M-%S"), InStr))
	else:
		LogF.write("%s %s\n" % (time.strftime("%Y-%m-%d-%H-%M-%S"), str(InStr)))
	LogF.close()
	return()

# Fix Bottle's memory size limitation
BaseRequest.MEMFILE_MAX = 10000000

##### Client GET and POST queires going to the server

# Allow GET on /
@get("/")
def GetSlash():
	return static_file("index.htm", root=".")

# Files and directories visible on the top level
ListOfTopLevelFilesThatWeCanServe = ( "index.htm", "document.htm", "favicon.ico" )
ListOfTopLevelSubDirectoriesThatWeCanServe = ( "css", "js", "fonts", "graphics" )

@get("/<TopDirFilename>")
def GetFileFromTopLevel(TopDirFilename):
	if TopDirFilename in ListOfTopLevelFilesThatWeCanServe:
		return static_file(TopDirFilename, root=".")
	else:
		return HTTPError(403, "You are not allowed to access '%s'." % TopDirFilename)

@get("/<InSubDir>/<InFilename>")
def ReturnStatic(InSubDir, InFilename):
	TheRequestedFile = InSubDir + "/" + InFilename
	if InSubDir not in ListOfTopLevelSubDirectoriesThatWeCanServe:
		return HTTPError(404, "The file '%s' does not exist." % TheRequestedFile)
	if os.path.exists(TheRequestedFile):
		return static_file(InFilename, root=InSubDir)
	else:
		return HTTPError(404, "The file '%s' does not exist." % TheRequestedFile)

# Handle POSTs
@post("/")
def DoPost():
	# Make sure that Bottle can find the JSON
	try:
		RequestDict = request.json
	except:
		return HTTPError(400, "There appears to be no JSON in that POST request")
	# Get the HTTP user name
	if request.environ.get('REMOTE_USER') == None:
		return("There was no REMOTE_USER in the POST request.")
	RequestDict["HTTP user"] = request.environ.get('REMOTE_USER')
	# Send it off to the server, get a dict back in return
	ResponseDict = ProcessPOST(RequestDict)
	return(json.dumps(ResponseDict))

##### Utility functions

def IntegerConvert(InThing, CanBeNone=False):
	# Returns the integer if the thing can be coerced to an integer and fits as a Unsigned, or a None if the input is a None or ""
	# Raises an exception with an error message otherwise
	if CanBeNone and ((InThing == None) or (InThing == "")):
		return(None)
	try:
		OutThing = int(InThing)
	except:
		if InThing == "":
			raise Exception(" could not be made an integer; it was an empty string")
		elif InThing == None:
			raise Exception(" could not be made an integer; it was 'None'")
		else:
			raise Exception(" could not be made an integer; it was '%s'" % (str(InThing)))
	if OutThing < 0:
		raise Exception(" was a negative integer, which is not allowed")
	if OutThing >= 2**32 - 1:
		raise Exception(" had a value that was too large")
	return(OutThing)

EnumValues = {
	"bddoctype": ("None", "RFC", "TestPlan", "RRtypeTemplate", "Other"),
	"bdthstat": ("None", "Testable"),
	"bddstat": ("None", "Active", "Removed", "Replaced"),
	"rtype": ("None", "Testable", "Format", "Operational", "HighVol", "LongPeriod",
		"FutureSpec", "Procedural", "Historic", "API", "AppsAndPeople"),
	"tdut": ("None", "Client", "Server", "Masterfile", "Caching", "Proxy", "Recursive",
		"SecResolv", "Any", "StubResolv", "Validator", "Signer", "SecStub"),
	"tneg": ("None", "Negative")
}

def EnumConvert(FieldName, Value):
	# Returns the value if it is valid, returns "None" if the value is None
	# Raises an exception with an error message otherwise
	if Value == None:
		return("None")
	if FieldName in EnumValues:
		if Value in EnumValues[FieldName]:
			return(Value)
		else:
			raise Exception("%s is not a valid value for %s" % (Value, FieldName))
	else:
		raise Exception("%s is not a known enumerated field" % FieldName)

def CreateTestPlanFromData(OrderedData, PlanTitle="", HideErrata=True):
	# Requires an array of basedocs dumped from the database
	# Returns an HTML string
	# HideErrata says whether or not to hide the errata
	if type(OrderedData) != list:
		raise Exception("The input to CreateTestPlanFromData was not an array.")
	# We're assuming here that OrderedData has all the right fields in it; if not, exceptions will happen naturally
	OutHTML = ""  # Holder for all the HTML in the test plan
	OutTableOfContents = ""  # Holder for the table of contents entries; it will already be in the right order
	ReqTableLines = {}  # Holder for the lines in the list of requirements
	TestTableLines = {}  # Holder for the lines in the list of tests
	NoneCounter = 0  # Used for references to non-RFCs
	for ThisBasedoc in OrderedData:
		ThisBdrfcno = ThisBasedoc['bdrfcno']
		if ThisBdrfcno == None:
			ThisBdrfcno = "NonRFC_{}".format(NoneCounter)
			NoneCounter += 1
		BasedocString = "<div class='basedoc' id='RFC-{}'><span class='bdname'>{}</span>\n".format(ThisBdrfcno, ThisBasedoc['bdname'])
		BasedocString += "<span class='bdrfcno'>{}</span>\n".format(ThisBdrfcno)
		BasedocString += "<span class='bdthstat'>{}</span>\n".format(ThisBasedoc['bdthstat'])
		BasedocString += "<span class='bddstat'>{}</span>\n".format(ThisBasedoc['bddstat'])
		if ThisBasedoc['bdcomment']:
			BasedocString += "<span class='bdcomment'>Comment: {}</span>\n".format(ThisBasedoc['bdcomment'])
		if not(HideErrata):
			if ThisBasedoc['bderrata']:
				BasedocString += "<span class='bderrata'>Errata: {}</span>\n".format(ThisBasedoc['bderrata'])
			if ThisBasedoc['bdediff']:
				BasedocString += "<span class='bdediff'>{}</span>\n".format(ThisBasedoc['bdediff'])
		if len(ThisBasedoc["All requirements"]) == 0:
			RequirementListString = "<div class='requirementlist'>No requirements</div>\n"
		else:
			RequirementListString = "<div class='requirementlist'>\n"
			for ThisRequirment in ThisBasedoc["All requirements"]:
				RequirementString = "<div class='requirement REQ-{}' id='req{}'>\n".format(ThisRequirment["rtype"], ThisRequirment["rseqno"])
				RequirementString += "<span class='rtext'>{}</span>\n".format(ThisRequirment["rtext"])
				RequirementString += "<span class='dontwrap'><span class='rtype'>{}</span>\n".format(ThisRequirment["rtype"])
				RequirementString += "<span class='rseqno'>{}</span></span>\n".format(ThisRequirment["rseqno"])
				if ThisRequirment["rcomment"]:
					RequirementString += "<div class='rcomment'>Comment: {}</div>\n".format(ThisRequirment["rcomment"])
				if ThisRequirment["rsameas"]:
					RequirementString += "<div class='rsameas'>Same as <a href='#req{}'>requirement {}</a></div>\n".format(ThisRequirment["rsameas"], ThisRequirment["rsameas"])
				if len(ThisRequirment["All tests"]) > 0:
					TestListString = "<div class='testlist'>\n"
					for ThisTest in ThisRequirment["All tests"]:
						TestString = "<div class='test DUT{}' id='test{}'>\n".format(ThisTest["tdut"], ThisTest["tseqno"])
						TestString += "<span class='tdut'>Target: {}</span>&nbsp;&nbsp;\n".format(ThisTest["tdut"])
						TestString += "<span class='tseqno'>{}</span>\n".format(ThisTest["tseqno"])
						TestString += "<span class='ttext'>{}</span>\n".format(ThisTest["ttext"])
						if ThisTest["toutcome"]:
							TestString += "<span class='toutcome'>Outcome: {}</span>\n".format(ThisTest["toutcome"])
						NegIndicator = ""
						if ThisTest["tneg"]:
							if ThisTest["tneg"] != "None":
								NegIndicator = "<span class='tneg'> (negative test)</span>"
						if ThisTest["tlscommand"]:
							TestString += "<span class='tlscommand'>LS setting{}: </span><span class='likepre'>{}</span>\n".format(NegIndicator, ThisTest["tlscommand"])
						if ThisTest["tmasterfile"]:
							TestString += "<span class='tmasterfile'>Master file{}: </span><span class='likepre'>{}</span>\n".format(NegIndicator, ThisTest["tmasterfile"])
						if ThisTest["tcomment"]:
							TestString += "<span class='tcomment'>Comment: {}</span>\n".format(ThisTest["tcomment"])
						if ThisTest["tsameas"]:
							TestString += "<span class='tsameas'>Same as <a href='#test{}'>test {}</a></span>\n".format(ThisTest["tsameas"], ThisTest["tsameas"])
						TestString += "</div>\n"
						TestListString += TestString
						TestTableLines[int(ThisTest['tseqno'])] = "<tr class='test_table_item'><td><a href='#test{}'>{}</a></td><td>{}</td></tr>\n".format(ThisTest['tseqno'], ThisTest['tseqno'], ThisTest['ttext'])
					TestListString += "</div>\n"
					RequirementString += TestListString
				RequirementString += "</div>\n"
				RequirementListString +=  RequirementString
				ReqTableLines[int(ThisRequirment['rseqno'])] = "<tr class='req_table_item'><td><a href='#req{}'>{}</a></td><td>{}</td></tr>\n".format(ThisRequirment['rseqno'], ThisRequirment['rseqno'], ThisRequirment['rtext'])
			RequirementListString += "</div>\n"
			BasedocString +=  RequirementListString
		BasedocString += "</div>\n\n"
		OutHTML += BasedocString
		OutTableOfContents += "<tr class='toc_item'><td><a href='#RFC-{}'>{}</td><td>&nbsp;</td><td>{}</a></td></tr>\n".format(ThisBdrfcno, ThisBdrfcno, ThisBasedoc['bdname'])
	# Put together the requirement and test tables
	OutReqTable = ""
	OutTestTable = ""
	for ThisItem in sorted(ReqTableLines):
		OutReqTable += ReqTableLines[ThisItem]
	for ThisItem in sorted(TestTableLines):
		OutTestTable += TestTableLines[ThisItem]
		
	TheCSS = '''
h1 { font-size: 18pt; font-family: Helvetica; }
h2 { font-size: 16pt; font-family: Helvetica; font-weight: lighter; }
.basedoc { margin-top: 20pt; font-family: Helvetica; font-weight: lighter; }
.bdname { font-weight: bold; font-size: 14pt; border-style: none none solid none; border-width: medium; }
.bderrata, .bdediff, .bdcomment { display: block; margin-left: .25in; padding-top: 3pt; }
.bdrfcno, .bdtext, .bdthstat, .bddstat { display: none; }
.requirementlist { margin-left: .25in; margin-top: 3pt; }
.requirement { border-style: none none solid none; border-width: thin; border-color: #404040; padding-top: 3pt; }
.rtext, .ttext { font-size: 12pt; }
.rtype, .rseqno, .tseqno { color: #909090; font-size: 10pt; }
.rtype:after { content: ", "; }
.rcomment, .rsameas { display: block; margin-left: .25in; }
.testlist { margin-left: .25in; margin-top: 3pt; margin-bottom: 3pt; }
.tneg { color: #ff0000 }
.ttext, .toutcome, .tlscommand, .tmasterfile, .tcomment, .tsameas { display: block; margin-left: .25in; }
.dontwrap { white-space: nowrap; }
.likepre { display: block; margin-left: .5in; font-family: monospace; white-space: pre; }
.filterOptions { display: none; border: 1px solid #dedede; padding: 10px; background-color: #efefef; font-family: Helvetica; font-weight: lighter; }
.toc_item, .req_table_item, .test_table_item { vertical-align: top; text-decoration: none; color: black; font-family: Helvetica; font-weight: lighter; }
.toc_item a, .req_table_item a, .test_table_item a { text-decoration: none; color: slateblue; font-family: Helvetica; font-weight: lighter; }
table { border-collapse: collapse; }
tr:nth-child(even) {background: #f0f0f0 }
tr:nth-child(odd) {background: white}
'''

	BeginningStuff = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html><head><title>{0}</title>
<meta http-equiv="Content-type" content="text/html;charset=UTF-8"> 
<style type="text/css">
<!--{1}-->
</style>
</head><body>
<h1>{2}</h1>

'''.format(PlanTitle, TheCSS, PlanTitle)

	ShowOptions = '''<button class="filterToggle">Show Display Options</button>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<button class="TableOfContentsToggle">Show Table of Contents</button>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<button class="ReqTableToggle">Show List of Requirements</button>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<button class="TestTableToggle">Show List of Tests</button>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<div class="filterOptions" style="display: none; border: 1px solid #dedede; padding: 10px; background-color: #efefef;">
Show only tests for DUTs of type:&nbsp;&nbsp;
<select class="form-control input-sm s_tdut">
    <option value="All" selected>All</option>
    <option value="DUTClient">Client</option>
    <option value="DUTServer">Server</option>
    <option value="DUTMasterfile">Master file</option>
    <option value="DUTCaching">Caching server</option>
    <option value="DUTProxy">Proxy server</option>
    <option value="DUTRecursive">Recursive resolver</option>
    <option value="DUTStubResolv">Stub resolver</option>
    <option value="DUTSecResolv">Security-aware resolver</option>
    <option value="DUTSecStub">Security-aware stub</option>
    <option value="DUTValidator">DNSSEC validating software</option>
    <option value="DUTSigner">DNSSEC signing software</option>
</select>
<button class="dut_highlight">Show</button>
<hr>
List of RFC numbers to show, such as "1034 1035 2181"; leave blank to show all<br>
<input type=text size=60 class="form-control input-sm rfc_list_text" value="">
<button class="rfc_show">Show</button>
</div>
<div class="TableOfContents" style="display: none; border: 1px solid #dedede; padding: 10px;">
<h2>Table of Contents</h2>
<table>
{}
</table>
</div>
<div class="ReqTable" style="display: none; border: 1px solid #dedede; padding: 10px;">
<h2>List of Requirements</h2>
<table>
{}
</table>
</div>
<div class="TestTable" style="display: none; border: 1px solid #dedede; padding: 10px;">
<h2>List of Tests</h2>
<table>
{}
</table>
</div>
'''.format(OutTableOfContents, OutReqTable, OutTestTable)

	EndingStuff = '''<br><script src="https://code.jquery.com/jquery-1.4.4.min.js"></script>
<script>
$(function() {
	// toggle filters
	$(".filterToggle").click(function() {
        if ($(".filterOptions").is(":visible")) {
            $(this).text("Show Display Options");
        } else {
            $(this).text("Hide Display Options");
        }
		$(".filterOptions").slideToggle("fast");
	});
	// handle filtering on dut_highlight click
	$(".dut_highlight").click(function() {
		dutVal = $(".s_tdut").val();
		if (dutVal === "All") {
			$(".test").show();
		} else {
			$(".test").hide();
			$("." + dutVal).show();
		};
	});
	// handle filtering on rfc_show click
	$(".rfc_show").click(function() {
		RFCListText = $(".rfc_list_text").val();
		if (RFCListText === "") {
			$(".basedoc").show();
		} else {
			$(".basedoc").hide();
			var ListOfRFCs = RFCListText.split(" ");
			for (var i in ListOfRFCs) {
				$(".RFC-" + ListOfRFCs[i]).show();
			};
		};
	});
	// toggle Table of Contents
	$(".TableOfContentsToggle").click(function() {
        if ($(".TableOfContents").is(":visible")) {
            $(this).text("Show Table of Contents");
        } else {
            $(this).text("Hide Table of Contents");
        }
		$(".TableOfContents").slideToggle("fast");
	});
	// toggle Requirements table
	$(".ReqTableToggle").click(function() {
        if ($(".ReqTable").is(":visible")) {
            $(this).text("Show List of Requirements");
        } else {
            $(this).text("Hide List of Requirements");
        }
		$(".ReqTable").slideToggle("fast");
	});
	// toggle Tests table
	$(".TestTableToggle").click(function() {
        if ($(".TestTable").is(":visible")) {
            $(this).text("Show List of Tests");
        } else {
            $(this).text("Hide List of Tests");
        }
		$(".TestTable").slideToggle("fast");
	});
});
</script>
</body></html>
'''

	OutHTML = BeginningStuff + ShowOptions + OutHTML + EndingStuff
	return(OutHTML)

##### Functions for communicating with the web UI

def GetUserAccessLevel(InDict):
	# Returns the user's access level
	# C: { "Command": "Get user access level" }
	# S: { "Command": "Get user access level", "Access": s_userauth, "Return": returnval }
	#    s_userauth = "markup" or "view"
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	(UserInfoRet, ThisUser) = db.getuserinfo()
	if not UserInfoRet:
		OutDict["ActionReturn"] = "The call to 'getuserinfo' failed for user '%s'." % ThisUser
		return(OutDict)
	ThisPriv = ThisUser['userpriv']
	if ThisPriv and "Edit" in ThisPriv:
		OutDict["Access"] = "markup"
		OutDict["ActionReturn"] = "good"
	else:
		OutDict["Access"] = "view"
		OutDict["ActionReturn"] = "good"
	return(OutDict)

def GetDocumentTextAndRanges(InDict):
	# Called after a document is selected in the <- Docs list
	# C: { "Command": "Get document text and ranges", "Document ID": bdseqno }
	# S: { "Command": "Get document text and ranges", "Document ID": s_bdseqno, "Name": s_bdname,
	#      "Ranges": { reqrange, reqrange, ... }, "Text": s_bdtext, "Return": returnval }
	#           reqrange = rseqno: [ s_rstart, s_rlength ]
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InDocID = OutDict.get("Document ID")
	try:
		InDocID = IntegerConvert(InDocID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to GetDocumentTextAndRanges had a 'Document ID' field that %s" % (e)
		return(OutDict)
	GetBaseDocReturn = db.getbasedoc(seqno=InDocID)
	if GetBaseDocReturn[0]:
		TheDoc = GetBaseDocReturn[1]
		if "bdname" in TheDoc:
			OutDict["Name"] = TheDoc["bdname"]
			# Keep track of all the ranges
			RangeDict = {}
			AssociatedReqs = db.listrequirement(seqno=TheDoc["bdseqno"])
			for ThisReq in AssociatedReqs[1]:
				RangeDict[ThisReq["rseqno"]] = [ ThisReq["rstart"], ThisReq["rlength"] ]
			OutDict["Ranges"] = RangeDict
			OutDict["Text"] = TheDoc["bdtext"]
			OutDict["ActionReturn"] = "good"
		else:
			OutDict["ActionReturn"] = "The call to getbasedoc in GetDocumentTextAndRanges did not return a 'bdname'."
	else:
		OutDict["ActionReturn"] = "The call to getbasedoc in GetDocumentTextAndRanges failed with error '%s'." % GetBaseDocReturn[1]
	return(OutDict)

def GetJSONDatabase(InDict):
	# C: { "Command": "Get JSON database" }
	# S: { "Command": "Get JSON database", "Database JSON": s_data, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	FullDatabaseReturn = db.fulldatabase(where="prompt")
	if FullDatabaseReturn[0]:
		OutDict["ActionReturn"] = "good"
		OutDict["Database JSON"] = FullDatabaseReturn[1]
	else:
		OutDict["ActionReturn"] = "The call to fulldatabase returned failure: %s" % FullDatabaseReturn[1]
	return(OutDict)

def GetMySQLDatabase(InDict):
	# C: { "Command": "Get MySQL database" }
	# S: { "Command": "Get MySQL database", "Database text": s_data, "Return": returnval }
	#  Note that this is no longer in use, but might come back later
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	(stat, dbtext) = db.dumpdb()
	if stat:
	    OutDict["ActionReturn"] = "good"
	    OutDict["Database text"] = dbtext
	else:
	    OutDict["ActionReturn"] = dbtext
	return(OutDict)

def GetListOfDocuments(InDict):
	# C: { "Command": "Get list of documents" }
	# S: { "Command": "Get list of documents", "Documents": { idname, idname, ... }, "Return": returnval }
	#         idname = s_bdseqno: Dict of values
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	ListBaseDocReturn = db.listbasedoc()
	if ListBaseDocReturn[0]:
		OutDocs = {}
		for ThisDoc in ListBaseDocReturn[1]:
			ThisUpdated = (ThisDoc["bdupdated"]).utctimetuple()
			Months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
			TimeFmt = "%%d %s %%Y %%H:%%M:%%S" % (Months[int(time.strftime("%m", ThisUpdated)) - 1])
			# Get the number of requirements
			TheReqs = db.listrequirement(seqno=ThisDoc["bdseqno"])
			if TheReqs[0]:
				TotalReqs = len(TheReqs[1])
				TestableReqs = 0
				TotalTests = 0
				for ThisReq in TheReqs[1]:
					if ThisReq["rtype"] == "Testable":
						TestableReqs += 1
					TheTests = db.listtest(rseqno=ThisReq["rseqno"])
					if TheTests[0]:
						TotalTests += len(TheTests[1])
					else:
						OutDict["ActionReturn"] = "The call to listtest on {0} in GetListOfDocuments failed with the message '{1}'".format(ThisDoc["bdseqno"], TheTests[1])
						return(OutDict)
			else:
				OutDict["ActionReturn"] = "The call to listrequirement on {0} in GetListOfDocuments failed with the message '{1}'".format(ThisDoc["bdseqno"], TheReqs[1])
				return(OutDict)
			OutDocs[ThisDoc["bdseqno"]] = {
				"DocName": ThisDoc["bdname"],
				"DateAsTimestamp": time.mktime(ThisUpdated),
				"DateAsText": time.strftime(TimeFmt, ThisUpdated),
				"Status": ThisDoc["bddstat"],
				"SeqNo": ThisDoc["bdseqno"],
				"TotalReqs": TotalReqs,
				"TestableReqs": TestableReqs,
				"TotalTests": TotalTests }
		OutDict["Documents"] = OutDocs
		LogThis(pprint.pformat(OutDocs))
		OutDict["ActionReturn"] = "good"
	else:
		OutDict["ActionReturn"] = "The call to listbasedoc returned failure: %s" % ListBaseDocReturn[1]
	return(OutDict)

def GetGeneralTestPlan(InDict, PlanStyle=""):
	# C: { "Command": "Get full test plan" }
	# S: { "Command": "Get full test plan", "Test plan HTML": s_html, "Return": returnval }
	# PlanStyle says what kind of test plan to produce
	#    full = Everything
	#    testable = Only testable requirements
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	FullDatabaseReturn = db.fulldatabase(where="prompt")
	if FullDatabaseReturn[0]:
		JSONReturned = FullDatabaseReturn[1]
	else:
		OutDict["ActionReturn"] = "The call to fulldatabase returned failure: %s" % FullDatabaseReturn[1]
		return(OutDict)
	try:
		AllData = json.loads(JSONReturned)
	except:
		OutDict["ActionReturn"] = "Could not read the JSON: {0}".format(JSONReturned)
		return(OutDict)
	# Make sure the JSON returned has the right set of keys at the top level
	DataKeys = set(AllData.keys())
	TheTops = set(('basedoc', 'tests', 'requirement'))
	if (DataKeys & TheTops) != TheTops:
		OutDict["ActionReturn"] = "The JSON appears to not be a conformance dataset; the top level keys are {0}. Exiting.".format(pprint.pformat(DataKeys))
		return(OutDict)
	# OrderedData is the list of all data
	OrderedData = []
	for ThisBasedoc in sorted(AllData["basedoc"], key=operator.itemgetter("bdname")):
		# If we only want testable records, check if there are any in the document
		if PlanStyle == "testable":
			if ThisBasedoc["bdthstat"] != "Testable":
				continue
		# Get the list of requirements for this doc
		FoundRequirements = []
		for ThisRequirement in sorted(AllData["requirement"], key=operator.itemgetter("rstart")):
			# If we only want testable records, check if this requirement is testable
			if PlanStyle == "testable":
				if ThisRequirement["rtype"] != "Testable":
					continue
			# Get the list of tests for this requirement
			FoundTests = []
			if ThisRequirement["bdseqno"] == ThisBasedoc["bdseqno"]:
				for ThisTest in sorted(AllData["tests"], key=operator.itemgetter("tdut")):
					if ThisTest["rseqno"] == ThisRequirement["rseqno"]:
						FoundTests.append(ThisTest)
				ThisRequirement["All tests"] = FoundTests
				FoundRequirements.append(ThisRequirement)
		ThisBasedoc["All requirements"] = FoundRequirements
		OrderedData.append(ThisBasedoc)
	# Done collecting data; set the report name
	if PlanStyle == "full":
		PlanTitle = "Full Conformance Test Plan"
	elif PlanStyle == "testable":
		PlanTitle = "Conformance Test Plan, Testable Requirements Only"
	else:
		OutDict["ActionReturn"] = "Got an invalid value for PlanStyle in GetTestPlan: {0}".format(PlanTitle)
		return(OutDict)
	# Convert the data into HTML
	OutHTML = CreateTestPlanFromData(OrderedData, PlanTitle)
	OutDict["ActionReturn"] = "good"
	OutDict["Test plan HTML"] = OutHTML
	return(OutDict)

def GetFullTestPlan(InDict):
	# C: { "Command": "Get test plan testable only" }
	# S: { "Command": "Get test plan testable only", "Test plan HTML": s_html, "Return": returnval }
	OutDict = GetGeneralTestPlan(InDict, PlanStyle="full")
	return(OutDict)

def GetTestPlanTestableOnly(InDict):
	# C: { "Command": "Get test plan testable only" }
	# S: { "Command": "Get test plan testable only", "Test plan HTML": s_html, "Return": returnval }
	OutDict = GetGeneralTestPlan(InDict, PlanStyle="testable")
	return(OutDict)

def DocumentDelete(InDict):
	# C: { "Command": "Document delete", "Document ID": c_bdseqno }
	# S: { "Command": "Document delete", "Document ID": s_bdeqno, "Return": returnval }
	# NOTE: there is no action for this command in the GUI
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InDocumentID = OutDict.get("Document ID")
	try:
		InDocumentID = IntegerConvert(InDocumentID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentDelete had a 'Document ID' field that %s" % (e)
		return(OutDict)
	DeleteRequestReturn = db.deletebasedoc(bdseqno=InDocumentID)
	if not DeleteRequestReturn[0]:
		OutDict["ActionReturn"] = "The call to deletebasedoc in DocumentDelete failed with the message '%s'" % DeleteRequestReturn[1]
	else:
		OutDict["ActionReturn"] = "good"
	return(OutDict)

def DocumentEdit(InDict):
	# C: { "Command": "Document edit", "Document ID": c_bdseqno, "Name": c_bdname, "Type": c_bddoctype, "RFC": c_bdrfcno,
	#      "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat, 
	#      "Comment": c_bdcomment, "Staus": c_bddstat }
	#    -- All fields are required
	# S: { "Command": "Document edit", "Document ID": s_bdseqno, "Name": c_bdname, "Type": c_bddoctype, "RFC": c_bdrfcno, 
	#      "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat,
	#      "Comment": c_bdcomment, "Staus": c_bddstat }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	for ThisRequiredField in ("Document ID", "Name", "Type", "RFC", "Text", "Errata notes", "Errata diff", \
			"Testable requirements", "Comment", "Status"):
		if not (ThisRequiredField in OutDict):
			OutDict["ActionReturn"] = "The call to DocumentEdit did not have a '%s' given." % ThisRequiredField
			return(OutDict)
	InDocID = OutDict["Document ID"]
	try:
		InDocID = IntegerConvert(InDocID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentEdit had a 'Document ID' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["RFC"] = IntegerConvert(OutDict["RFC"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentEdit had an 'RFC' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Type"] = EnumConvert("bddoctype", OutDict["Type"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentEdit had error %s" % (e)
		return(OutDict)
	try:
		OutDict["Testable requirements"] = EnumConvert("bdthstat", OutDict["Testable requirements"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentEdit had error %s" % (e)
		return(OutDict)
	try:
		OutDict["Status"] = EnumConvert("bddstat", OutDict["Status"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentEdit had error %s" % (e)
		return(OutDict)
	# Update the record
	UpdateDocReturn = db.updatebasedoc(seqno=InDocID, name=OutDict["Name"], doctype=OutDict["Type"], rfcno=OutDict["RFC"], \
		errata=OutDict["Errata notes"], ediff=OutDict["Errata diff"], thstat=OutDict["Testable requirements"],\
		comment=OutDict["Comment"], dstat=OutDict["Status"])
	if not UpdateDocReturn[0]:
		OutDict["ActionReturn"] = "The call to updatebasedoc failed with error '%s'." % UpdateDocReturn[1]
	else:
		FullDoc = db.getbasedoc(seqno=InDocID)
		if not FullDoc[0]:
			OutDict["ActionReturn"] = "The call to getbasedoc after updatebasedoc failed with error '%s'." % FullDoc[1]
		else:
			OutDict["ActionReturn"] = "good"
			OutDict["Name"] = FullDoc[1]["bdname"]
	return(OutDict)

def DocumentNew(InDict):
	# C: { "Command": "Document new", "Name": c_bdname, "Type: c_bddoctype, "RFC": c_bdrfcno, "Text": c_bdtext,
	#      "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat,
	#      "Comment": c_bdcomment, "Status": c_bddstat }
	#    -- "Name" and "Text" are required
	# S: { "Command": "Document new", "Document ID": s_bdseqno, "Name": c_bdname, "Type: c_bddoctype, "RFC": c_bdrfcno, 
	#      "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat,
	#      "Comment": c_bdcomment, "Status": c_bddstat }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	for ThisRequiredField in ("Name", "Text"):
		if not (ThisRequiredField in OutDict):
			OutDict["ActionReturn"] = "The call to DocumentNew did not have a '%s' given." % ThisRequiredField
			return(OutDict)
	try:
		OutDict["RFC"] = IntegerConvert(OutDict.get("RFC"), CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentNew had an 'RFC' field that %s" % (e)
		return(OutDict)
	if OutDict.get("Type") != None:
		try:
			OutDict["Type"] = EnumConvert("bddoctype", OutDict["Type"])
		except Exception as e:
			OutDict["ActionReturn"] = "The call to DocumentNew had error %s" % (e)
			return(OutDict)
	if OutDict.get("Testable requirements") != None:
		try:
			OutDict["Testable requirements"] = EnumConvert("bdthstat", OutDict["Testable requirements"])
		except Exception as e:
			OutDict["ActionReturn"] = "The call to DocumentNew had error %s" % (e)
			return(OutDict)
	if OutDict.get("Status") != None:
		try:
			OutDict["Status"] = EnumConvert("bddstat", OutDict["Status"])
		except Exception as e:
			OutDict["ActionReturn"] = "The call to DocumentNew had error %s" % (e)
			return(OutDict)
	# Set default values for items not in the dict
	OutDict.setdefault("Type", None)
	OutDict.setdefault("RFC", None)
	OutDict.setdefault("Errata notes", None)
	OutDict.setdefault("Errata diff", None)
	OutDict.setdefault("Testable requirements", None)
	OutDict.setdefault("Comment", None)
	OutDict.setdefault("Status", None)
	# Put it
	PutDocumentReturn = db.putbasedoc(seqno=None,name=OutDict["Name"], doctype=OutDict["Type"], rfcno=OutDict["RFC"], \
		text=OutDict["Text"], errata=OutDict["Errata notes"], ediff=OutDict["Errata diff"], thstat=OutDict["Testable requirements"],\
		comment=OutDict["Comment"], dstat=OutDict["Status"])
	if not PutDocumentReturn[0]:
		OutDict["ActionReturn"] = "The call to putbasedoc in DocumentNew failed with error '%s'." % PutDocumentReturn[1]
	else:
		GetDocumentReturn = db.getbasedoc(seqno=PutDocumentReturn[1])
		if not GetDocumentReturn[0]:
			OutDict["ActionReturn"] = "The call to getbasedoc in DocumentNew failed with the message '%s'" % GetDocumentReturn[1]
		else:
			OutDict["ActionReturn"] = "good"
			OutDict["Document ID"] = GetDocumentReturn[1]["bdseqno"]
			OutDict["Name"] = GetDocumentReturn[1]["bdname"]
			OutDict["Type"] = GetDocumentReturn[1]["bddoctype"]
			OutDict["RFC"] = GetDocumentReturn[1]["bdrfcno"]
			OutDict["Text"] = GetDocumentReturn[1]["bdtext"]
			OutDict["Errata notes"] = GetDocumentReturn[1]["bderrata"]
			OutDict["Errata diff"] = GetDocumentReturn[1]["bdediff"]
			OutDict["Testable requirements"] = GetDocumentReturn[1]["bdthstat"]
			OutDict["Comment"] = GetDocumentReturn[1]["bdcomment"]
			OutDict["Status"] = GetDocumentReturn[1]["bddstat"]
			OutDict["This user"] = GetDocumentReturn[1]["bduser"]
			OutDict["Updated"] = GetDocumentReturn[1]["bdupdated"]
			OutDict["Added"] = GetDocumentReturn[1]["bdadded"]
	return(OutDict)

def DocumentView(InDict):
	# C: { "Command": "Document view", "Document ID": c_bdseqno }
	# S: { "Command": "Document view", "Document ID": s_bdseqno, "Name": s_bdname, "Type": s_bddoctype, "RFC": s_bdrfcno, 
	#      "Text": s_bdtext, "Errata notes": s_bderrata, "Errata diff": s_bdediff, "Testable requirements": s_bdthstat,
	#      "Comment": s_bdcomment, "Status": s_bddstat, "Last user": s_bduser, "Last updated": s_bdupdated,
	#			 "Summary report": s_bdreport, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InDocID = OutDict.get("Document ID")
	try:
		InDocID = IntegerConvert(InDocID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to DocumentView had a 'Document ID' field that %s" % (e)
		return(OutDict)
	GetDocumentReturn = db.getbasedoc(seqno=InDocID)
	if not GetDocumentReturn[0]:
		OutDict["ActionReturn"] = "The call to getbasedoc in DocumentView failed with the message '%s'" % GetDocumentReturn[1]
	else:
		OutDict["ActionReturn"] = "good"
		OutDict["Document ID"] = GetDocumentReturn[1]["bdseqno"]
		OutDict["Name"] = GetDocumentReturn[1]["bdname"]
		OutDict["Type"] = GetDocumentReturn[1]["bddoctype"]
		OutDict["RFC"] = GetDocumentReturn[1]["bdrfcno"]
		OutDict["Text"] = GetDocumentReturn[1]["bdtext"]
		OutDict["Errata notes"] = GetDocumentReturn[1]["bderrata"]
		OutDict["Errata diff"] = GetDocumentReturn[1]["bdediff"]
		OutDict["Testable requirements"] = GetDocumentReturn[1]["bdthstat"]
		OutDict["Comment"] = GetDocumentReturn[1]["bdcomment"]
		OutDict["Status"] = GetDocumentReturn[1]["bddstat"]
		OutDict["This user"] = GetDocumentReturn[1]["bduser"]
		OutDict["Updated"] = GetDocumentReturn[1]["bdupdated"]
		OutDict["Added"] = GetDocumentReturn[1]["bdadded"]
		# Report the number of requirement types
		SummaryReportDict = { Key: 0 for Key in EnumValues["rtype"] }
		SummaryReportText = ""
		TheReqs = db.listrequirement(seqno=OutDict["Document ID"])
		if TheReqs[0]:
			for ThisReq in TheReqs[1]:
				SummaryReportDict[ThisReq["rtype"]] += 1
			for ThisKey in sorted(SummaryReportDict):
				if SummaryReportDict[ThisKey] > 0:
					SummaryReportText += "{0}: {1}, ".format(ThisKey, SummaryReportDict[ThisKey])
			OutDict["Summary report"] = SummaryReportText[:-2]
		else:
			OutDict["ActionReturn"] = "The call to listrequirement in DocumentView failed with the message '%s'" % TheReqs[1]
	return(OutDict)

def RequirementDelete(InDict):
	# C: { "Command": "Requirement delete", "Requirement ID": c_rseqno }
	# S: { "Command": "Requirement delete", "Requirement ID": s_rseqno, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InRequirementID = OutDict.get("Requirement ID")
	try:
		InRequirementID = IntegerConvert(InRequirementID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementDelete had a 'Requirement ID' field that %s" % (e)
		return(OutDict)
	DeleteRequestReturn = db.deleterequirement(rseqno=InRequirementID)
	if not DeleteRequestReturn[0]:
		OutDict["ActionReturn"] = "The call to deleterequirement in RequirementDelete failed with the message '%s'" % DeleteRequestReturn[1]
	else:
		OutDict["ActionReturn"] = "good"
	return(OutDict)

def RequirementEdit(InDict):
	# C: { "Command": "Requirement edit", "Requirement ID": c_rseqno, "Base document": c_bdseqno, "Same as": c_rsameas,
	#       "Start": c_rstart, "Length": c_rlength, "Text": c_rtext, "Type": c_rtype, "Comment": c_rcomment,
	#       "Replaced by": c_rreplacedby }
	#    -- All fields are are required
	# S: { "Command": "Requirement edit", "Requirement ID": s_rseqno, "Base document": s_bdseqno, "Same as": s_rsameas,
	#       "Start": s_rstart, "Length": s_rlength, "Text": s_rtext, "Type": s_rtype, "Comment": s_rcomment,
	#      "Replaced by": s_rreplacedby, "This user": s_ruser, "Updated": s_rupdated, "Added": s_radded, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	for ThisRequiredField in ("Requirement ID", "Base document", "Start", "Length", "Text", "Type", "Comment", "Replaced by"):
		if not (ThisRequiredField in OutDict):
			OutDict["ActionReturn"] = "The call to RequirementEdit did not have a '%s' given." % ThisRequiredField
			return(OutDict)
	InRequirementID = OutDict["Requirement ID"]
	try:
		InRequirementID = IntegerConvert(InRequirementID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Requirement ID' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Base document"] = IntegerConvert(OutDict["Base document"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Base document' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Same as"] = IntegerConvert(OutDict["Same as"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Same as' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Start"] = IntegerConvert(OutDict["Start"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Start' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Length"] = IntegerConvert(OutDict["Length"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Length' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Replaced by"] = IntegerConvert(OutDict["Replaced by"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Replaced by' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Type"] = EnumConvert("rtype", OutDict["Type"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had error %s" % (e)
		return(OutDict)
	# Update the record
	UpdateRequirementReturn = db.updaterequirement(rseqno=InRequirementID, bdseqno=OutDict["Base document"], rsameas=OutDict["Same as"], \
	 rstart=OutDict["Start"], rlength=OutDict["Length"], rtext=OutDict["Text"], rtype=OutDict["Type"], rcomment=OutDict["Comment"], \
	 replacedby=OutDict["Replaced by"])
	if not UpdateRequirementReturn[0]:
		OutDict["ActionReturn"] = "The call to updaterequirement in RequirementEdit failed with error '%s'." % UpdateRequirementReturn[1]
	else:
		GetRequestReturn = db.getrequirement(seqno=InRequirementID)
		if not GetRequestReturn[0]:
			OutDict["ActionReturn"] = "The call to getrequirement in RequirementEdit failed with the message '%s'" % GetRequestReturn[1]
		else:
			ListTestReturn = db.listtest(rseqno=InRequirementID)
			if ListTestReturn[0]:
				OutDict["ActionReturn"] = "good"
				OutDict["Requirement"] = GetRequestReturn[1]["rseqno"]
				OutDict["Base document"] = GetRequestReturn[1]["bdseqno"]
				OutDict["Same as"] = GetRequestReturn[1]["rsameas"]
				OutDict["Start"] = GetRequestReturn[1]["rstart"]
				OutDict["Length"] = GetRequestReturn[1]["rlength"]
				OutDict["Text"] = GetRequestReturn[1]["rtext"]
				OutDict["Comment"] = GetRequestReturn[1]["rcomment"]
				OutDict["Replaced by"] = GetRequestReturn[1]["rreplacedby"]
				OutDict["This user"] = GetRequestReturn[1]["ruser"]
				OutDict["Updated"] = GetRequestReturn[1]["rupdated"]
				OutDict["Added"] = GetRequestReturn[1]["radded"]
				TestListForRequirement = []
				for ThisTest in ListTestReturn[1]:
					TestListForRequirement.append([ ThisTest["tseqno"], ThisTest["ttext"], ThisTest["tdut"] ])
				OutDict["Tests"] = TestListForRequirement
			else:
				OutDict["ActionReturn"] = "The call to listtest in RequirementView failed with the message '%s'" % ListTestReturn[1]
	return(OutDict)

def RequirementNew(InDict):
	# C: { "Command": "Requirement new", "Base document": c_bdseqno, "Same as": c_rsameas, "Start": c_rstart, "Length": c_rlength,
	#      "Text": c_rtext, "Type": c_rtype, "Comment": c_rcomment, "Replaced by": c_rreplacedby }
	#    -- "Base document", "Start", "Length", and "Text" are required
	# S: { "Command": "Requirement new", "Requirement ID": s_rseqno, "Base document": s_bdseqno, "Same as": s_rsameas,
	#      "Start": s_rstart, "Length": s_rlength, "Text": s_rtext, "Type": s_rtype, "Comment": s_rcomment,
	#      "Replaced by": s_rreplacedby, "This user": s_ruser, "Updated": s_rupdated, "Added": s_radded, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	for ThisRequiredField in ("Base document", "Start", "Length", "Text"):
		if not (ThisRequiredField in OutDict):
			OutDict["ActionReturn"] = "The call to RequirementNew did not have a '%s' given." % ThisRequiredField
			return(OutDict)
	try:
		OutDict["Base document"] = IntegerConvert(OutDict["Base document"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementNew had a 'Base document' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Same as"] = IntegerConvert(OutDict["Same as"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementEdit had a 'Same as' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Start"] = IntegerConvert(OutDict["Start"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementNew had a 'Start' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Length"] = IntegerConvert(OutDict["Length"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementNew had a 'Length' field that %s" % (e)
		return(OutDict)
	# Set default values for items not in the dict
	OutDict.setdefault("Type", "None")
	OutDict.setdefault("Comment", "")
	OutDict.setdefault("Replaced by", 0)
	# Put it
	PutRequestReturn = db.putrequirement(rseqno=None, bdseqno=OutDict["Base document"], rsameas=OutDict["Same as"], \
		rstart=OutDict["Start"], rlength=OutDict["Length"], rtext=OutDict["Text"], rtype=OutDict["Type"], rcomment=OutDict["Comment"], \
		replacedby=OutDict["Replaced by"])
	if not PutRequestReturn[0]:
		OutDict["ActionReturn"] = "The call to putrequirement in RequirementNew failed with error '%s'." % PutRequestReturn[1]
	else:
		GetRequestReturn = db.getrequirement(seqno=PutRequestReturn[1])
		if not GetRequestReturn[0]:
			OutDict["ActionReturn"] = "The call to getrequirement for '%s' in RequirementNew failed with error '%s'." \
				% (PutRequestReturn[1], GetRequestReturn[1])
		else:
			OutDict["ActionReturn"] = "good"
			OutDict["Requirement ID"] = GetRequestReturn[1]["rseqno"]
			OutDict["Base document"] = GetRequestReturn[1]["bdseqno"]
			OutDict["Same as"] = GetRequestReturn[1]["rsameas"]
			OutDict["Start"] = GetRequestReturn[1]["rstart"]
			OutDict["Length"] = GetRequestReturn[1]["rlength"]
			OutDict["Text"] = GetRequestReturn[1]["rtext"]
			OutDict["Type"] = GetRequestReturn[1]["rtype"]
			OutDict["Comment"] = GetRequestReturn[1]["rcomment"]
			OutDict["Replaced by"] = GetRequestReturn[1]["rreplacedby"]
			OutDict["This user"] = GetRequestReturn[1]["ruser"]
			OutDict["Updated"] = GetRequestReturn[1]["rupdated"]
			OutDict["Added"] = GetRequestReturn[1]["radded"]
	return(OutDict)

def RequirementView(InDict):
	# C: { "Command": "Requirement view", "Requirement ID": rseqno }
	# S: { "Command": "Requirement view", "Requirement ID": s_rseqno, "Base document": s_bdseqno, "Same as": s_rsameas,
	#      "Start": s_rstart, "Length": s_rlength, "Text": s_rtext, "Type": s_rtype, "Comment": s_rcomment,
	#      "Replaced by": s_rreplacedby, "This user": s_ruser, "Updated": s_rupdated, "Added": s_radded,
	#      "Tests": [ [testid, testtext], [testid, testtext], ... ], "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InRequirementID = OutDict.get("Requirement ID")
	try:
		InRequirementID = IntegerConvert(InRequirementID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to RequirementView had a 'Requirement ID' field that %s" % (e)
		return(OutDict)
	GetRequestReturn = db.getrequirement(seqno=InRequirementID)
	if not GetRequestReturn[0]:
		OutDict["ActionReturn"] = "The call to getrequirement in RequirementView failed with the message '%s'" % GetRequestReturn[1]
	else:
		OutDict["Requirement"] = GetRequestReturn[1]["rseqno"]
		OutDict["Base document"] = GetRequestReturn[1]["bdseqno"]
		OutDict["Same as"] = GetRequestReturn[1]["rsameas"]
		OutDict["Start"] = GetRequestReturn[1]["rstart"]
		OutDict["Length"] = GetRequestReturn[1]["rlength"]
		OutDict["Text"] = GetRequestReturn[1]["rtext"]
		OutDict["Type"] = GetRequestReturn[1]["rtype"]
		OutDict["Comment"] = GetRequestReturn[1]["rcomment"]
		OutDict["Replaced by"] = GetRequestReturn[1]["rreplacedby"]
		OutDict["This user"] = GetRequestReturn[1]["ruser"]
		OutDict["Updated"] = GetRequestReturn[1]["rupdated"]
		OutDict["Added"] = GetRequestReturn[1]["radded"]
		ListTestReturn = db.listtest(rseqno=InRequirementID)
		if ListTestReturn[0]:
			TestListForRequirement = []
			for ThisTest in ListTestReturn[1]:
				TestListForRequirement.append([
					ThisTest["tseqno"], 
					ThisTest["ttext"], 
					ThisTest["tdut"], 
					ThisTest["toutcome"], 
					ThisTest["tcomment"], 
					ThisTest["tmasterfile"], 
					ThisTest["tsameas"], 
					ThisTest["tlscommand"],
					ThisTest["tneg"]
				])
			OutDict["Tests"] = sorted(TestListForRequirement, key=operator.itemgetter(2))
			OutDict["ActionReturn"] = "good"
		else:
			OutDict["ActionReturn"] = "The call to listtest in RequirementView failed with the message '%s'" % ListTestReturn[1]
	return(OutDict)

def TestDelete(InDict):
	# C: { "Command": "Test delete", "Test ID": c_tseqno }
	# S: { "Command": "Test delete", "Test ID": s_tseqno, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InTestID = OutDict.get("Test ID")
	try:
		InTestID = IntegerConvert(InTestID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestDelete had a 'Test ID' field that %s" % (e)
		return(OutDict)
	DeleteRequestReturn = db.deletetests(tseqno=InTestID)
	if not DeleteRequestReturn[0]:
		OutDict["ActionReturn"] = "The call to deletetests in TestDelete failed with the message '%s'" % DeleteRequestReturn[1]
	else:
		OutDict["ActionReturn"] = "good"
	return(OutDict)

def TestEdit(InDict):
	# C: { "Command": "Test edit", "Test ID": c_tseqno, "Base requirement": c_rseqno, "Same as": c_tsameas,
	#      "Text": c_ttext, "DUT": c_tdut, "LS command": c_tlscommand, "Outcome": c_toutcome, "Neg": c_tneg, "Comment": c_tcomment, 
	#	     "Master file entry": c_tmasterfile, "Replaced by": c_treplacedby }
	#    -- All fields are are required
	# S: { "Command": "Test edit", "Test ID": s_tseqno, "Base requirement": s_rseqno, "Same as": s_tsameas,
	#      "Text": s_ttext, "DUT": s_tdut, "LS command": s_tlscommand, "Outcome": s_toutcome, "Neg": s_tneg, "Comment": s_tcomment,
	#      "Master file entry": c_smasterfile, "Replaced by": s_treplacedby, "This user": s_tuser, "Updated": s_tupdated,
	#      "Added": s_tadded, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	for ThisRequiredField in ("Test ID", "Base requirement", "Same as", "Text", "DUT", "Outcome", "Comment", "Replaced by"):
		if not (ThisRequiredField in OutDict):
			OutDict["ActionReturn"] = "The call to TestEdit did not have a '%s' given." % ThisRequiredField
			return(OutDict)
	InTestID = OutDict["Test ID"]
	try:
		InTestID = IntegerConvert(InTestID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Test ID' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Base requirement"] = IntegerConvert(OutDict["Base requirement"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Base requirement' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Same as"] = IntegerConvert(OutDict["Same as"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Same as' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Replaced by"] = IntegerConvert(OutDict["Replaced by"], CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Replaced by' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["DUT"] = EnumConvert("tdut", OutDict["DUT"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had error %s" % (e)
		return(OutDict)
	try:
		OutDict["Neg"] = EnumConvert("tneg", OutDict["Neg"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had error %s" % (e)
		return(OutDict)
	# Update the record
	UpdateTestReturn = db.updatetest(tseqno=InTestID, rseqno=OutDict["Base requirement"], tsameas=OutDict["Same as"],
		ttext=OutDict["Text"], tdut=OutDict["DUT"], tlscommand=OutDict["LS command"], toutcome=OutDict["Outcome"],
		tneg=OutDict["Neg"], tcomment=OutDict["Comment"], tmasterfile=OutDict["Master file entry"], replacedby=OutDict["Replaced by"])
	if not UpdateTestReturn[0]:
		OutDict["ActionReturn"] = "The call to updatetest failed with error '%s'." % UpdateTestReturn[1]
	else:
		FullDoc = db.gettest(seqno=InTestID)
		if not FullDoc[0]:
			OutDict["ActionReturn"] = "The call to gettest after updatetest failed with error '%s'." % FullDoc[1]
		else:
			OutDict["ActionReturn"] = "good"
			OutDict["Text"] = FullDoc[1]["ttext"]
	return(OutDict)

def TestNew(InDict):
	# C: { "Command": "Test new", "Base requirement": c_rseqno, "Same as": c_tsameas, "Text": c_ttext,
	#      "DUT": c_tdut, "LS command": c_tlscommand, "Outcome": c_toutcome, "Neg": c_tneg, "Comment": c_tcomment,"Master file entry": c_tmasterfile }
	#    -- "Base requirement" and "Text" are required
	# S: { "Command": "Test new", "Test": s_tseqno, "Base requirement": s_rseqno, "Same as": s_tsameas,
	#      "Text": s_ttext, "DUT": tdut, "LS command": s_tlscommand, "Outcome": s_toutcome, "Neg": s_tneg, "Comment": s_tcomment, 
	#      "Master file entry": s_tmasterfile, "Replaced by": s_treplacedby, "This user": s_tuser, "Updated": s_tupdated,
	#      "Added": s_tadded, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	for ThisRequiredField in ("Base requirement", "Text"):
		if not (ThisRequiredField in OutDict):
			OutDict["ActionReturn"] = "The call to TestNew did not have a '%s' given." % ThisRequiredField
			return(OutDict)
	try:
		OutDict["Base requirement"] = IntegerConvert(OutDict["Base requirement"])
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Base requirement' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Same as"] = IntegerConvert(OutDict.get("Same as"), CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Same as' field that %s" % (e)
		return(OutDict)
	try:
		OutDict["Replaced by"] = IntegerConvert(OutDict.get("Replaced by"), CanBeNone=True)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestEdit had a 'Replaced by' field that %s" % (e)
		return(OutDict)
	if OutDict.get("DUT") != None:
		try:
			OutDict["DUT"] = EnumConvert("tdut", OutDict["DUT"])
		except Exception as e:
			OutDict["ActionReturn"] = "The call to RequirementEdit had error %s" % (e)
			return(OutDict)
	# Set default values for items not in the dict
	OutDict.setdefault("Same as", 0)
	OutDict.setdefault("DUT", "None")
	OutDict.setdefault("Neg", "None")
	OutDict.setdefault("Outcome", "")
	OutDict.setdefault("Comment", "")
	OutDict.setdefault("Master file entry", "")
	# Put it
	PutTestReturn = db.puttest(tseqno=None, rseqno=OutDict["Base requirement"], tsameas=OutDict["Same as"], ttext=OutDict["Text"],
		tdut=OutDict["DUT"], tlscommand=OutDict["LS command"], toutcome=OutDict["Outcome"], tcomment=OutDict["Comment"],
		tmasterfile=OutDict["Master file entry"])
	if not PutTestReturn[0]:
		OutDict["ActionReturn"] = "The call to puttest in TestNew failed with error '%s'." % PutTestReturn[1]
	else:
		GetTestReturn = db.gettest(seqno=PutTestReturn[1])
		if not GetTestReturn[0]:
			OutDict["ActionReturn"] = "The call to gettest in TestNew failed with error '%s'." % GetTestReturn[1]
		else:
			OutDict["ActionReturn"] = "good"
			OutDict["Test ID"] = GetTestReturn[1]["tseqno"]
			OutDict["Base requirement"] = GetTestReturn[1]["rseqno"]
			OutDict["Same as"] = GetTestReturn[1]["tsameas"]
			OutDict["Text"] = GetTestReturn[1]["ttext"]
			OutDict["DUT"] = GetTestReturn[1]["tdut"]
			OutDict["LS command"] = GetTestReturn[1]["tlscommand"]
			OutDict["Outcome"] = GetTestReturn[1]["toutcome"]
			OutDict["Neg"] = GetTestReturn[1]["tneg"]
			OutDict["Comment"] = GetTestReturn[1]["tcomment"]
			OutDict["Master file entry"] = GetTestReturn[1]["tmasterfile"]
			OutDict["Replaced by"] = GetTestReturn[1]["treplacedby"]
			OutDict["This user"] = GetTestReturn[1]["tuser"]
			OutDict["Updated"] = GetTestReturn[1]["tupdated"]
			OutDict["Added"] = GetTestReturn[1]["tadded"]
	return(OutDict)

def TestView(InDict):
	# C: { "Command": "Test view", "Test ID": c_tseqno }
	# S: { "Command": "Test view", "Test ID": s_tseqno, "Base requirement": s_rseqno, "Same as": s_tsameas,
	#      "Text": s_ttext, "DUT": s_tdut, "LS command": c_tlscommand, "Outcome": s_toutcome, "Neg": s_tneg, "Comment": s_tcomment,
	#      "Master file entry": s_tmasterfile, "Replaced by": s_treplacedby, "This user": s_tuser,
	#      "Updated": s_tupdated, "Added": s_tadded, "Return": returnval }
	OutDict = InDict.copy()
	db = Conformdb(OutDict["HTTP user"])
	InTestID = OutDict.get("Test ID")
	try:
		InTestID = IntegerConvert(InTestID)
	except Exception as e:
		OutDict["ActionReturn"] = "The call to TestView had a 'Test ID' field that %s" % (e)
		return(OutDict)
	GetTestReturn = db.gettest(seqno=InTestID)
	if not GetTestReturn[0]:
		OutDict["ActionReturn"] = "The call to gettest failed with the message '%s'" % GetTestReturn[1]
	else:
		OutDict["ActionReturn"] = "good"
		OutDict["Test ID"] = GetTestReturn[1]["tseqno"]
		OutDict["Base requirement"] = GetTestReturn[1]["rseqno"]
		OutDict["Same as"] = GetTestReturn[1]["tsameas"]
		OutDict["Text"] = GetTestReturn[1]["ttext"]
		OutDict["DUT"] = GetTestReturn[1]["tdut"]
		OutDict["LS command"] = GetTestReturn[1]["tlscommand"]
		OutDict["Outcome"] = GetTestReturn[1]["toutcome"]
		OutDict["Neg"] = GetTestReturn[1]["tneg"]
		OutDict["Comment"] = GetTestReturn[1]["tcomment"]
		OutDict["Master file entry"] = GetTestReturn[1]["tmasterfile"]
		OutDict["Replaced by"] = GetTestReturn[1]["treplacedby"]
		OutDict["This user"] = GetTestReturn[1]["tuser"]
		OutDict["Updated"] = GetTestReturn[1]["tupdated"]
		OutDict["Added"] = GetTestReturn[1]["tadded"]
	return(OutDict)

ActionDict = {
	"Get document text and ranges": GetDocumentTextAndRanges,
	"Get list of documents": GetListOfDocuments,
	"Get JSON database": GetJSONDatabase,
	"Get MySQL database": GetMySQLDatabase,
	"Get full test plan": GetFullTestPlan,
	"Get test plan testable only": GetTestPlanTestableOnly,
	"Get user access level": GetUserAccessLevel,
	"Document delete": DocumentDelete,
	"Document edit": DocumentEdit,
	"Document new": DocumentNew,
	"Document view": DocumentView,
	"Requirement delete": RequirementDelete,
	"Requirement edit": RequirementEdit,
	"Requirement new": RequirementNew,
	"Requirement view": RequirementView,
	"Test delete": TestDelete,
	"Test edit": TestEdit,
	"Test new": TestNew, 
	"Test view": TestView,
}


# Finally, do it all
def ProcessPOST(DictFromRequest):
	# The return values are (True, "") or (False, message)
	# Be sure this got a dict
	if not isinstance(DictFromRequest, dict):
		return({ "Return": (False, "ProcessPOST got a non-dict: %s" % str(type(DictFromRequest))) })
	# Don't allow requests that already have "Return"
	if "Return" in DictFromRequest:
		return({ "Return": (False, "ProcessPOST got a dict that already had a 'Return'") })
	# Be sure the request has a "Command"
	if not ("Command" in DictFromRequest):
		return({ "Return": (False, "ProcessPOST got a dict that did not have a 'Command'") })
	# Be sure that this is an action we know
	if DictFromRequest["Command"] not in ActionDict:
		return({ "Return": (False, "ProcessPOST got a dict that had an unknown 'Command': %s" % DictFromRequest["Command"]) })
	# Log the messages
	LogFileName = "/tmp/Common-log.txt"
	if not(os.path.exists(LogFileName)):
		try:
			CreateF = open(LogFileName, mode="w")
			CreateF.close()
		except:
			return({ "Return": (False, "Failed to create log file %s." % LogFileName) })
		try:
			os.chmod(LogFileName, 0o0666)
		except:
			return({ "Return": (False, "Failed to chmod 0666 on log file %s." % LogFileName) })
	try:
		LogF = open(LogFileName, mode="a")
	except:
		return({ "Return": (False, "Was not able to append to %s." % LogFileName) })
	LogF.write("%s Request:  %s\n" % (time.strftime("%Y-%m-%d-%H-%M-%S"), pprint.pformat(DictFromRequest)))
	# OK, now do it
	DictForOutput = ActionDict[DictFromRequest["Command"]](DictFromRequest)
	LogThis("Request:  %s\n" % pprint.pformat(DictFromRequest))
	LogThis("Response: %s\n\n" % pprint.pformat(DictForOutput))
	# Make sure the action set a status
	if not ("ActionReturn" in DictForOutput):
		return({ "Return": (False, "There was no 'ActionReturn' for the command '%s'." % DictFromRequest["Command"]) })
	# If the return is not "good", send back a dict with only False and a message
	if DictForOutput["ActionReturn"] != "good":
		return({ "Return": (False, "The action for %s gave the error: %s." % (DictForOutput["Command"], DictForOutput["ActionReturn"])) })
	else:
		# Say that this was good and return
		DictForOutput["Return"] = (True, "")
		return(DictForOutput)

'''
                             Test description of actions in the web client

All commands from the web client are done as POST on /, sending JSON as a body, getting back JSON

On startup, the web client should check the user's access level (GetUserAccessLevel)
	Store that so that it doesn't have to keep asking

View/Markup button
	If user is authorized to go into markup mode
		Toggle the mode and store the result
	Else
		Modal dialog that says "Only users authorized to enter markup mode can take this action."

When the <- Docs button is clicked
	Show a new page with a scrolling list sorted by title (GetListOfDocuments)
		User clicks on a title
		Get that document's text and set of ranges (GetDocumentTextAndRanges)
	Switch back to the main page
		Change the left column to show the document's with ranges highlighted
		Scroll to the first requirement
		Change right column to be the first requirement and associated tests (if one exists)

After selecting text in the left column
	Show small dialog with "Make requirement" and "Cancel"
	If "Make requirement"
		If the user is not authorized to go into markup mode
			Modal dialog that says "Only users authorized to enter markup mode can take this action." with OK
			Remove the selection from the document
		If not in markup mode
			Modal dialog that says "Please enter markup mode and select some text before choosing this action."  with OK
			Remove the selection from the document
		Display requirement editing popup with fields filled in saved from the previous invocation (RequirementNew)
		If OK:
			If the return is False
				Show the error message in a modal dialog
			Else
				Use new selection color in left column for this new selection
				Change second column to show the new requirement
		If Cancel:
			Remove the selection from the document
	If Cancel:
		Remove the selection from the document

Clicking on an existing selection
	Determine the associated requirement from existing selection
	Change right column to be the selected requirement and associated tests

Metadata button in document header
	If in view mode:
		Get data (DocumentView)
		Display document viewing popup
	If in markup mode:
		Get data (DocumentView)
		Display document editing popup (DocumentEdit)
		If OK:
			If Return is False
				Show the error message in a modal dialog
			Else
				Show the new title for the document at the top of the left column
		If Cancel:
			Close with no action

Metadata button in requirement box
	If in view mode:
		Get data (RequirementView)
		Display requirement viewing popup
	If in markup mode:
		Get data (RequirementView)
		Display requirement editing popup (RequirementEdit)
		If OK:
			If Return is False
					Show the error message in a modal dialog
				Else
					Update the requirement text in box in right column
		If Cancel:
			Close with no action

Delete button in requirement box
	If in view mode:
		Modal dialog that says "Please enter markup mode before choosing this action."  with OK
	If in markup mode:
		Modal dialog that says "Do you really want to delete requirement X whose text is<br /><br />:Y"
			where "X" is the rseqno and "Y" is the rtext
		If OK:
			If Return is False
					Show the error message in a modal dialog
				Else
					Remove the requirement from the right column
					Update the left column with the new (smaller) set of requirements
		If Cancel:
			Close with no action

Add Test button in a requirement box
	If the user is not authorized to go into markup mode
		Modal dialog that says "Only users authorized to enter markup mode can take this action." with OK
	If not in markup mode
		Modal dialog that says "Please enter markup mode before choosing this action." with OK
	Display test editing popup with no fields filled in (TestNew)
	If OK:
		If Return is False
			Show the error message in a modal dialog
		Else
			Display test in list below the requirement
	If Cancel:
		Close with no action

Metadata button in test box
	If in view mode:
		Get data (TestView)
		Display test viewing popup
	If in markup mode:
		Get data (TestView)
		Display test editing popup (TestEdit)
		If OK:
			If Return is False
					Show the error message in a modal dialog
			Else
				Update test text in box in box inright column
		If Cancel:
			Close with no action
	
Delete button in test box
	If in view mode:
		Modal dialog that says "Please enter markup mode before choosing this action."  with OK
	If in markup mode:
		Modal dialog that says "Do you really want to delete test X whose text is<br /><br />:Y"
			where "X" is the tseqno and "Y" is the ttext
		If OK:
			If Return is False
					Show the error message in a modal dialog
				Else
					Remove the test box from the right column
		If Cancel:
			Close with no action

Search button
	########## To be determined later
'''

######## Test stub
if __name__=="__main__":
	Now = time.strftime("%Y-%m-%d-%H-%M-%S")
	## Tests that don't change the database
	NoncreatingTests = (
		{ "Command": "Get user access level", "Result": "Should give demo's level",
			"Args": {} },
		{ "Command": "Get user access level", "Result": "Should give Paul's level",
			"Args": {'HTTP user': 'paul'} },
		{ "Command": "Get list of documents", "Result": "Should list all the documents",
			"Args": {} },
		{ "Command": "Get document text and ranges", "Result": "Should give the ranges for 23",
			"Args": {'Document ID': 23} },
		{ "Command": "Get document text and ranges", "Result": "Should fail for bad id",
			"Args": {'Document ID': 10000} },
		{ "Command": "Document new", "Result": "Should fail because demo cannot add",
			"Args": {'Name': 'Bogus document at %s' % Now, 'Text': '<pre>This would be the text</pre>'} },
		{ "Command": "Document new", "Result": "Should fail because of no text",
			"Args": {'Name': 'Bogus document at %s' % Now} },
		{ "Command": "Document new", "Result": "Should fail because of no name",
			"Args": {'Text': '<pre>This would be the text</pre>'} },
		{ "Command": "Document view", "Result": "Lists the metadata for document 23",
			"Args": {'Document ID': 23 } },
		{ "Command": "Requirement new", "Result": "Should fail because demo cannot add",
			"Args": {'Start': 792, 'Length': 33, 'Text': 'Bogus requirement at %s' % Now, 'Base document': 23} },
		{ "Command": "Requirement new", "Result": "Should fail because of no base doc",
			"Args": {'Start': 9835, 'Length': 44, 'HTTP user': 'paul', 'Text': 'Bogus requirement at %s' % Now} },
		{ "Command": "Requirement new", "Result": "Should fail because of no start",
			"Args": {'Length': 55, 'Text': 'Bogus requirement at %s' % Now, 'HTTP user': 'paul', 'Base document': 23} },
		{ "Command": "Requirement new", "Result": "Should fail because of no length",
			"Args": {'Start': 4234, 'Text': 'Bogus requirement at %s' % Now, 'HTTP user': 'paul', 'Base document': 23} },
		{ "Command": "Requirement new", "Result": "Should fail because of no text",
			"Args": {'Start': 742, 'Length': 66, 'HTTP user': 'paul', 'Base document': 23} },
		{ "Command": "Requirement view", "Result": "Should show requirement 212",
			"Args": {'Requirement ID': 212} },
		{ "Command": "Test new", "Result": "Should fail because demo cannot add",
			"Args": {'Base requirement': 212, 'Text': 'Bogus test at %s' % Now} },
		{ "Command": "Test new", "Result": "Should fail because of no requirement ID",
			"Args": {'HTTP user': 'paul', 'Text': 'Bogus test at %s' % Now} },
		{ "Command": "Test new", "Result": "Should fail because of no text",
			"Args": {'Base requirement': 212, 'HTTP user': 'paul'} },
		{ "Command": "Test view", "Result": "Should show test 1",
			"Args": {'Test ID': 1} },
	)
	for ThisTest in NoncreatingTests:
		ThisDict = { "HTTP user": "demo" }
		ThisDict["Command"] = ThisTest["Command"]
		ThisDict.update(ThisTest["Args"])
		ThisResult = ProcessPOST(ThisDict)
		if "Text" in ThisResult:
			if (ThisResult["Text"]).startswith("<pre>"):
				ThisResult["Text"] = "<pre>Elided a bunch of text here.</pre>"
		print("%s -- %s\n%s\n\n" % (ThisTest["Result"], str(ThisDict), pprint.pformat(ThisResult)))
	## Tests that change the database
	# Create a new document
	DocNewCmd = { "Command": "Document new", 'Name': 'Bogus document at %s' % Now, 'HTTP user': 'paul',
			'Text': '<pre>This would be the text</pre>', "Comment": "DeleteMe %s" % Now }
	DocNewReturn = ProcessPOST(DocNewCmd)
	NewDocID = DocNewReturn["Document ID"]
	print("Created new document with ID %s:\n%s\n\n" % (NewDocID, pprint.pformat(DocNewReturn)))
	# Edit its metadata
	DocViewCmd = { "Command": "Document view", "Document ID": NewDocID, 'HTTP user': 'paul' }
	DocViewReturn = ProcessPOST(DocViewCmd)
	DocEditCmd = DocViewReturn.copy()
	del DocEditCmd["Return"]
	DocEditCmd["Command"] = "Document edit"
	DocEditCmd["Testable requirements"] = "Testable"
	DocEditCmd["Type"] = "Other"
	DocEditReturn = ProcessPOST(DocEditCmd)
	print("Edited document ID %s with a new 'Testable requirement' and 'Type':\n%s\n\n" % (NewDocID, pprint.pformat(DocEditReturn)))
	# Test that all fields must be present
	BadDocEditCmd = DocEditCmd.copy()
	del BadDocEditCmd["Type"]
	BadDocEditReturn = ProcessPOST(BadDocEditCmd)
	print("This doc edit command should have failed:\n%s\n\n" % pprint.pformat(BadDocEditReturn))
	# Create a new requirement
	ReqNewCmd = { "Command": "Requirement new", 'Start': 1872, 'Length': 22, 'Text': 'Bogus requirement at %s' % Now, 'HTTP user': 'paul',
			'Base document': NewDocID, "Comment": "DeleteMe %s" % Now }
	ReqNewReturn = ProcessPOST(ReqNewCmd)
	NewReqID = ReqNewReturn["Requirement ID"]
	print("Created new requirement with ID %s:\n%s\n\n" % (NewReqID, pprint.pformat(ReqNewReturn)))
	# Edit its metadata
	ReqViewCmd = { "Command": "Requirement view", "Requirement ID": NewReqID, 'HTTP user': 'paul' }
	ReqViewReturn = ProcessPOST(ReqViewCmd)
	ReqEditCmd = ReqViewReturn.copy()
	del ReqEditCmd["Return"]
	ReqEditCmd["Command"] = "Requirement edit"
	ReqEditCmd["Text"] = "This requirement text was clearly edited"
	ReqEditCmd["Type"] = "HighVol"
	ReqEditReturn = ProcessPOST(ReqEditCmd)
	print("Edited requirement ID %s with a new 'Text' and 'Type':\n%s\n\n" % (NewReqID, pprint.pformat(ReqEditReturn)))
	# Test that all fields must be present
	BadReqEditCmd = ReqEditCmd.copy()
	del BadReqEditCmd["Type"]
	BadReqEditReturn = ProcessPOST(BadReqEditCmd)
	print("This requirement edit command should have failed:\n%s\n\n" % pprint.pformat(BadReqEditReturn))
	# Create a new test
	TestNewCmd = { "Command": "Test new", 'Text': 'Bogus test at %s' % Now, 'HTTP user': 'paul',
			'Base requirement': NewReqID, "Comment": "DeleteMe %s" % Now }
	TestNewReturn = ProcessPOST(TestNewCmd)
	NewTestID = TestNewReturn["Test ID"]
	print("Created new test with ID %s:\n%s\n\n" % (NewTestID, pprint.pformat(TestNewReturn)))
	# Edit its metadata
	TestViewCmd = { "Command": "Test view", "Test ID": NewTestID, 'HTTP user': 'paul' }
	TestViewReturn = ProcessPOST(TestViewCmd)
	TestEditCmd = TestViewReturn.copy()
	del TestEditCmd["Return"]
	TestEditCmd["Command"] = "Test edit"
	TestEditCmd["Text"] = "This test text was clearly edited"
	TestEditCmd["DUT"] = "Server"
	TestEditReturn = ProcessPOST(TestEditCmd)
	print("Edited test ID %s with a new 'Text' and 'DUT':\n%s\n\n" % (NewTestID, pprint.pformat(TestEditReturn)))
	# Test that all fields must be present
	BadTestEditCmd = TestEditCmd.copy()
	del BadTestEditCmd["Outcome"]
	BadTestEditReturn = ProcessPOST(BadTestEditCmd)
	print("This test edit command should have failed:\n%s\n\n" % pprint.pformat(BadTestEditReturn))
	# Clean up after all that creation and editing
	db = Conformdb("paul")
	DocCleanupReturn = db.deletebasedoc(bdcomment="DeleteMe")
	print("The return from deletebasedoc was '%s'." % pprint.pformat(DocCleanupReturn))
	ReqCleanupReturn = db.deleterequirement(rcomment="DeleteMe")
	print("The return from deleterequirement was '%s'." % pprint.pformat(ReqCleanupReturn))
	TestCleanupReturn = db.deletetests(tcomment="DeleteMe")
	print("The return from deletetests was '%s'." % pprint.pformat(TestCleanupReturn))
