// global vars
var baseDocumentID = "";
var baseDocumentName = "";
var baseDocumentText = "";
var baseRequirementID = 0;
var baseTestID = 0;
var userAccessLevel = "view";
var userCanMarkup = false; // this value set from entitlements on document load
var debug = true;
var currentMode = "view";
var scrollTop = 0;
var lastRequirementAdded = 0;
var lastRequirementArrow = 1;
var totalRequirements = 0; // init in singleSpan click binding function

var helpText = "" +
'<b><font size=+1>Viewing in the Database</font></b>' +
'<br><br>' +
'The "Docs" list shows you every DNS-related RFC (and other documents) that was reviewed as a part of the project. ' +
'Choose individual documents to read from the "Docs" list. ' +
'When editing a document, you change documents by selecting the Docs item:<br>' +
'&nbsp;&nbsp;&nbsp;&nbsp;<img src="/graphics/docs-icon.png"/><br>' +
'You then select the desired document from the list. You can change the sorting by clicking on the column headings.' +
'<br><br>' +
'In the main document window, the left column shows the document with every requirement highlighted. ' +
'The heading fo the document has a "metadata" button that shows information about the doucment. ' +
'If the document has no testable requirements, that is shown as a banner under the header. ' +
'<br><br>' +
'Clicking on a highlighted requriment in the document cuase the right column to show the derived requirement, ' +
'plus any tests for that requirement. ' +
'If a requirement is not testable, the reason for that is listed in a banner as part of the test. ' +
'<br><br>' +
'Each requirement that has tests has the tests listed under the requirement. ' +
'A test consists of many parts, including the action to be taken, the type of object to be acted on ' +
'(such as "Client", "Server", "Resolver", and so on), the method to test the outcome, and any comments. ' +
'The test descriptions describe what actions to take on the DUT (device under test) and what to take ' +
'on the LS (lab systems). For example, a test on a DUT resolver might involve both an LS client sending ' +
'requests to the DUT resolver, and the DUT resolver sending requests to an LS authoritative server.' +
'<br><br>' +
'Documents, requirements, and tests each have a "metadata" button:<br>' +
'&nbsp;&nbsp;&nbsp;&nbsp;<img src="/graphics/metadata-button.png"/><br>' +
'When viewing, this brings up a dialog with relevant information about the item; when editing, ' +
'the dialog lets you change the information. ' +
'Documents, requirements, and tests can also have comments, which appear with the icon:<br>' +
'&nbsp;&nbsp;&nbsp;&nbsp;<img src="/graphics/comment-icon.png"/><br>' +
"Comments can also be seen in the item's metadata. " +
'<br><hr><br>' +
'<b><font size=+1>Editing in the Database</font></b>' +
'<br><br>' +
'When you are in markup mode, you can edit records in the database. There are a few different ways to edit. ' +
'When editing a document, you can change the metadata. ' +
'When editing a requirement, you can change the metadata, add tests, and even delete the requirement itself. ' +
'When editing tests, you can change the metadata and delete the test itself. ' +
'<br><br>' +
'To add tests to a document, you select the text in the document you want to be a new requirement. ' +
'This brings up a metadata dialog for the new requirement. ' +
'<br><br>' +
'You add a document to the database by using the "New Document" command in the Admin menu. ' +
'There is no way to delete a document from the web UI: that has to be done by hand in the database. ' +
'<br><hr><br>' +
'<b><font size=+1>Downloading Test Plans</font></b>' +
'<br><br>' +
'There are two styles of test plan, "full" and "testable-only". The former contains everything in ' +
'the database, while the latter has only those documents that have testable requirmements, and lists ' +
'only those testable requirements. ' +
'The result of each is an HTML-formatted test plan that is saved on the local computer. ' +
'<br><hr><br>' +
'<b><font size=+1>Downloading the Database</font></b>' +
'<br><br>' +
'The "Download Database as JSON" command in the Admin menu will save a full copy of the database as JSON. ' +
'The JSON database is not complete: it does not contain the text of the base specifications. ' +
'To get the full database, the database administrator can use the "mysqldump" command at the command line.' +
'<br><hr><br>' +
'Copyright (c) 2015, Standcore LLC<br>' +
'All rights reserved.<br>' +
'<br>' +
'Redistribution and use in source and binary forms, with or without modification,<br>' +
'are permitted provided that the following conditions are met:<br>' +
'<br>' +
'1. Redistributions of source code must retain the above copyright notice, this<br>' +
'list of conditions, and the following disclaimer.<br>' +
'<br>' +
'2. Redistributions in binary form must reproduce the above copyright notice,<br>' +
'this list of conditions, and the following disclaimer in the documentation and/or<br>' +
'other materials provided with the distribution.<br>' +
'<br>' +
'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND<br>' +
'ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED<br>' +
'WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE<br>' +
'DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR<br>' +
'ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES<br>' +
'(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;<br>' +
'LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON<br>' +
'ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT<br>' +
'(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS<br>' +
'SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.<br>' +
'<br><hr><br>' +
'If you have any questions about the web UI, please contact Standcore directly. Thank you!'
;

// general utility function for invoking error modal dialog
function invokeErrorModal(title, content) {
    $("#errorModal .modal-body").html(content);
    $("#errorModal .modal-title").html(title);
    $('#errorModal').modal('show'); 
}

// replace line breaks with <br /> tag for display, safely handle null input
function replaceLBBR(s) {
	if (s) {
		return s.replace(/\n/g, '<br/>');
	} else {
		return s;
	}
}

function standardErrorModalAjaxReturn(returnErr) {
    invokeErrorModal("Error", "There was an error, and the changes were not made. The error is:<br /><br />" + returnErr);
}            

function writeLog(a,b) {
    if (debug) {
        console.log("---" + a + "---");
        console.log(b);
    }
}

function logout() {
    // window.location.href = location.protocol+'//log:out@'+location.hostname+(location.port ? ':'+location.port: '');
    var outcome, u, m = "You should be logged out now.";
    // IE has a simple solution for it - API:
    try { outcome = document.execCommand("ClearAuthenticationCache") }catch(e){}
    // Other browsers need a larger solution - AJAX call with special user name - 'logout'.
    if (!outcome) {
        // Let's create an xmlhttp object
        outcome = (function(x){
            if (x) {
                // the reason we use "random" value for password is 
                // that browsers cache requests. changing
                // password effectively behaves like cache-busing.
                x.open("HEAD", location.href, true, "logout", (new Date()).getTime().toString())
                x.send("")
                // x.abort()
                return 1 // this is **speculative** "We are done." 
            } else {
                return
            }
        })(window.XMLHttpRequest ? new window.XMLHttpRequest() : ( window.ActiveXObject ? new ActiveXObject("Microsoft.XMLHTTP") : u ))
    }
    if (!outcome) {
        m = "Your browser is too old or too weird to support log out functionality. Close all windows and restart the browser."
    }
    alert(m)
}

// general function to issue Ajax request to server
// parameters are command name (text) and return function
function issueAjax(cmd, fn) {
    $.ajax({
        type: "POST",
        url: "/",
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(cmd),
        success: function(data){
            fn(data);
        }
    });
}

// get paramter value from URL string
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

// admin functions
function admin_new_document() {
    if (userCanMarkup) {
        if (currentMode === "markup") {
            $("#adminNewDocument").modal("show");
        } else {
            invokeErrorModal("Error", "Please enter markup mode before choosing this action.");
        }
    } else {
        invokeErrorModal("Error", "Only users authorized to enter markup mode can take this action.");
    }
}

function admin_download_full_test_plan() { 
    // # C: { "Command": "Get full test plan" }
    // # S: { "Command": "Get full test plan", "Test plan HTML": s_html, "Return": returnval }
    issueAjax({ Command : "Get full test plan" }, function(data) {
    
        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // show modal
            $("#downloadFullTestPlan").modal("show");

            // set default file name in text field and download link
            $(".dloadFullTestPlanFileName").val("DNSConformanceFullTestPlan.html");
            $("#dloadFullTestPlan").attr("download", "DNSConformanceFullTestPlan.html");

            // load up url
            $("#dloadFullTestPlan").attr("href", "data:text/html;charset=UTF-8," + encodeURIComponent(data["Test plan HTML"]));

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }
    });
}

function admin_download_testable_only_test_plan() { 
    // # C: { "Command": "Get test plan testable only" }
    // # S: { "Command": "Get test plan testable only", "Test plan HTML": s_html, "Return": returnval }
    issueAjax({ Command : "Get test plan testable only" }, function(data) {
    
        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // show modal
            $("#downloadTestableOnlyTestPlan").modal("show");

            // set default file name in text field and download link
            $(".dloadTestableOnlyTestPlanFileName").val("DNSConformanceTestableOnlyTestPlan.html");
            $("#dloadTestableOnlyTestPlan").attr("download", "DNSConformanceTestableOnlyTestPlan.html");

            // load up url
            $("#dloadTestableOnlyTestPlan").attr("href", "data:text/html;charset=UTF-8," + encodeURIComponent(data["Test plan HTML"]));

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }
    });
}

function admin_download_db_json() { 
    // # C: { "Command": "Get JSON database" }
    // # S: { "Command": "Get JSON database", "Database JSON": s_data, "Return": returnval }
    issueAjax({ Command : "Get JSON database" }, function(data) {
    
        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // show modal
            $("#downloadJSON").modal("show");

            // set default file name in text field and download link
            $(".dloadJSONFileName").val("DNSConformanceDatabase.json");
            $("#dloadJSON").attr("download", "DNSConformanceDatabase.json");

            // load up url
            $("#dloadJSON").attr("href", "data:application/json;charset=UTF-8," + encodeURIComponent(data["Database JSON"]));

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }
    });

}

function admin_help() { 
    invokeErrorModal("Help", helpText);
}

// handle clicks on view/markup button toggle
function switchModes(clickedButton) {
    var clickedMode = clickedButton.text();

    if (clickedMode === "View") {
        // set toggle state of buttons
        $(".modeSelector button").removeClass("active");
        $(".modeSelector .viewModeButton").addClass("active");
        currentMode = "view";
    } else {
        if (userCanMarkup) {
            // set toggle state of buttons
            $(".modeSelector button").removeClass("active");
            $(".modeSelector .markupModeButton").addClass("active");
            currentMode = "markup";
        } else {
            // if user cannot go into markup, show error
            // set toggle state of buttons for view state
            $(".modeSelector button").removeClass("active");
            $(".modeSelector .viewModeButton").addClass("active");
            invokeErrorModal("Error", "Only users authorized to enter markup mode can take this action.");
        }
    }
}

// load document metadata into dialog
function loadDocumentMD(docID) {
    // get the metadata for the current document and load it up
    issueAjax({ Command : "Document view", "Document ID": docID }, function(data) {

        writeLog("loadDocumentMDDone", data);
    
        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // show testable requirements notice
            if (data["Testable requirements"] === "None") {
                $(".alert-no-testable").show();
            }

            var documentComment = replaceLBBR(data['Comment']);
            if (documentComment != "") {
                $("#rfcComment").html('<i class="fa fa-comment-o"></i> ' + documentComment).show();    
            }
        
            // size left col once more
            setScrollHeight();

            $("#documentMDModal .s_bdseqno").html(data["Document ID"]);
            $("#documentMDModal .s_bdname").html(data["Name"]);
            $("#documentMDModal .s_bddoctype").html(data["Type"]);
            $("#documentMDModal .s_bdrfcno").html(data["RFC"]);
            $("#documentMDModal .s_bderrata").html(replaceLBBR(data["Errata notes"]));
            $("#documentMDModal .s_bdediff").html(replaceLBBR(data["Errata diff"]));
            $("#documentMDModal .s_bdthstat").html(data["Testable requirements"]);
            $("#documentMDModal .s_bdcomment").html(replaceLBBR(data["Comment"]));
            $("#documentMDModal .s_bddstat").html(data["Status"]);
            $("#documentMDModal .s_bduser").html(data["This user"]);
            $("#documentMDModal .s_bdupdated").html(data["Updated"]);
            $("#documentMDModal .s_bdadded").html(data["Added"]);
            $("#documentMDModal .s_bdreport").html(data["Summary report"]);

            $("#documentMDModalEditable .s_bdseqno").html(data["Document ID"]);
            $("#documentMDModalEditable .s_bdname").val(data["Name"]);
            $("#documentMDModalEditable .s_bddoctype").val(data["Type"]);
            $("#documentMDModalEditable .s_bdrfcno").val(data["RFC"]);
            $("#documentMDModalEditable .s_bderrata").val(data["Errata notes"]);
            $("#documentMDModalEditable .s_bdediff").val(data["Errata diff"]);
            $("#documentMDModalEditable .s_bdthstat").val(data["Testable requirements"]);
            $("#documentMDModalEditable .s_bdcomment").val(data["Comment"]);
            $("#documentMDModalEditable .s_bddstat").val(data["Status"]);
            $("#documentMDModalEditable .s_bduser").html(data["This user"]);
            $("#documentMDModalEditable .s_bdupdated").html(data["Updated"]);
            $("#documentMDModalEditable .s_bdadded").html(data["Added"]);
            $("#documentMDModalEditable .s_bdreport").html(data["Summary report"]);

        }
    });
}

// get test details and load up metadata overlay
function testMDLinkClick(obj) {
        
    var thisTestID = $(obj).attr("id").slice(4);
    issueAjax({ Command : "Test view", "Test ID": thisTestID }, function(data) {

        writeLog("loadTestViewDone", data);

        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // populate the modal
            $("#testMDModal .s_tseqno").html(data["Test ID"]);
            $("#testMDModal .s_rseqno").html(data["Base requirement"]);
            $("#testMDModal .s_tsameas").html(data["Same as"]);
            $("#testMDModal .s_ttext").html(data["Text"]);
            $("#testMDModal .s_tdut").html(data["DUT"]);
            $("#testMDModal .s_toutcome").html(replaceLBBR(data["Outcome"]));
            $("#testMDModal .s_tneg").html(replaceLBBR(data["Neg"]));
            $("#testMDModal .s_tcomment").html(replaceLBBR(data["Comment"]));
            $("#testMDModal .s_tmasterfile").html(replaceLBBR(data["Master file entry"]));
            $("#testMDModal .s_tlscommand").html(replaceLBBR(data["LS command"]));
            $("#testMDModal .s_treplacedby").html(data["Replaced by"]);
            $("#testMDModal .s_tuser").html(data["This user"]);
            $("#testMDModal .s_tupdated").html(data["Updated"]);
            $("#testMDModal .s_tadded").html(data["Added"]);

            $("#testMDModalEditable .s_tseqno").html(data["Test ID"]);
            $("#testMDModalEditable .s_rseqno").val(data["Base requirement"]);
            $("#testMDModalEditable .s_tsameas").val(data["Same as"]);
            $("#testMDModalEditable .s_ttext").html(data["Text"]);
            $("#testMDModalEditable .s_tdut").val(data["DUT"]);
            $("#testMDModalEditable .s_toutcome").val(data["Outcome"]);
            $("#testMDModalEditable .s_tneg").val(data["Neg"]);
            $("#testMDModalEditable .s_tcomment").val(data["Comment"]);
            $("#testMDModalEditable .s_tmasterfile").val(data["Master file entry"]);
            $("#testMDModalEditable .s_tlscommand").val(data["LS command"]);
            $("#testMDModalEditable .s_treplacedby").val(data["Replaced by"]);
            $("#testMDModalEditable .s_tuser").html(data["This user"]);
            $("#testMDModalEditable .s_tupdated").html(data["Updated"]);
            $("#testMDModalEditable .s_tadded").html(data["Added"]);

            if (currentMode === "markup") {
                $('#testMDModalEditable').modal('show');
            } else {
                $('#testMDModal').modal('show');
            }

        }

    }); // end get test view
}

function testDeleteLinkClick(obj) {
    var thisTestID = $(obj).attr("id").slice(4);
    baseTestID = thisTestID;
    if (currentMode === "markup") {
        
        // get test text and load into modal along with text
        issueAjax({ Command : "Test view", "Test ID": thisTestID }, function(data) {

            var returnVal = data.Return[0];
            var returnErr = data.Return[1];

            if (returnVal) {
                // populate and show the modal
                $("#testDeleteModal .tseqno").html(data["Test ID"]);
                $("#testDeleteModal .ttext").html(data["Text"]);
                $('#testDeleteModal').modal('show');
            }

        });
        
    } else {
        invokeErrorModal("Error", "Please enter markup mode before choosing this action.");
    }
}

function requirementDeleteLinkClick() {
    if (currentMode === "markup") {
        $("#requirementDeleteModal .rseqno").text(baseRequirementID);
        $("#requirementDeleteModal .rtext").html($(".reqDetail p").html());
        $('#requirementDeleteModal').modal('show');
    } else {
        invokeErrorModal("Error", "Please enter markup mode before choosing this action.");
    }
}

function documentMDLinkClick() {
    if (currentMode === "markup") {
        $('#documentMDModalEditable').modal('show');
    } else {
        $('#documentMDModal').modal('show');
    }
}

function requirementMDLinkClick() {
    if (currentMode === "markup") {
        $('#requirementMDModalEditable').modal('show');
    } else {
        $('#requirementMDModal').modal('show');
    }
}

// load requirement metadata into dialog
function loadRequirementMD(reqID) {

    // preserve the ID for use in adding tests
    baseRequirementID = reqID;

    // get the metadata for the current document and load it up
    issueAjax({ Command : "Requirement view", "Requirement ID": reqID }, function(data) {

        writeLog("loadRequirementMDDone", data);
    
        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            $("#requirementMDModal .rseqno").html(data["Requirement"]);
            $("#requirementMDModal .bdseqno").html(data["Base document"]);
            $("#requirementMDModal .rstart").html(data["Start"]);
            $("#requirementMDModal .rlength").html(data["Length"]);
            $("#requirementMDModal .rtext").html(replaceLBBR(data["Text"]));
            $("#requirementMDModal .rcomment").html(replaceLBBR(data["Comment"]));
            $("#requirementMDModal .rreplacedby").html(data["Replaced by"]);
            $("#requirementMDModal .ruser").html(data["This user"]);
            $("#requirementMDModal .rupdated").html(data["Updated"]);
            $("#requirementMDModal .radded").html(data["Added"]);
            $("#requirementMDModal .rtype").html(data["Type"]);
            $("#requirementMDModal .rsameas").html(data["Same as"]);

            $("#requirementMDModalEditable .rseqno").html(data["Requirement"]);
            $("#requirementMDModalEditable .bdseqno").val(data["Base document"]);
            $("#requirementMDModalEditable .rstart").val(data["Start"]);
            $("#requirementMDModalEditable .rlength").val(data["Length"]);
            $("#requirementMDModalEditable .rtext").val(data["Text"]);
            $("#requirementMDModalEditable .rcomment").val(data["Comment"]);
            $("#requirementMDModalEditable .rreplacedby").val(data["Replaced by"]);
            $("#requirementMDModalEditable .ruser").html(data["This user"]);
            $("#requirementMDModalEditable .rupdated").html(data["Updated"]);
            $("#requirementMDModalEditable .radded").html(data["Added"]);
            $("#requirementMDModalEditable .rtype").val(data["Type"]);
            $("#requirementMDModalEditable .rsameas").val(data["Same as"]);

            $(".requirementMDLink").unbind("click");
            $(".requirementMDLink").click(function() {
                requirementMDLinkClick();
            });

            $(".requirementDeleteLink").unbind("click");
            $(".requirementDeleteLink").click(function() {
                requirementDeleteLinkClick();
            });

            var testsArray = data["Tests"];
            var testString = "";

            if (testsArray.length) {
                // write tests into the right column under the requirements DIV

                for (var i = 0; i < testsArray.length; i++) {
                    testString += '<div class="testDetail">';
                    testString += '<h2>Test ' + testsArray[i][0] + ' <div class="testDUT">' + testsArray[i][2] + '</div>';
                    if (testsArray[i][6] > 0) {
                        testString += '<div class="testSameAs">Same as ' + testsArray[i][6] + '</div>';
                    } else {
                        testString += '<div class="testSameAs" style="display: none"></div>';
                    }
                    testString += ' <a id="test' + testsArray[i][0] + '" class="btn btn-xxs btn-danger pull-right testDeleteLink">delete</a>';
                    testString += ' <a id="test' + testsArray[i][0] + '" class="btn btn-xxs btn-default pull-right testMDLink" style="margin-right: 5px">metadata</a></h2>';
                    testString += '<div class="testText"><p>' + testsArray[i][1] + '</p></div>';
                    if ((testsArray[i][7] !== "") && (testsArray[i][7] !== null)) {
                        testString += '<div class="testLSCommand">LS Command: ' + replaceLBBR(testsArray[i][7]) + '</div>';
                    } else {
                        testString += '<div class="testLSCommand" style="display: none"></div>';
                    }
                    if (testsArray[i][3] !== "") {
                        testString += '<div class="testOutcome">Outcome: ' + replaceLBBR(testsArray[i][3]) + '</div>';
                    } else {
                        testString += '<div class="testOutcome" style="display: none"></div>';
                    }
                    if (testsArray[i][4] !== "") {
                        testString += '<div class="testComment"><i class="fa fa-comment-o"></i> ' + replaceLBBR(testsArray[i][4]) + '</div>';
                    } else {
                        testString += '<div class="testComment" style="display: none"></div>';
                    }
                    if (testsArray[i][5] !== "") {
                        testString += '<div class="testMasterFile">Master file entry: ' + replaceLBBR(testsArray[i][5]) + '</div>';
                    } else {
                        testString += '<div class="testMasterFile" style="display: none"></div>';
                    }
                    if (testsArray[i][8] !== "None") {
                        testString += '<div class="testNeg">Negative: ' + replaceLBBR(testsArray[i][8]) + '</div>';
                    } else {
                        testString += '<div class="testNeg" style="display: none"></div>';
                    }
                    
                    testString += '</div>';
                    $(".rfcReqTests").append(testString);
                    testString = "";
                }
            }

            $(".testMDLink").unbind("click");
            $(".testMDLink").click(function() {
                testMDLinkClick($(this));
            }); // end testMDLink click

            $(".testDeleteLink").unbind("click");
            $(".testDeleteLink").click(function() {
                testDeleteLinkClick($(this));
            }); // end testDeleteLink click
        }
    });
}

// return function for setting the user's access level
function getUserAccessLevelDone(data) {
    writeLog("getUserAccessLevelDone", data);
    $(".modeIndicator").html("View");
    
    var returnVal = data.Return[0];
    var returnErr = data.Return[1];

    if (returnVal) {
        if (data.Access === "markup") {
            userCanMarkup = true;
            $(".markupModeButton").click(); // set markup default
            $(".modeIndicator").html("Markup");
        } else {
            userCanMarkup = false;
            $(".modeIndicator").html("View");
        }
    }
}

// utility for string insertion
String.prototype.insertAt=function(index, string) { 
  return this.substr(0, index) + string + this.substr(index);
};

// callback function for requirement view done
function requirementViewDone(data) {
    writeLog("requirementViewDone", data);
    $("#reqDiv .requirementNumber").text(data['Requirement ID']);
    if (data["Same as"] > 0) {
        $("#reqDiv .requirementSameAs").text("Same as " + data['Same as']).show();
    } else {
        $("#reqDiv .requirementSameAs").text("").hide();
    }
    $("#reqDiv .requirementText").html(data['Text']);
    if (data['Comment'] !== "") {
        $("#reqDiv .requirementComment").html('<i class="fa fa-comment-o"></i> ' + replaceLBBR(data['Comment'])).show();
    } else {
        $("#reqDiv .requirementComment").hide();
    }
    

    // requirement type notice
    var thisType = data['Type'];
    var typeElaborated = "";
    if ((thisType !== "None") && (thisType !== "Testable")) {
        if (thisType === "Format") { typeElaborated = "Nontestable - message format"; }
        if (thisType === "Operational") { typeElaborated = "Nontestable - operational practices"; }
        if (thisType === "HighVol") { typeElaborated = "Nontestable - high volume"; }
        if (thisType === "LongPeriod") { typeElaborated = "Nontestable - long periods"; }
        if (thisType === "FutureSpec") { typeElaborated = "Nontestable - applies to future specifications"; }
        if (thisType === "Procedural") { typeElaborated = "Nontestable - procedural"; }
        if (thisType === "Historic") { typeElaborated = "Nontestable - historic"; }
        if (thisType === "API") { typeElaborated = "Nontestable - DNS API only"; }
        if (thisType === "AppsAndPeople") { typeElaborated = "Nontestable - Applications and people only"; }
        $(".requirementTypeNotice").text(typeElaborated).fadeIn();
    } else {
        $(".requirementTypeNotice").text("").hide();
    }

    $(".reqDetail").fadeIn();

    // remove any previous tests
    $("#reqDiv hr").remove();
    $("#reqDiv .testDetail").remove();

    // load requirement MD
    loadRequirementMD(data['Requirement ID']);
}

// set up binding for single span clicking, should get and show requirement in right column
function bindSingleSpanClicks() {
    $(".singleSpan").click(function() {
        var sSpanID = $(this).attr("id").slice(3);
        issueAjax({ Command : "Requirement view", "Requirement ID": sSpanID }, requirementViewDone);
		$(".singleSpan").css("border", 0);
        lastRequirementArrow = $(".singleSpan").index($(this))+1;
        $(".singleSpan" + lastRequirementArrow).css("border", "1px solid green");
    });
    totalRequirements = $(".singleSpan").size();
}

// return function for single document
function initDocumentDone(data) {
    writeLog("initDocumentDone", data);

    var returnVal = data.Return[0];
    var returnErr = data.Return[1];
    var insertString = "";
    var cumulativeInserted = 0;

    if (returnVal) {
        var documentName = data['Name'];
        var documentText = data['Text'];
        baseDocumentText = documentText; // save for editing document metadata, must pass unaltered text back
        var documentID = data['Document ID'];
        var documentRanges = data.Ranges;
        var documentRangesSorted = [];
        var username = data['HTTP user'];

        // set username in header
        $(".username").text(username);

        // create array of ranges
        $.each(documentRanges, function(requirementID, rangeDetails) {
            var rangeStart = rangeDetails[0];
            var rangeLength = rangeDetails[1];
            documentRangesSorted.push([requirementID, rangeStart, rangeLength, "single"]);
        });

        // sort by rangeStart [1]
        documentRangesSorted = documentRangesSorted.sort(function(a,b) {
            return a[1] - b[1];
        });

        // loop through documentRangesSorted and identify any overlapping ranges
        // if any overlapping ranges found, create new "double" entry and modify existing
        var documentRangesSortedLength = documentRangesSorted.length;
        var thisStart = 0;
        var thisLength = 0;
        var thisEnd = 0;
        var nextStart = 0;
        var nextStartMod = 0;
        var nextLength = 0;
        var nextEnd = 0;
        var doubleRangeArray = [];

        for (var i = 0; i < documentRangesSortedLength-1; i++) {

            // get this start and length
            thisStart = documentRangesSorted[i][1];
            thisLength = documentRangesSorted[i][2];

            // console.log("thisStart: " + thisStart);
            // console.log("thisLength: " + thisLength);

            // get next start and length
            nextStart = documentRangesSorted[i+1][1];
            nextLength = documentRangesSorted[i+1][2];

            // console.log("nextStart: " + nextStart);
            // console.log("nextLength: " + nextLength);

            // calculate this end
            thisEnd = thisStart + thisLength;

            // console.log("thisEnd: " + thisEnd);

            // if there's an overlap, let's do the math
            if (nextStart < thisEnd) {

                // reset thisLength in array
                documentRangesSorted[i][2] = nextStart - thisStart;

                // calculate doublerange start and end for addition to another doubleRangeArray
                doubleRangeArray.push([0, thisStart + documentRangesSorted[i][2], thisEnd - (thisStart + documentRangesSorted[i][2]), "double"]);

                // what SHOULD the next start be? reset it
                documentRangesSorted[i+1][1] = thisEnd;

                // reset the next length
                documentRangesSorted[i+1][2] = (nextStart + nextLength) - thisEnd;

            }

        } // end for loop looking for overlapping ranges

        // merge the two arrays now
        documentRangesSorted = documentRangesSorted.concat(doubleRangeArray);
        
        // re-sort the array
        documentRangesSorted = documentRangesSorted.sort(function(a,b) {
            return a[1] - b[1];
        });

        // highlight the ranges
        reqNum = 1;
        $.each(documentRangesSorted, function(key, value) {
            var requirementID = value[0];
            var rangeStart = value[1] + 1;
            var rangeLength = value[2];
            var spanType = value[3];
            
            // console.log(requirementID + ": " + spanType + " from " + rangeStart + " to " + parseInt(rangeStart+rangeLength) + " (length " + rangeLength + ")");

            if (spanType === "single") {
                insertString = '<span id="req' + requirementID + '" class="singleSpan singleSpan' + reqNum + '" title="Requirement ' + requirementID + '">';
                reqNum++;
            } else {
                insertString = '<span class="doubleSpan">';
            }
            documentText = documentText.insertAt(rangeStart + cumulativeInserted, insertString);
            cumulativeInserted += insertString.length;

            insertString = '</span>';
            documentText = documentText.insertAt(rangeStart + cumulativeInserted + rangeLength, insertString);
            cumulativeInserted += insertString.length;
        });

        // update global vars
        baseDocumentID = documentID;
        baseDocumentName = documentName;

        // update document HTML with these values
        if(documentName.indexOf(':') === -1) {
            $("#rfcNumber").text("--");
            $("#rfcTitle").text(documentName.trim());
        } else {
            $("#rfcNumber").text(documentName.split(/:(.+)/)[0]);
            $("#rfcTitle").text(documentName.split(/:(.+)/)[1].trim());
        }
        
        //writeLog("text before written to DOM", documentText);
        $(".rfcContents").html(documentText);

        // bind clicks on those highlighted elements
        bindSingleSpanClicks();

        // click the one we just added to show it in the right column
        $("#req" + lastRequirementAdded).click();     

        // get and set the user's access level
        issueAjax({ Command : "Get user access level" }, getUserAccessLevelDone);

        // scroll left pane if in the middle of doing updates
        if (scrollTop > 0) {
            $(".rfcContents").scrollTop(scrollTop);
            scrollTop = 0;
        } else {
            // initial load: is there a singleSpan already? if so, click it and scroll to it
            if ($(".singleSpan:first-child").length) {
                $(".singleSpan:first-child" + lastRequirementArrow).css("border", "1px solid green");
                $(".singleSpan:first-child").click();
                var offset = $(".singleSpan:first-child").offset();
                var offoffset = offset.top - 175;
                $(".rfcContents").scrollTop(offoffset);
            }
        }
        
        // link up document MD link
        $(".documentMDLink").click(function() {
            documentMDLinkClick();
        }); // end documentMDLink click

    }
}

// get and load document, right now we'll just call for metadata to be loaded
function initDocument() {
    if (document.location.href.indexOf('document.htm') > -1 ) {
        // we are on document page, so get ID parameter and make JSON request for document data
        var docID = getParameterByName('id');
        issueAjax({ Command : "Get document text and ranges", "Document ID": docID }, initDocumentDone);

        // load in document metadata
        loadDocumentMD(docID);
    }
}

// return function for make requirement submission
function submitMakeRequirementDone(data) {
    writeLog("submitMakeRequirementDone", data);

    var returnVal = data.Return[0];
    var returnErr = data.Return[1];

    if (returnVal) {

        // save the scroll position of the left pane
        scrollTop = $(".rfcContents").scrollTop();

        // save this new requirement's ID so we can show it automatically
        lastRequirementAdded = data["Requirement ID"];

        // let's now get the document again to get the new range
        initDocument();

    } else {
        standardErrorModalAjaxReturn(returnErr);
    }
    
}

// submit the make requirement form
function submitMakeRequirement() {
    // get values from form
    var s_bdseqno = $('#makeRequirementModal .modal-body .s_bdseqno').val();
    var s_rstart = $('#makeRequirementModal .modal-body .s_rstart').val();
    var s_rlength = $('#makeRequirementModal .modal-body .s_rlength').val();
    var s_rtext = $('#makeRequirementModal .modal-body .s_rtext').val();
    var s_rtype = $('#makeRequirementModal .modal-body .s_rtype').val();
    var s_rcomment = $('#makeRequirementModal .modal-body .s_rcomment').val();
    var s_rreplacedby = $('#makeRequirementModal .modal-body .s_rreplacedby').val();
    var s_rsameas = $('#makeRequirementModal .modal-body .s_rsameas').val();

    if (s_rreplacedby === "") {
        s_rreplacedby = 0;
    }

    // submit ajax
    issueAjax({ Command : "Requirement new", "Base document": s_bdseqno, "Start": s_rstart, "Length": s_rlength, "Text": s_rtext, "Type": s_rtype, "Comment": s_rcomment, "Replaced by": s_rreplacedby, "Same as": s_rsameas }, submitMakeRequirementDone);
}

// submit change of document metadata
function submitDocumentMD() {

    // get values from form
    var s_bdname = $('#documentMDModalEditable .modal-body .s_bdname').val();
    var s_bddoctype = $('#documentMDModalEditable .modal-body .s_bddoctype').val();
    var s_bdrfcno = $('#documentMDModalEditable .modal-body .s_bdrfcno').val();
    var s_bderrata = $('#documentMDModalEditable .modal-body .s_bderrata').val();
    var s_bdediff = $('#documentMDModalEditable .modal-body .s_bdediff').val();
    var s_bdthstat = $('#documentMDModalEditable .modal-body .s_bdthstat').val();
    var s_bdcomment = $('#documentMDModalEditable .modal-body .s_bdcomment').val();
    var s_bddstat = $('#documentMDModalEditable .modal-body .s_bddstat').val();

    // # C: { "Command": "Document edit", "Document ID": c_bdseqno, "Name": c_bdname, "Type": c_bddoctype, "RFC": c_bdrfcno,
    // #      "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat, 
    // #      "Comment": c_bdcomment, "Staus": c_bddstat }
    // #    -- All fields are required
    // # S: { "Command": "Document edit", "Document ID": s_bdseqno, "Name": c_bdname, "Type": c_bddoctype, "RFC": c_bdrfcno, 
    // #      "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat,
    // #      "Comment": c_bdcomment, "Staus": c_bddstat }

    issueAjax({ 
        Command : "Document edit", 
        "Document ID": baseDocumentID, 
        "Name": s_bdname, 
        "Type": s_bddoctype, 
        "RFC": s_bdrfcno, 
        "Text": baseDocumentText, 
        "Errata notes": s_bderrata, 
        "Errata diff": s_bdediff, 
        "Testable requirements": s_bdthstat, 
        "Comment": s_bdcomment, 
        "Status": s_bddstat 
    }, function(data) {

        writeLog("submitDocumentMDDone", data);

        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // update RFC Title
            var newName = data["Name"];
            $("#rfcNumber").text(newName.split(/:(.+)/)[0]);
            if (newName.split(/:(.+)/)[1]) {
                $("#rfcTitle").text(newName.split(/:(.+)/)[1].trim());
            }

            // update comment
            var docComment = replaceLBBR(data["Comment"]);
            if (docComment != "") {
                $("#rfcComment").html('<i class="fa fa-comment-o"></i> ' + docComment).show();    
            } else {
                $("#rfcComment").hide();    
            }

            // update modal content
            $("#documentMDModal .s_bdseqno").html(data["Document ID"]);
            $("#documentMDModal .s_bdname").html(data["Name"]);
            $("#documentMDModal .s_bddoctype").html(data["Type"]);
            $("#documentMDModal .s_bdrfcno").html(data["RFC"]);
            $("#documentMDModal .s_bderrata").html(data["Errata notes"].replace(/\n/g));
            $("#documentMDModal .s_bdediff").html(data["Errata diff"].replace(/\n/g));
            $("#documentMDModal .s_bdthstat").html(data["Testable requirements"]);
            $("#documentMDModal .s_bdcomment").html(data["Comment"].replace(/\n/g));
            $("#documentMDModal .s_bddstat").html(data["Status"]);
            $("#documentMDModal .s_bduser").html(data["This user"]);
            $("#documentMDModal .s_bdupdated").html(data["Updated"]);
            $("#documentMDModal .s_bdadded").html(data["Added"]);

            $("#documentMDModalEditable .s_bdseqno").html(data["Document ID"]);
            $("#documentMDModalEditable .s_bdname").val(data["Name"]);
            $("#documentMDModalEditable .s_bddoctype").val(data["Type"]);
            $("#documentMDModalEditable .s_bdrfcno").val(data["RFC"]);
            $("#documentMDModalEditable .s_bderrata").val(data["Errata notes"]);
            $("#documentMDModalEditable .s_bdediff").val(data["Errata diff"]);
            $("#documentMDModalEditable .s_bdthstat").val(data["Testable requirements"]);
            $("#documentMDModalEditable .s_bdcomment").val(data["Comment"]);
            $("#documentMDModalEditable .s_bddstat").val(data["Status"]);
            $("#documentMDModalEditable .s_bduser").html(data["This user"]);
            $("#documentMDModalEditable .s_bdupdated").html(data["Updated"]);
            $("#documentMDModalEditable .s_bdadded").html(data["Added"]);

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }

    });
}

// submit change of document metadata
function submitRequirementMD() {

    // get values from form
    var rstart = $('#requirementMDModalEditable .modal-body .rstart').val();
    var rlength = $('#requirementMDModalEditable .modal-body .rlength').val();
    var rtext = $('#requirementMDModalEditable .modal-body .rtext').val();
    var rtype = $('#requirementMDModalEditable .modal-body .rtype').val();
    var rcomment = $('#requirementMDModalEditable .modal-body .rcomment').val();
    var rreplacedby = $('#requirementMDModalEditable .modal-body .rreplacedby').val();
    var rsameas = $('#requirementMDModalEditable .modal-body .rsameas').val();

    // # C: { "Command": "Requirement edit", "Requirement ID": c_rseqno, "Base document": c_bdseqno,
    // #       "Start": c_rstart, "Length": c_rlength, "Text": c_rtext, "Type": c_rtype, "Comment": c_rcomment,
    // #       "Replaced by": c_rreplacedby }
    // #    -- All fields are are required
    // # S: { "Command": "Requirement edit", "Requirement ID": s_rseqno, "Base document": s_bdseqno, "Start": s_rstart,
    // #      "Length": s_rlength, "Text": s_rtext, "Type": s_rtype, "Comment": s_rcomment, "Replaced by": s_rreplacedby, 
    // #      "This user": s_ruser, "Updated": s_rupdated, "Added": s_radded, "Return": returnval }

    issueAjax({ 
        Command : "Requirement edit", 
        "Requirement ID": baseRequirementID, 
        "Base document": baseDocumentID, 
        "Start": rstart, 
        "Length": rlength, 
        "Text": rtext, 
        "Type": rtype,
        "Comment": rcomment, 
        "Replaced by": rreplacedby,
        "Same as": rsameas 
    }, function(data) {

        writeLog("submitRequirementMDDone", data);

        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // update requirement text
            $(".requirementText").text(data["Text"]);
            if (data['Comment'] !== "") {
                $(".requirementComment").text('<i class="fa fa-comment-o"></i> ' + replaceLBBR(data["Comment"])).show();
            } else {
                $(".requirementComment").hide();
            }

            // update same as
            if (data["Same as"] > 0) {
                $(".requirementSameAs").text("Same as " + data["Same as"]).show();
            } else {
                $(".requirementSameAs").text("").hide();
            }

            // update modal content
            $("#requirementMDModal .rseqno").html(data["Requirement"]);
            $("#requirementMDModal .bdseqno").html(data["Base document"]);
            $("#requirementMDModal .rstart").html(data["Start"]);
            $("#requirementMDModal .rlength").html(data["Length"]);
            $("#requirementMDModal .rtext").html(replaceLBBR(data["Text"]));
            $("#requirementMDModal .rcomment").html(replaceLBBR(data["Comment"]));
            $("#requirementMDModal .rreplacedby").html(data["Replaced by"]);
            $("#requirementMDModal .ruser").html(data["This user"]);
            $("#requirementMDModal .rupdated").html(data["Updated"]);
            $("#requirementMDModal .radded").html(data["Added"]);
            $("#requirementMDModal .rtype").html(data["Type"]);
            $("#requirementMDModal .rsameas").html(data["Same as"]);

            $("#requirementMDModalEditable .rseqno").html(data["Requirement"]);
            $("#requirementMDModalEditable .bdseqno").val(data["Base document"]);
            $("#requirementMDModalEditable .rstart").val(data["Start"]);
            $("#requirementMDModalEditable .rlength").val(data["Length"]);
            $("#requirementMDModalEditable .rtext").val(data["Text"]);
            $("#requirementMDModalEditable .rcomment").val(data["Comment"]);
            $("#requirementMDModalEditable .rreplacedby").val(data["Replaced by"]);
            $("#requirementMDModalEditable .ruser").html(data["This user"]);
            $("#requirementMDModalEditable .rupdated").html(data["Updated"]);
            $("#requirementMDModalEditable .radded").html(data["Added"]);
            $("#requirementMDModalEditable .rtype").val(data["Type"]);
            $("#requirementMDModalEditable .rsameas").val(data["Same as"]);

            lastRequirementAdded = data["Requirement"];

            // save the scroll position of the left pane
            scrollTop = $(".rfcContents").scrollTop();

            // let's now get the document again to get the revised range, if it changed
            initDocument();

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }

    });
}

// submit change of test metadata
function submitTestMD() {

    // get values from form
    var s_ttext = $('#testMDModalEditable .modal-body .s_ttext').html();
    var s_tdut = $('#testMDModalEditable .modal-body .s_tdut').val();
    var s_toutcome = $('#testMDModalEditable .modal-body .s_toutcome').val();
    var s_tneg = $('#testMDModalEditable .modal-body .s_tneg').val();
    var s_tcomment = $('#testMDModalEditable .modal-body .s_tcomment').val();
    var s_tmasterfile = $('#testMDModalEditable .modal-body .s_tmasterfile').val();
    var s_tlscommand = $('#testMDModalEditable .modal-body .s_tlscommand').val();
    var s_treplacedby = $('#testMDModalEditable .modal-body .s_treplacedby').val();
    var s_tsameas = $('#testMDModalEditable .modal-body .s_tsameas').val();
    var thisTestID = $("#testMDModal .s_tseqno").text();

    if (s_treplacedby === "") {
        s_treplacedby = null;
    }

	// 	# C: { "Command": "Test edit", "Test ID": c_tseqno, "Base requirement": c_rseqno, "Same as": c_tsameas,
	// 	#      "Text": c_ttext, "DUT": c_tdut, "LS command": c_tlscommand, "Outcome": c_toutcome, "Neg": c_tneg, "Comment": c_tcomment, 
	// 	#	     "Master file entry": c_tmasterfile, "Replaced by": c_treplacedby }
	// 	#    -- All fields are are required
	// 	# S: { "Command": "Test edit", "Test ID": s_tseqno, "Base requirement": s_rseqno, "Same as": s_tsameas,
	// 	#      "Text": s_ttext, "DUT": s_tdut, "LS command": s_tlscommand, "Outcome": s_toutcome, "Neg": s_tneg, "Comment": s_tcomment,
	// 	#      "Master file entry": c_smasterfile, "Replaced by": s_treplacedby, "This user": s_tuser, "Updated": s_tupdated,
	// 	#      "Added": s_tadded, "Return": returnval }

    issueAjax({ 
        Command : "Test edit", 
        "Test ID": thisTestID, 
        "Base requirement": baseRequirementID, 
        "Same as": s_tsameas,
        "Text": s_ttext, 
        "DUT": s_tdut, 
        "LS command": s_tlscommand, 
        "Outcome": s_toutcome, 
        "Neg": s_tneg, 
        "Comment": s_tcomment, 
        "Master file entry": s_tmasterfile, 
        "Replaced by": s_treplacedby
    }, function(data) {

        writeLog("submitTestMDDone", data);

        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // update test text
            var testName = "Test " + data["Test ID"];
            $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testText").html(data["Text"]);
            if ((data["LS command"] !== "") && (data["LS command"] !== null)) {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testLSCommand").html("LS Command: " + replaceLBBR(data["LS command"])).show();
            } else {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testLSCommand").hide();
            }
            if (data["Outcome"] !== "") {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testOutcome").html(replaceLBBR(data["Outcome"])).show();
            } else {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testOutcome").hide();
            }
            if (data["Neg"] !== "None") {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testNeg").html(replaceLBBR(data["Neg"])).show();
            } else {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testNeg").hide();
            }
            if (data["Comment"] !== "") {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testComment").html('<i class="fa fa-comment-o"></i> ' + replaceLBBR(data["Comment"])).show();
            } else {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testComment").hide();
            }
            if (data["Master file entry"] !== "") {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testMasterFile").html("Master file entry: " + replaceLBBR(data["Master file entry"])).show();
            } else {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testMasterFile").hide();
            }
            $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testDUT").html(data["DUT"]);

            // same as?
            if (data["Same as"] > 0) {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testSameAs").html("Same as " + data["Same as"]).show();
            } else {
                $("#reqDiv").find("h2:contains(" + testName + ")").parent().find(".testSameAs").hide();
            }

            // update modal content
            $("#testMDModal .s_tseqno").html(data["Test ID"]);
            $("#testMDModal .s_rseqno").html(data["Base requirement"]);
            $("#testMDModal .s_tsameas").html(data["Same as"]);
            $("#testMDModal .s_ttext").html(data["Text"]);
            $("#testMDModal .s_tdut").html(data["DUT"]);
            $("#testMDModal .s_toutcome").html(replaceLBBR(data["Outcome"]));
            $("#testMDModal .s_tneg").html(replaceLBBR(data["Neg"]));
            $("#testMDModal .s_tcomment").html(replaceLBBR(data["Comment"]));
            $("#testMDModal .s_tmasterfile").html(replaceLBBR(data["Master file entry"]));
            $("#testMDModal .s_tlscommand").html(replaceLBBR(data["LS command"]));
            $("#testMDModal .s_treplacedby").html(data["Replaced by"]);
            $("#testMDModal .s_tuser").html(data["This user"]);
            $("#testMDModal .s_tupdated").html(data["Updated"]);
            $("#testMDModal .s_tadded").html(data["Added"]);

            $("#testMDModalEditable .s_tseqno").html(data["Test ID"]);
            $("#testMDModalEditable .s_rseqno").val(data["Base requirement"]);
            $("#testMDModalEditable .s_tsameas").val(data["Same as"]);
            $("#testMDModalEditable .s_ttext").html(data["Text"]);
            $("#testMDModalEditable .s_tdut").val(data["DUT"]);
            $("#testMDModalEditable .s_toutcome").val(data["Outcome"]);
            $("#testMDModalEditable .s_tneg").val(data["Neg"]);
            $("#testMDModalEditable .s_tcomment").val(data["Comment"]);
            $("#testMDModalEditable .s_tmasterfile").val(data["Master file entry"]);
            $("#testMDModalEditable .s_tlscommand").val(data["LS command"]);
            $("#testMDModalEditable .s_treplacedby").val(data["Replaced by"]);
            $("#testMDModalEditable .s_tuser").html(data["This user"]);
            $("#testMDModalEditable .s_tupdated").html(data["Updated"]);
            $("#testMDModalEditable .s_tadded").html(data["Added"]);

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }

    });
}

// delete the requirement
function submitRequirementDelete() {

    // # C: { "Command": "Requirement delete", "Requirement ID": c_rseqno }
    // # S: { "Command": "Requirement delete", "Requirement ID": s_rseqno, "Return": returnval }

    issueAjax({ 
        Command : "Requirement delete", 
        "Requirement ID": baseRequirementID
    }, function(data) {

        writeLog("submitRequirementDeleteDone", data);

        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // hide the requirement DIV
            $(".reqDetail").hide();
            
            // remove any tests from the display
            $(".testDetail").remove();

            // save the scroll position of the left pane
            scrollTop = $(".rfcContents").scrollTop();
            // scrollTop = 0; // uncomment if you want to scroll to next requirement instead

            // let's now get the document again to get the revised ranges (this one now missing)
            initDocument();

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }

    });

}

// delete the test
function submitTestDelete() {

    // # C: { "Command": "Test delete", "Test ID": c_tseqno }
    // # S: { "Command": "Test delete", "Test ID": s_tseqno, "Return": returnval }

    issueAjax({ 
        Command : "Test delete", 
        "Test ID": baseTestID
    }, function(data) {

        writeLog("submitTestDeleteDone", data);

        var returnVal = data.Return[0];
        var returnErr = data.Return[1];

        if (returnVal) {

            // find and remove the test DIV
            $("#test" + baseTestID).closest(".testDetail").slideUp("slow", function() {
                $("#test" + baseTestID).closest(".testDetail").remove();
            });

        } else {
            standardErrorModalAjaxReturn(returnErr);
        }

    });
}

// submit the add test form
function submitAddTest() {
    // get values from form
    var c_rseqno = $('#addTestModal .modal-body .c_rseqno').val();
    var c_tsameas = $('#addTestModal .modal-body .c_tsameas').val();
    var c_ttext = $('#addTestModal .modal-body .c_ttext').html();
    var c_tdut = $('#addTestModal .modal-body .c_tdut').val();
    var c_toutcome = $('#addTestModal .modal-body .c_toutcome').val();
    var c_tneg = $('#addTestModal .modal-body .c_tneg').val();
    var c_tcomment = $('#addTestModal .modal-body .c_tcomment').val();
    var c_tmasterfile = $('#addTestModal .modal-body .c_tmasterfile').val();
    var c_tlscommand = $('#addTestModal .modal-body .c_tlscommand').val();

    issueAjax({ Command : "Test new", "Base requirement": c_rseqno, "Same as": c_tsameas, "Text": c_ttext, "DUT": c_tdut, "LS command": c_tlscommand, "Outcome": c_toutcome, "Neg": c_tneg, "Comment": c_tcomment, "Master file entry": c_tmasterfile }, function(data) {
        writeLog("submitAddTestDone", data);

        var testString = "";
        testString += '<div class="testDetail">';
        testString += '<h2>Test ' + data["Test ID"] + ' <div class="testDUT">' + data["DUT"] + '</div>';
        if (data["Same as"] > 0) {
            testString += '<div class="testSameAs">Same as ' + data["Same as"] + '</div>';
        } else {
            testString += '<div class="testSameAs" style="display: none"></div>';
        }
        testString += ' <a id="test' + data["Test ID"] + '" class="btn btn-xxs btn-danger pull-right testDeleteLink">delete</a>';
        testString += ' <a id="test' + data["Test ID"] + '" class="btn btn-xxs btn-default pull-right testMDLink" style="margin-right: 5px">metadata</a></h2>';
        testString += '<div class="testText"><p>' + data["Text"] + '</p></div>';
        if ((data["LS command"] !== "") && (data["LS command"] !== null)) {
            testString += '<div class="testLSCommand">LS Command: ' + replaceLBBR(data["LS command"]) + '</div>';
        } else {
            testString += '<div class="testLSCommand" style="display: none"></div>';
        }
        if (data["Outcome"] !== "") {
            testString += '<div class="testOutcome">' + replaceLBBR(data["Outcome"]) + '</div>';
        } else {
            testString += '<div class="testOutcome" style="display: none"></div>';
        }
        if (data["Neg"] !== "None") {
            testString += '<div class="testNeg">' + replaceLBBR(data["Neg"]) + '</div>';
        } else {
            testString += '<div class="testNeg" style="display: none"></div>';
        }
        if (data["Comment"] !== "") {
            testString += '<div class="testComment">' + '<i class="fa fa-comment-o"></i> ' + replaceLBBR(data["Comment"]) + '</div>';
        } else {
            testString += '<div class="testComment" style="display: none"></div>';
        }
        if (data["Master file entry"] !== "") {
            testString += '<div class="testMasterFile">Master file entry: ' + replaceLBBR(data["Master file entry"]) + '</div>';
        } else {
            testString += '<div class="testMasterFile" style="display: none"></div>';
        }
        testString += '</div>';
        
        $(".rfcReqTests").append(testString);

        $(".testMDLink").unbind("click");
        $(".testMDLink").click(function() {
            testMDLinkClick($(this));
        }); // end testMDLink click

        $(".testDeleteLink").unbind("click");
        $(".testDeleteLink").click(function() {
            testDeleteLinkClick($(this));
        }); // end testDeleteLink click

        // clear values for next time
        $('#addTestModal .modal-body .c_ttext').html("");
        $('#addTestModal .modal-body .c_tdut').val("Client");
        $('#addTestModal .modal-body .c_toutcome').val("");
        $('#addTestModal .modal-body .c_tneg').val("");
        $('#addTestModal .modal-body .c_tcomment').val("");
        $('#addTestModal .modal-body .c_tmasterfile').val("");
        $('#addTestModal .modal-body .c_tlscommand').val("");
    });
}

function getListOfDocumentsDone(data) {

    writeLog("getListOfDocumentsDone", data);

    var returnVal = data.Return[0];
    var returnErr = data.Return[1];
    var documentList = data.Documents;
    var sortedDocuments = [];
    var username = data['HTTP user'];

    // set username in header
    $(".username").text(username);

    if (returnVal) {

        // convert to array
        $.each(documentList, function(index, element) {
            sortedDocuments.push([index, element]);
        });

        // sort a list by document name
        sortedDocuments.sort(function(a, b) {
            var nameA=a[1]["DocName"].toLowerCase(), nameB=b[1]["DocName"].toLowerCase();
             if (nameA < nameB) {//sort string ascending
              return -1; 
             } else if (nameA > nameB) {
              return 1;
             } else {
             return 0; 
             }
        });

        // input into table
        var status = "";
        $.each(sortedDocuments, function(index) {
			docname = sortedDocuments[index][1]["DocName"]
			seqno = sortedDocuments[index][1]["SeqNo"]
            docnamestring = "<td><a href='document.htm?id=" + seqno + "'>" + docname + "</a></td>"
            seqnostring = "<td class='text-center'>" + seqno + "</td>"
            totalreqsstring = "<td class='text-center'>" + sortedDocuments[index][1]["TotalReqs"] + "</td>"
            testablereqsstring = "<td class='text-center'>" + sortedDocuments[index][1]["TestableReqs"] + "</td>"
            totaltestsstring = "<td class='text-center'>" + sortedDocuments[index][1]["TotalTests"] + "</td>"
            // status = sortedDocuments[index][1]["Status"];
			// dateastimestamp = sortedDocuments[index][1]["DateAsTimestamp"]
			// dateastext = sortedDocuments[index][1]["DateAsText"]
            // Earlier: $('#rfcListing > tbody:last').append("<tr><td><a href='document.htm?id=" + sortedDocuments[index][0] + "'>" + docname + "</a></td><td data-sort-value='" + dateastimestamp + "'>" + dateastext + "</td><td class='text-center'>" + seqno + "</td><td>" + status + "</td></tr>");
            $('#rfcListing > tbody:last').append("<tr>" + docnamestring + seqnostring + totalreqsstring + testablereqsstring + totaltestsstring + "</tr>");
        });

        // sort it
        $("#rfcListing").stupidtable();

    } else {
        // trigger modal with returnErr
        standardErrorModalAjaxReturn(returnErr);
    }
    
    // documents loaded, handle filtering
    // set up filtering function for main RFC listing (documents)
    var $rows = $('#rfcListing tbody tr');
    $('#search').keyup(function() {
        var val = '^(?=.*\\b' + $.trim($(this).val()).split(/\s+/).join('\\b)(?=.*\\b') + ').*$',
            reg = new RegExp(val, 'i'),
            text;
        if (val) { $("#resetSearch").fadeIn(); }
        $rows.show().filter(function() {
            text = $(this).text().replace(/\s+/g, ' ');
            return !reg.test(text);
        }).hide();
    });
}

// load initial list of documents into main page
function getListOfDocuments() {
    issueAjax({ Command : "Get list of documents" }, getListOfDocumentsDone);

    // get and set the user's access level
    issueAjax({ Command : "Get user access level" }, getUserAccessLevelDone);
}

// admin new document
function adminNewDocumentSubmit() {

    // # C: { "Command": "Document new", "Name": c_bdname, "Type: c_bddoctype, "RFC": c_bdrfcno, "Text": c_bdtext,
    // #      "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat,
    // #      "Comment": c_bdcomment, "Status": c_bddstat }
    // #    -- "Name" and "Text" are required
    // # S: { "Command": "Document new", "Document ID": s_bdseqno, "Name": c_bdname, "Type: c_bddoctype, "RFC": c_bdrfcno, 
    // #      "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat,
    // #      "Comment": c_bdcomment, "Status": c_bddstat }

    // get values from form
    var c_bdname = $('#adminNewDocument .modal-body .c_bdname').val();
    var c_bddoctype = $('#adminNewDocument .modal-body .c_bddoctype').val();
    var c_bdrfcno = $('#adminNewDocument .modal-body .c_bdrfcno').val();
    var c_bdtext = $('#adminNewDocument .modal-body .c_bdtext').val(); // parsed on client side after document selected
    var c_bderrata = $('#adminNewDocument .modal-body .c_bderrata').val();
    var c_bdediff = $('#adminNewDocument .modal-body .c_bdediff').val();
    var c_bdthstat = $('#adminNewDocument .modal-body .c_bdthstat').val();
    var c_bdcomment = $('#adminNewDocument .modal-body .c_bdcomment').val();
    var c_bddstat = $('#adminNewDocument .modal-body .c_bddstat').val();

    if (c_bdtext === "") {
        // oh no, you need to add some text!
        $("#adminNewDocument .alert-select-document").show();
        setTimeout(function(){$("#adminNewDocument").modal("show");}, 1000);
    } else {
        $("#adminNewDocument .alert-select-document").hide();
        issueAjax({ Command : "Document new", "Name": c_bdname, "Type": c_bddoctype, "RFC": c_bdrfcno, "Text": c_bdtext, "Errata notes": c_bderrata, "Errata diff": c_bdediff, "Testable requirements": c_bdthstat, "Comment": c_bdcomment, "Status": c_bddstat }, function(data) {
            writeLog("adminNewDocumentDone", data);

            var returnVal = data.Return[0];
            var returnErr = data.Return[1];

            if (returnVal) {
                // todo: anything to do here?
                var newDocID = data["Document ID"];
                location.href = "/document.htm?id=" + newDocID;
            } else {
                standardErrorModalAjaxReturn(returnErr);
            }
        });
    }
}

// file selection
function handleFileSelect(evt) {
    var files = evt.target.files; // FileList object

    // files is a FileList of File objects. List some properties.
    var output = [];
    for (var i = 0, f; f = files[i]; i++) {
    
        var reader = new FileReader();

        // Closure to capture the file information.
        reader.onload = (function(theFile) {
            return function(e) {
                $("#adminNewDocumentContent").val(e.target.result);
            };
        })(f);
        
        reader.readAsText(f);
    } 
}

// initialize variables used to resized the center handle
var isResizing = false,
    lastDownX = 0;

// utility function to only fire a function after a certain timeout (ie. resize)
function debouncer( func , timeout ) {
    var timeoutID;
    return function () {
        var scope = this, args = arguments;
        clearTimeout( timeoutID );
        timeoutID = setTimeout( function () {
            func.apply(scope, Array.prototype.slice.call(args));
        }, timeout);
    };
}

// sets the scroll height of the left and right column to have it scroll independently of the browser scrollbar
function setScrollHeight() {
    $(".rfcContents").css("max-height", $(window).height() - $(".rfcContents").offset().top);
    if ($(".rfcReqTests").length) {
        $(".rfcReqTests").css("max-height", $(window).height() - $(".rfcReqTests").offset().top);
    }
}

// get the selected HTML from the left panel and return to calling function
function getSelectionHTML() {
    var range;
    if (document.selection && document.selection.createRange) {
        range = document.selection.createRange();
        return range.htmlText;
    }
    else if (window.getSelection) {
        var selection = window.getSelection();
        if (selection.rangeCount > 0) {
            range = selection.getRangeAt(0);
            var clonedSelection = range.cloneContents();
            var div = document.createElement('div');
            div.appendChild(clonedSelection);
            return div.innerHTML;
        }
        else {
            return '';
        }
    }
    else {
        return '';
    }
}

// on document load, run once
// set up click and other event handlers
$(function() {
    // references to panels for dragging middle handle
    var container = $('#panelWrapper'),
        left = $('#panelLeft'),
        right = $('#panelRight'),
        handle = $('#panelHandle');

    // when mouse clicks on handle, set resizing to true
    handle.on('mousedown', function (e) {
        isResizing = true;
        lastDownX = e.clientX;
    });

    // if resizing, track mouse movements and adjust left/right panels accordingly
    $(document).on('mousemove', function (e) {
        if (!isResizing) {
            return; // not resizing, so bail
        }
        var offsetRight = container.width() - (e.clientX - container.offset().left);
        left.css('right', offsetRight);
        right.css('width', offsetRight);
    }).on('mouseup', function () {
        isResizing = false; // stop resizing
    });

    // set initial width halfway
    var initialLeft = 650;
    var windowWidth = $(window).width();
    $("#panelWrapper #panelRight").width(windowWidth-initialLeft);
    left.css('right', windowWidth-initialLeft);
    right.css('width', windowWidth-initialLeft);

    // set initial height of left panel for scrolling
    setScrollHeight();

    // on browser resize, reset scroll height of left panel for scrolling
    $(window).resize(debouncer(function() {
        setScrollHeight();
    }));

    // when .modal opened, set content-body height based on browser height;
    // 200 is appx height of modal padding, modal title and button bar
    $(".modal").on("show.bs.modal", function() {
        $(this).find(".modal-body").css("max-height", $(window).height() - 200);
    });

    // for add test modal, populate requirement ID before showing
    $("#addTestButton").click(function() {

        if (userCanMarkup) {
            if (currentMode === "markup") {
                $("#addTestModal .c_rseqno").val(baseRequirementID);
                $('#addTestModal').modal('show');
            } else {
                invokeErrorModal("Error", "Please enter markup mode before choosing this action.");
            }
        } else {
            // if user cannot go into markup, show error
            // set toggle state of buttons for view state
            invokeErrorModal("Error", "Only users authorized to enter markup mode can take this action.");
        }

    });

    // if user has searched for an RFC, the reset button appears. When clicked, will reset search box
    $("#resetSearch").click(function() {
        $("#search").val("").keyup();
        $(this).fadeOut();
    });

    // when user clicks a singleSpan, function should populate right column
    $("pre span.singleSpan").click(function() {
        alert("This should populate requirements and tests for ID " + $(this).attr('id'));
        // todo: Ajax and display show right column for this element
    });

    // has the user made a text selection in the left column?
    // show makeRequirement div if so, otherwise hide
    $(".rfcContents").mouseup(function() {
        var text = getSelectionHTML();
        if (text !== "") {
            // valid text selection, so show make requirement button
            $("#makeRequirement").fadeIn();
        } else {
            $("#makeRequirement").fadeOut();
        }
    });

    // if user didn't want to make selection, de-select text and remove make requirement button
    $("#cancelSelection").click(function() {
        document.getSelection().removeAllRanges();
        $("#makeRequirement").fadeOut();
    });

    // if the user wants to make selected text a requirement, get selected text and show make requirement modal
    $("#makeRequirementButton").click(function() {

        if (userCanMarkup) {
            if (currentMode === "markup") {

                // get selected HTML, strip out span and close span tags
                var text = getSelectionHTML().replace(/<\/?span[^>]*>/g,"");

                // strip off any opening or closing tag to account for terminal tags that the browser inserts for partial selections
                var compareText = text.replace(/^<\S+>/,"");            // replace opening tag
                    compareText = compareText.replace(/<\/\S+>$/,"");   // replace trailing tag

                // if we stripped tags, get the offset to substract for the length later
                var offset = text.length - compareText.length;

                // find the text in the entire left side, get index of location
                // strip out span and close span tags to identify range selected
                var compareString = $(".rfcContents").html().replace(/<\/?span[^>]*>/g,"");
                
                // get the start location in the stripped string
                var startLocation = compareString.indexOf(compareText);

                // get length of text
                var textLength = compareText.length;

                // console.log("making a requirement for start " + startLocation + " with length " + textLength);               

                $('#makeRequirementModal .modal-body .s_bdseqno').val(baseDocumentID);
                $('#makeRequirementModal .modal-body .s_bdname').val(baseDocumentName);
                $('#makeRequirementModal .modal-body .s_rstart').val(startLocation);
                $('#makeRequirementModal .modal-body .s_rlength').val(textLength);
                $('#makeRequirementModal .modal-body .s_rtext').val(text);

                // blank other fields
                $('#makeRequirementModal .modal-body .s_rtype').val("Testable");
                $('#makeRequirementModal .modal-body .s_rcomment').val("");
                $('#makeRequirementModal .modal-body .s_rreplacedby').val("");
                $('#makeRequirementModal .modal-body .s_rsameas').val("");

                $('#makeRequirementModal').modal('show');
            } else {
                invokeErrorModal("Error", "Please enter markup mode and select some text before choosing this action.");
            }
        } else {
            // if user cannot go into markup, show error
            // set toggle state of buttons for view state
            invokeErrorModal("Error", "Only users authorized to enter markup mode can take this action.");
        }
        document.getSelection().removeAllRanges();
        $("#makeRequirement").fadeOut();
    });

    $("#makeRequirementModalSubmit").click(function() {
        submitMakeRequirement();
    });

    $("#addTestModalSubmit").click(function() {
        submitAddTest();
    });

    $("#requirementDeleteModalSubmit").click(function() {
        submitRequirementDelete();
    });

    $("#testDeleteModalSubmit").click(function() {
        submitTestDelete();
    });

    $("#documentMDModalEditableSubmit").click(function() {
        submitDocumentMD();
    });

    $("#requirementMDModalEditableSubmit").click(function() {
        submitRequirementMD();
    });

    $("#adminNewDocumentSubmit").click(function() {
        adminNewDocumentSubmit();
    });

    $("#testMDModalEditableSubmit").click(function() {
        submitTestMD();
    });

    $(".modeSelector button").click(function() {
        switchModes($(this));
    });

    $(".admin_button").click(function() {
        switch($(this).attr("id")) {
            case "admin_new_document":
                admin_new_document();
                break;
            case "admin_download_full_test_plan":
                admin_download_full_test_plan();
                break;
            case "admin_download_testable_only_test_plan":
                admin_download_testable_only_test_plan();
                break;
            case "admin_download_db_json":
                admin_download_db_json();
                break;
            case "admin_help":
                admin_help();
                break;
        }
    });

    $(document).keyup(function(event) {
        var thisEvent = event || window.event;
        var offsetA = 0;
        var offsetB = 0;
        var modalShown = $('.modal').hasClass('in');

        if (thisEvent.which === 27 || thisEvent.keyCode === 27) {
            // escape key pressed
            $("#cancelSelection:visible").click(); // cancel
            $(".modal").modal('hide'); // close any visible modals on escape
            return false;
        } else if (thisEvent.which === 13 || thisEvent.keyCode === 13) {
            // enter key pressed
            $("#makeRequirementButton:visible").click(); // make requirement
            return false;
        } else if ((thisEvent.which === 38) && !modalShown) {
			// up arrow pressed
			if (lastRequirementArrow > 1) {
			   lastRequirementArrow--;
			}
            offsetA = $(".singleSpan" + lastRequirementArrow).offset();
			offsetB = offsetA.top - 175 + $(".rfcContents").scrollTop();
			$(".rfcContents").scrollTop(offsetB);
            $(".singleSpan" + lastRequirementArrow).click();
			return false;
     	} else if ((thisEvent.which === 40) && !modalShown) {
			// down arrow pressed
			if (lastRequirementArrow < totalRequirements) {
			   lastRequirementArrow++;
			}
			offsetA = $(".singleSpan" + lastRequirementArrow).offset();
			offsetB = offsetA.top - 175 + $(".rfcContents").scrollTop();
			$(".rfcContents").scrollTop(offsetB);
            $(".singleSpan" + lastRequirementArrow).click();
			return false;
     	}
    });

    // listen for file load
    document.getElementById('exampleInputFile').addEventListener('change', handleFileSelect, false);

    // Test plan download helper - clear URL
    $('#downloadFullTestPlan').on('hide.bs.modal', function() {
        setTimeout(function(){$("#dloadFullTestPlan").attr("href", "#").attr("download", "DNSConformanceFullTestPlan.html");}, 3000);
    });

    // Test plan download helper - click handler
    $("#dloadFullTestPlan").click(function() {
        $("#downloadFullTestPlan").modal("hide");
    });

    // Test plan download helper - change file name
    $(".dloadFullTestPlanFileName").change(function() {
        $("#dloadFullTestPlan").attr("download", $(this).val());
    });
            
    // Test plan download helper - clear URL
    $('#downloadTestableOnlyTestPlan').on('hide.bs.modal', function() {
        setTimeout(function(){$("#dloadTestableOnlyTestPlan").attr("href", "#").attr("download", "DNSConformanceTestableOnlyTestPlan.html");}, 3000);
    });

    // Test plan download helper - click handler
    $("#dloadTestableOnlyTestPlan").click(function() {
        $("#downloadTestableOnlyTestPlan").modal("hide");
    });

    // Test plan download helper - change file name
    $(".dloadTestableOnlyTestPlanFileName").change(function() {
        $("#dloadTestableOnlyTestPlan").attr("download", $(this).val());
    });
            
    // JSON download helper - clear URL
    $('#downloadJSON').on('hide.bs.modal', function() {
        setTimeout(function(){$("#dloadJSON").attr("href", "#").attr("download", "DNSConformanceDatabase.json");}, 3000);
    });

    // JSON download helper - click handler
    $("#dloadJSON").click(function() {
        $("#downloadJSON").modal("hide");
    });

    // JSON downloads helper - change file name
    $(".dloadJSONFileName").change(function() {
        $("#dloadJSON").attr("download", $(this).val());
    });
            
}); // end jQuery load
