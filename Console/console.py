#!/usr/bin/env python3
import sys
from bottle import request, route, get, post, run, hook, template, view, static_file, Request
from Entable import Entable
from conformdb import Conformdb
from itertools import compress,chain,cycle
from html import escape

'''
Console program for searching and bulk editing of the database.
'''

Request.MEMFILE_MAX = 1024*1024 # allow large requests

# Get the host name from the web server
# remote edit link, host name added dynamically along with whatever
# we're editing
rmtedit = "https://{0}:44317/document.htm?id={1}"

# Set up the database for editing
@hook('before_request')
def setup_request():
    user = request.environ.get('REMOTE_USER')
    if not user:
        user = "demo"
    request.db = Conformdb(user=user)
    userinfo = request.db.getuserinfo()
    if not userinfo[0]:
        print("Bogus userinfo",userinfo[1])
        return
    request.user = userinfo[1]['userwho']
    request.userpriv = userinfo[1]['userpriv'] or ""
    
# boilerplate toolbar at the top of each page
def boilerplate():
    here = request.path
    def bp(page, desc):
        if here == page:
            return "<li><a href=\"{}\" class=active>{}</a></li>\n".format(page,desc)
        else:
            return "<li><a href=\"{}\">{}</a></li>\n".format(page,desc)
    bo = "<ul id=tabnav>\n"
    bo += bp("/basedoc","Base Documents")
    bo += bp("/allreq","All Reqs")
    bo += bp("/req","Search Reqs")
    bo += bp("/alltest","All Tests")
    bo += bp("/scantest","Scan Tests")
    bo += bp("/test","Search Tests")
    bo += bp("/whacktest","Patch Tests")
    # bo += bp("/diff","Differences")
    bo += bp("/help","Help")
    bo += "</ul>\n<p align=right>Logged in as " + request.user
    if 'Edit' in request.userpriv:
        bo += " (Can edit)"
    bo += "</p>"
    return bo

# hack to return alternating v and w for tables
altvw = cycle("vw")

# clean up a number or None
def numornone(x):
    if isinstance(x, int):
        return x if x>0 else None       # zeros aren't interesting
    if x.isdigit():
        return int(x)
    return None

# string snippet for tables
# now does fuzzy wrapping too
def snip(s, sniplen=300, wrap=80):
    # sniplen is max length
    # wrap is wrap length
    fuzz = 20                           # wrap fuzziness

    if not isinstance(s, str):
        return "&nbsp;"
    if len(s) > sniplen:
        s = s[:sniplen] + "..."

    def dofuzz(chk):
        """ break a chunk into subchunks using fuzzy length
        """
        chl = []
        while len(chk) > wrap:
            p = chk.rfind(" ", wrap-fuzz,wrap)
            if p > 0:                   # break at a space
                chl.append(chk[:p])
                chk = chk[p+1:]
            else:                       # just break
                chl.append(chk[:wrap])
                chk = chk[wrap:]
        return chl + [chk]

    # break into lines, fuzzy break lines into chunks, make a single list of
    # the chunks, escape the chunks, combine into one blob.  Easy, eh?
    return "<br/>\n".join(map(escape, chain(*map(dofuzz,s.split("\n")))))

# start here
@get("/")
@view("homepage")
def startup():
    """ return n empty status page
    """
    return dict(boilerplate=boilerplate())

# Help text
@get("/help")
@view("help")
def help():
	helptext = '''The console is used for searching through the base documents,
	the requirements, and the tests in the database.
	It should not be needed in normal use of the the database, but might be handy
	for some mass-editing or searching.
	Most of the tables in the console have column headings that, when clicked,
	sort the rows of the table.
	<br><ul>
	<li>The <strong>Base Documents</strong> tab shows all the documents in the
	database, and allow the metadata for the document to be edited. The right column
	is used to open the document itself.</li>
	<li>The <strong>All Reqs</strong> tab lists the most interesting data for all
	of the requirements.</li>
	<li>The <strong>Search Reqs</strong> tab lists all the documents and lets you easily see
	all the requirements for each document.</li>
	<li>The <strong>All Tests</strong> tab lists the most interesting data for all
	of the tests in the database.</li>
	<li>The <strong>Scan Tests</strong> tab lets you see all the tests for a particular
	type of DUT.</li>
	<li>The <strong>Search Tests</strong> tab lists all the documents and lets you easily see
	all the tests for each document.</li>
	<li>The <strong>Patch Tests</strong> tab lets you perform a universal search-and-replace
	for the tests in the database. Clearly, this can be a bit dangerous because patches cannot
	be undone.</li>
	</ul>
	<br><hr><br>
	<pre>
	Copyright (c) 2015, Standcore LLC
	All rights reserved.

	Redistribution and use in source and binary forms, with or without modification,
	are permitted provided that the following conditions are met:

	1. Redistributions of source code must retain the above copyright notice, this
	list of conditions, and the following disclaimer.

	2. Redistributions in binary form must reproduce the above copyright notice,
	this list of conditions, and the following disclaimer in the documentation and/or
	other materials provided with the distribution.

	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
	ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
	WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
	DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
	ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
	(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
	LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
	ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
	SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
	</pre>
	'''
	return dict(boilerplate=boilerplate(),helptext=helptext)

### basedoc
@get("/basedoc")
@view("basedoc")
def basedoc(namepat=None):
    """ return a table of base docs
        optional pattern limits them
    """
    bdlist = request.db.listbasedoc(name=namepat)
    if not bdlist[0]:
        print("listbasedoc failed")

    # sort appropriately 
    if 's' in request.query:
        sortfns = (
            lambda d: d['bdrfcno'] or -1,
            lambda d: d['bddoctype'],
            lambda d: d['bddstat'],
            lambda d: d['bdthstat'],
            lambda d: d['bdname']
        )
        bdlist[1].sort(key=sortfns[int(request.query.s)])

    doctable = "\n".join(
        [ """<tr><td class={vw}><a href="/bdedit/{seqno}" target="_blank">{rfcno}</a></td>
            <td class={vw}>{doctype}</td>
            <td class={vw}>{dstat}</td>
            <td class={vw}>{thstat}</td>
            <td class={vw}>{name}</td>
            <td class={vw}><a href="{rmtedit}" target="_blank">{rfcno}</a></td>
            </tr>""".format(vw= vw, rfcno=d['bdrfcno'],seqno=d['bdseqno'],doctype=d['bddoctype'],
                dstat=d['bddstat'],thstat=d['bdthstat'],name=d['bdname'],
                rmtedit=rmtedit.format(request.urlparts.hostname, d['bdseqno']))
                for vw, d in zip(altvw, bdlist[1])
            ])
    return dict(boilerplate=boilerplate(),doctable=doctable, url=request.path)

@get("/bdedit/<seqno:int>")
@view("bdedit")
def bdedit(seqno):
    bdr = request.db.getbasedoc(seqno=seqno)
    (ret, bdschema) = request.db.getbasedocschema()
    if not ret or not bdr[0]:
        return failpage("no such document {}: {}".format(seqno, bdr[1]))
    basedoc = bdr[1]
    return dict(docname=basedoc['bdname'], docno=basedoc['bdseqno'], boilerplate=boilerplate(),
        doctable=Entable('bdedit.csv',defs=basedoc).tedit(schema=bdschema))

@post("/bdedit/<seqno:int>")
@view("bdedit")
def dobdedit(seqno):
    doit = request.db.updatebasedoc(seqno=int(seqno),
        name=request.forms.bdname, rfcno=numornone(request.forms.bdrfcno),
            text=request.forms.bdtext, doctype=request.forms.bddoctype,
            errata=request.forms.bderrata, ediff=request.forms.bdediff, thstat=request.forms.bdthstat,
            comment=request.forms.bdcomment, dstat=request.forms.bddstat)
    if not doit[0]:
        return failpage(doit[1])
    return bdedit(seqno)

### requirements
@get("/req")
@view("req")
def req():
    """ return a table of requirements per base doc
    """
    bdlist = request.db.listbasedoc()
    if not bdlist[0]:
        print("listbasedoc failed")
    # find out how many requirements each one has
    for bd in bdlist[1]:
        reqs = request.db.listrequirement(bd['bdseqno'])
        if not reqs[0]:
            return failpage(reqs[1])
        bd['nreqs'] = len(reqs[1])

    # squeeze out the ones with no reqs and make the table
    reqtable = "\n".join(
        [ """<tr><td class={vw}><a href="/req/{seqno}">{nreqs}</a></td>
            <td class={vw}><a href="/bdedit/{seqno}" target="_blank">{rfcno}</a></td>
            <td class={vw}>{doctype}</td>
            <td class={vw}>{dstat}</td>
            <td class={vw}>{name}</td></tr>""".format(vw=vw,
              nreqs=d['nreqs'],seqno=d['bdseqno'],rfcno=d['bdrfcno'],doctype=d['bddoctype'],
              dstat=d['bddstat'],name=d['bdname'])
                for vw, d in zip(altvw, compress(bdlist[1], map(lambda bd: bd['nreqs'], bdlist[1])))
            ])

    return dict(boilerplate=boilerplate(),reqtable=reqtable)

@get("/allreq")
def allreq():
    return req1(0, getall=True)

@get("/req/<seqno:int>")
@view("req1")
def req1(seqno, getall=False):
    """ Table of requirements for a specific base doc
        also a link to look at the tests
    """
    if getall:
        reqlist = request.db.listrequirement(getall=True)
        bdname = "all base documents"
    else:
        bdr = request.db.getbasedoc(seqno=seqno)
        if not bdr[0]:
            return failpage("no such document {}: {}".format(seqno, bdr[1]))
        bdname = bdr[1]['bdname']

        reqlist = request.db.listrequirement(int(seqno))
    if not reqlist[0]:
        print("listrequirement failed "+reqlist[1])

    def reqtest(reqno):
        """ provide link to related tests showing number of tests
        """
        tests = request.db.listtest(rseqno=int(reqno))
        if not tests[0] or len(tests[1]) <= 0:
            return "-"
        return """<a href="/rtest/{0}">{1}</a>""".format(reqno, len(tests[1]))

    def counttests(reqno):
        tests = request.db.listtest(rseqno=int(reqno))
        if not tests[0] or len(tests[1]) <= 0:
            return 0
        return len(tests[1])

    # sort appropriately 
    if 's' in request.query:
        sortfns = (
            lambda r: r['rseqno'],
            lambda r: r['rstart'],
            lambda r: r['rsameas']or -1,
            lambda r: counttests(r['rseqno']),
            lambda r: r['rtype'],
            lambda r: r['rtext'],
            lambda r: r['rcomment']
        )
        reqlist[1].sort(key=sortfns[int(request.query.s)])
        
    reqtable = "\n".join(
        [ """<tr><td class={vw}><a href="/reqedit/{seqno}" target="_blank">{seqno}</a></td>
            <td class={vw}>{start}/{length}</td>
            <td class={vw}>{sameas}</td>
            <td class={vw}>{reqtest}</td>
            <td class={vw}>{type}</td>
            <td class={vw}>{text}</td>
            <td class={vw}>{comment}</td></tr>""".format(vw=vw, seqno=r['rseqno'],start=r['rstart'],
                length=r['rlength'],sameas=r['rsameas'],reqtest=reqtest(r['rseqno']),
                type=r['rtype'],text=snip(r['rtext']),comment=snip(r['rcomment']))
                for vw, r in zip(altvw, reqlist[1])
         ])


    return dict(boilerplate=boilerplate(),reqtable=reqtable,bdname=bdname,url=request.path)

@get("/reqedit/<seqno:int>")
@view("reqedit")
def reqedit(seqno):
    rreq = request.db.getrequirement(seqno=int(seqno))
    (ret, rreqschema) = request.db.getrequirementschema()
    if not ret or not rreq[0]:
        return failpage("no such requirement {}: {}".format(seqno, rreq[1]))
    req = rreq[1]
    return dict(seqno=seqno, boilerplate=boilerplate(),
        reqtable=Entable('reqedit.csv',defs=req).tedit(schema=rreqschema))

@post("/reqedit/<seqno:int>")
@view("reqedit")
def doreqedit(seqno):
    """ apply changes to a requirement
    """
    if not request.forms.bdseqno.isdigit():
        return failpage("bdseqno not a number")
    if not request.forms.rstart.isdigit():
        return failpage("rstart not a number")
    if not request.forms.rlength.isdigit():
        return failpage("rlength not a number")

    doit = request.db.updaterequirement(rseqno=int(seqno),
        bdseqno=int(request.forms.bdseqno), rsameas=numornone(request.forms.rsameas),
        rstart=int(request.forms.rstart), rlength=int(request.forms.rlength),
        rtext=request.forms.rtext, rtype=request.forms.rtype, rcomment=request.forms.rcomment,
        replacedby=numornone(request.forms.rreplacedby))

    if not doit[0]:
        return failpage("requirement edit failed "+doit[1])
    return reqedit(seqno)

@get("/reqclone/<seqno:int>/<clone>")
@view("reqclone")
def reqclone(seqno, clone):
    clones = request.db.getclones()
    if not clones[0]:
        return failpage("You are not authorized to use this feature.")
    if clone not in clones[1]:
        return failpage("no such clone as {0}".format(request.forms.clone))

    rreq = request.db.getrequirement(seqno=int(seqno))
    if not rreq[0]:
        return failpage("no such requirement {}: {}".format(seqno, rreq[1]))
    req = rreq[1]

    request.db.setprefix(clone)
    crreq = request.db.getrequirement(seqno=int(seqno))
    if not crreq[0]:
        return failpage("no such clone requirement {}: {}".format(seqno, crreq[1]))
    creq = crreq[1]
    request.db.setprefix(None)
    
    return dict(seqno=seqno, boilerplate=boilerplate(), clone=clone,
        reqtable=Entable('reqedit.csv',defs=diffize1(req, creq)).tview(noquote=True))

### tests
@get("/test")
@view("test")
def test():
    """ return a table of tests per base doc
    """
    bdlist = request.db.listbasedoc()
    if not bdlist[0]:
        print("listbasedoc failed")
    # find out how many testts each one has
    for bd in bdlist[1]:
        tests = request.db.listtest(bdseqno=int(bd['bdseqno']))
        if not tests[0]:
            return failpage(tests[1])
        bd['ntests'] = len(tests[1])

    # squeeze out the ones with no reqs and make the table
    testtable = "\n".join(
        [ """<tr><td class={vw}><a href="/btest/{seqno}">{ntests}</a></td>
            <td class={vw}><a href="/bdedit/{seqno}" target="_blank">{rfcno}</a></td>
            <td class={vw}>{doctype}</td>
            <td class={vw}>{stat}</td>
            <td class={vw}>{name}</td></tr>""".format(vw=vw, ntests=d['ntests'],seqno=d['bdseqno'],
                rfcno=d['bdrfcno'],doctype=d['bddoctype'],stat=d['bddstat'],name=d['bdname'])
                for vw, d in zip(altvw, compress(bdlist[1], map(lambda bd: bd['ntests'], bdlist[1])))
            ])

    return dict(boilerplate=boilerplate(),testtable=testtable)

@get("/alltest")
def alltest():
    return rtest(0, getall=True)

@get("/btest/<seqno:int>")
def btest(seqno):
    return rtest(seqno, basedoc=True)
    
@get("/rtest/<seqno:int>")
@view("rtest")
def rtest(seqno, basedoc=False, getall=False):
    """ return a list of tests per requirement
    """
    if getall:
        tlist = request.db.listtest(getall=True)
        tty = "All base documents"
    elif basedoc:
        tlist = request.db.listtest(bdseqno=int(seqno))
        tty = "Base document"
    else:
        tlist = request.db.listtest(rseqno=int(seqno))
        tty = "Requirement"
    if not tlist[0]:
            return failpage("test lookup "+tlist[1])
       
    # sort appropriately 
    if 's' in request.query:
        sortfns = (
            lambda t: t['tseqno'],
            lambda t: t['tdut'],
            lambda t: t['ttext'] or "",
            lambda t: t['tcomment'] or "",
            lambda t: t['tmasterfile'] or "",
            lambda t: t['tlscommand'] or "",
        )
        tlist[1].sort(key=sortfns[int(request.query.s)])

    testtable = "\n".join(
        [ """<tr><td class={vw}><a href="/testedit/{seqno}" target="_blank">{seqno}</a></td>
            <td class={vw}>{dut}</td>
            <td class={vw}>{text}</td>
            <td class={vw}>{comment}</td>
            <td class={vw}>{lscommand}</td></tr>""".format(vw=vw, seqno=t['tseqno'],dut=t['tdut'],
                text=snip(t['ttext']),comment=snip(t['tcomment']),masterfile=snip(t['tmasterfile']),lscommand=snip(t['tlscommand']))
                for vw, t in zip(altvw, tlist[1])
            ])

    return dict(boilerplate=boilerplate(),testtable=testtable,tty=tty, url=request.path)
    
@get("/scantest")
@view("scantest")
def scantest():
    """ return a summary of test info
    """
    tlist = request.db.listtest(getall=True)
    tty = "All base documents"
       
    # sort appropriately 
    if 's' in request.query:
        sortfns = (
            lambda t: t['tseqno'],
            lambda t: t['tdut'],
            lambda t: t['ttext'] or "",
            lambda t: t['tcomment'] or "",
            lambda t: t['tmasterfile'] or "",
            lambda t: t['tlscommand'] or "",
            lambda t: t['toutcome'] or "",
        )
        tlist[1].sort(key=sortfns[int(request.query.s)])

    def stuffize(t):
        """ combine the stuff into one field """
        stuff = "<b>dut</b>: {0}".format(t['tdut'])
        if t['tmasterfile']:
            stuff += ", <b>mf</b>: {0}".format(t['tmasterfile'])
        stuff += "<br/>\n"

        if t['ttext']:
            stuff += "<b>text</b>: {0}<br/>".format(snip(t['ttext'], sniplen=600, wrap=150))
        if t['tcomment']:
            stuff += "<b>comment</b>: {0}<br/>".format(snip(t['tcomment'], sniplen=600, wrap=150))
        if t['tlscommand']:
            stuff += "<b>lscmd</b>: {0}<br/>".format(snip(t['tlscommand'], sniplen=600, wrap=150))
        if t['toutcome']:
            stuff += "<b>outcome</b>: {0}<br/>".format(snip(t['toutcome'], sniplen=600, wrap=150))
        if t['tneg']:
            stuff += "<b>negative</b>: {0}<br/>".format(snip(t['tneg'], sniplen=600, wrap=150))
        return stuff

    testtable = "\n".join(
        [ """<tr><td class={vw}><a href="/testedit/{seqno}" target="_blank">{seqno}</a></td>
            <td class={vw}>{stuff}</td></tr>""".format(vw=vw, seqno=t['tseqno'],stuff=stuffize(t))
                for vw, t in zip(altvw, tlist[1])
            ])

    return dict(boilerplate=boilerplate(),testtable=testtable,tty=tty, url=request.path)
    
@get("/testedit/<seqno:int>")
@view("testedit")
def testedit(seqno):
    rtest = request.db.gettest(seqno=int(seqno))
    (req, rtestschema) = request.db.gettestschema()
    if not req or not rtest[0]:
        return failpage("no such test {}: {}".format(seqno, rtest[1]))
    test = rtest[1]
    return dict(seqno=seqno, boilerplate=boilerplate(),
        reqtable=Entable('testedit.csv',defs=test).tedit(schema=rtestschema))

@get("/testclone/<seqno:int>/<clone>")
@view("testclone")
def testclone(seqno, clone):
    clones = request.db.getclones()
    if not clones[0]:
        return failpage("You are not authorized to use this feature.")
    if clone not in clones[1]:
        return failpage("no such clone as {0}".format(request.forms.clone))

    rtest = request.db.gettest(seqno=int(seqno))
    if not rtest[0]:
        return failpage("no such test {}: {}".format(seqno, rtest[1]))
    test = rtest[1]

    request.db.setprefix(clone)
    crtest = request.db.gettest(seqno=int(seqno))
    if not crtest[0]:
        return failpage("no such clone test {}: {}".format(seqno, crtest[1]))
    request.db.setprefix(None)
    ctest = crtest[1]

    return dict(seqno=seqno, boilerplate=boilerplate(), clone=clone,
        testtable=Entable('testedit.csv',defs=diffize1(test, ctest)).tview(noquote=True))

@post("/testedit/<seqno:int>")
@view("testedit")
def dotestedit(seqno):
    """ apply changes to a test
    """
    if not request.forms.rseqno.isdigit():
        return failpage("rseqno not a number")

    doit = request.db.updatetest(tseqno=int(seqno), rseqno=int(request.forms.rseqno),
        tsameas=numornone(request.forms.tsameas), ttext=request.forms.ttext, tdut=request.forms.tdut,
        tlscommand=request.forms.tlscommand, toutcome=request.forms.toutcome, tneg=request.forms.tneg,
        tcomment=request.forms.tcomment, tmasterfile=request.forms.tmasterfile, replacedby=numornone(request.forms.treplacedby))

    if not doit[0]:
        return failpage("test edit failed "+doit[1])
    return testedit(seqno)

@get("/whacktest")
@view("whacktest")
def whacktest():
    return dict(boilerplate=boilerplate(),
        kvetch="",old="",new="")

@post("/whacktest")
@view("whacktest")
def whacktest():
    oldt = request.forms.old
    newt = request.forms.new

    tlist = request.db.listtest(getall=True)
    if not tlist[0]:
        return failpage(tlist[1])
    nttext = 0
    ntlscommand = 0
    ntoutcome = 0
    ntcomment = 0
    ntmasterfile = 0
    nrecs = 0
    # count or change now
    for t in tlist[1]:
        changed = False
        if request.forms.ttext and t['ttext']:
            n = t['ttext'].count(oldt)
            if n:
                changed = True
                nttext += n
                t['ttext'] = t['ttext'].replace(oldt, newt)
        if request.forms.tlscommand and t['tlscommand']:
            n = t['tlscommand'].count(oldt)
            if n:
                changed = True
                ntlscommand += n
                t['tlscommand'] = t['tlscommand'].replace(oldt, newt)
        if request.forms.toutcome and t['toutcome']:
            n = t['toutcome'].count(oldt)
            if n:
                changed = True
                ntoutcome += n
                t['toutcome'] = t['toutcome'].replace(oldt, newt)
        if request.forms.tcomment and t['tcomment']:
            n = t['tcomment'].count(oldt)
            if n:
                changed = True
                ntcomment += n
                t['tcomment'] = t['tcomment'].replace(oldt, newt)
        if request.forms.tmasterfile and t['tmasterfile']:
            n = t['tmasterfile'].count(oldt)
            if n:
                changed = True
                ntmasterfile += n
                t['tmasterfile'] = t['tmasterfile'].replace(oldt, newt)
        if changed:
            nrecs += 1
        if changed and request.forms.Patch:
            r = request.db.updatetest(tseqno=int(t['tseqno']), ttext=t['ttext'], tlscommand=t['tlscommand'],
                toutcome=t['toutcome'], tcomment=t['tcomment'], tmasterfile=t['tmasterfile'])
            if not r[0]:
                return failpage(r[1])

    x = """Records changed: {}<br/>Changes to ttext: {}<br/>Changes to tlscommand: {}<br/>
    Changes to toutcome: {}<br/>Changes to tcomment: {}<br/>Changes to tmasterfile: {}<br/>""".format(nrecs, nttext, ntlscommand, ntoutcome, ntcomment, ntmasterfile)
    if request.forms.Check:
        x += "No changes actually made"
    else:
        x += "Changes complete"

    return dict(boilerplate=boilerplate(),
        kvetch=x,old=request.forms.old,new=request.forms.new)

# Removed because this was only for Standcore's internal use
'''
@get("/diff")
@view("diff")
def getdiff():
    """
    prepare to check for diffs
    """

    clones = request.db.getclones()
    if not clones[0]:
        return failpage("You are not authorized to use this feature.")
    cloneopts = "\n".join([ "<option>{0}</option>".format(c) for c in clones[1]])
    return dict(boilerplate=boilerplate(),
        kvetch="",cloneopts=cloneopts)

@post("/diff")
def pgetdiff():
    """
    prepare to check for diffs
    """
    clone = request.forms.clone
    which = request.forms.w
    clones = request.db.getclones()
    if not clones[0]:
        return failpage("You are not authorized to use this feature.")
    if clone not in clones[1]:
        return failpage("no such clone as {0}".format(request.forms.clone))

    if which == "b":                     # compare base docs
        (stat, val) = request.db.setprefix(None)
        if not stat:
            return failpage("failed reset prefix from {0} {1}",format(clone, val))
        livebase = request.db.listbasedoc()
        if not livebase[0]:
            return failpage("Cannot get live base documents.")
        (stat, val) = request.db.setprefix(clone)
        if not stat:
            return failpage("failed set prefix to {0} {1}",format(clone, val))
        clonebase = request.db.listbasedoc()
        if not clonebase[0]:
            return failpage("Cannot get clone base documents.")
        (stat, val) = request.db.setprefix(None)
        if not stat:
            return failpage("failed reset prefix from {0} {1}",format(clone, val))
        # make into dicts keyed by seqno
        livedict = { b['bdseqno'] : b for b in livebase[1] }
        clonedict = { b['bdseqno'] : b for b in clonebase[1] }
        (l, c, d) = dictdiff(livedict, clonedict)
        return failpage("Base doc diff: {0}, live: {1}, clone: {2}".format("/".join(map(str,d)), "/".join(map(str,l)), "/".join(map(str,c))))
    elif which == "r":                     # compare requirements
        (stat, val) = request.db.setprefix(None)
        if not stat:
            return failpage("failed reset prefix from {0} {1}",format(clone, val))
        livereq = request.db.listrequirement(getall=True)
        if not livereq[0]:
            return failpage("Cannot get live requirements.")
        (stat, val) = request.db.setprefix(clone)
        if not stat:
            return failpage("failed set prefix to {0} {1}",format(clone, val))
        clonereq = request.db.listrequirement(getall=True)
        if not clonereq[0]:
            return failpage("Cannot get clone requirements.")
        (stat, val) = request.db.setprefix(None)
        if not stat:
            return failpage("failed reset prefix from {0} {1}",format(clone, val))
        request.db.setprefix(None)
        livedict = { b['rseqno'] : b for b in livereq[1] }
        clonedict = { b['rseqno'] : b for b in clonereq[1] }
        (l, c, d) = dictdiff(livedict, clonedict)

        def reqtest(reqno):
            """ provide link to related tests showing number of tests
            """
            tests = request.db.listtest(rseqno=int(reqno))
            if not tests[0] or len(tests[1]) <= 0:
                return "-"
            return """<a href="/rtest/{0}">{1}</a>""".format(reqno, len(tests[1]))

        dreqtable = "\n".join(
        [ """<tr><td class={vw}><a href="/reqclone/{seqno}/{clone}" target="_blank">{seqno}</a></td>
            <td class={vw}>{start}/{length}</td>
            <td class={vw}>{sameas}</td>
            <td class={vw}>{reqtest}</td>
            <td class={vw}>{type}</td>
            <td class={vw}>{text}</td>
            <td class={vw}>{comment}</td></tr>""".format(vw=vw, clone=clone, seqno=r['rseqno'],start=r['rstart'],
                length=r['rlength'],sameas=r['rsameas'],reqtest=reqtest(r['rseqno']),
                type=r['rtype'],text=r['rtext'],comment=r['rcomment'])
                for vw, r in zip(altvw,  diffize(d, livedict, clonedict))
         ])

        creqtable = "\n".join(
        [ """<tr><td class={vw}><a href="/reqedit/{seqno}" target="_blank">{seqno}</a></td>
            <td class={vw}>{start}/{length}</td>
            <td class={vw}>{sameas}</td>
            <td class={vw}>{reqtest}</td>
            <td class={vw}>{type}</td>
            <td class={vw}>{text}</td>
            <td class={vw}>{comment}</td></tr>""".format(vw=vw, seqno=r['rseqno'],start=r['rstart'],
                length=r['rlength'],sameas=r['rsameas'],reqtest=reqtest(r['rseqno']),
                type=r['rtype'],text=snip(r['rtext']),comment=snip(r['rcomment']))
                for vw, r in zip(altvw, [ clonedict[rseq] for rseq in c ])
         ])
        return template('reqdiff',boilerplate=boilerplate(),dreqtable=dreqtable,creqtable=creqtable,clone=clone,
            kvetch="Req diff: {0}, live: {1}, clone: {2}".format("/".join(map(str,d)), "/".join(map(str,l)), "/".join(map(str,c))))

    elif which == "t":                     # compare requirements
        (stat, val) = request.db.setprefix(None)
        if not stat:
            return failpage("failed reset prefix from {0} {1}",format(clone, val))
        livetest = request.db.listtest(getall=True)
        if not livetest[0]:
            return failpage("Cannot get live tests.")
        (stat, val) = request.db.setprefix(clone)
        if not stat:
            return failpage("failed set prefix to {0} {1}",format(clone, val))
        clonetest = request.db.listtest(getall=True)
        if not clonetest[0]:
            return failpage("Cannot get clone requirements.")
        (stat, val) = request.db.setprefix(None)
        if not stat:
            return failpage("failed reset prefix from {0} {1}",format(clone, val))

        # make into dicts keyed by seqno
        livedict = { b['tseqno'] : b for b in livetest[1] }
        clonedict = { b['tseqno'] : b for b in clonetest[1] }
        (l, c, d) = dictdiff(livedict, clonedict)

        dtesttable = "\n".join(
        [ """<tr><td class={vw}><a href="/testclone/{seqno}/{clone}" target="_blank">{seqno}</a></td>
            <td class={vw}>{dut}</td>
            <td class={vw}>{text}</td>
            <td class={vw}>{comment}</td>
            <td class={vw}>{lscommand}</td></tr>""".format(vw=vw, clone=clone, seqno=t['tseqno'],dut=t['tdut'],
                text=t['ttext'],comment=t['tcomment'],masterfile=t['tmasterfile'],lscommand=t['tlscommand'])
                for vw, t in zip(altvw, diffize(d, livedict, clonedict))
            ])

        ctesttable = "\n".join(
        [ """<tr><td class={vw}><a href="/testedit/{seqno}" target="_blank">{seqno}</a></td>
            <td class={vw}>{dut}</td>
            <td class={vw}>{text}</td>
            <td class={vw}>{comment}</td>
            <td class={vw}>{lscommand}</td></tr>""".format(vw=vw, seqno=t['tseqno'],dut=t['tdut'],
                text=escape(t['ttext']),comment=escape(t['tcomment']),masterfile=escape(t['tmasterfile']),lscommand=escape(t['tlscommand']))
                for vw, t in zip(altvw,  [ clonedict[tseq] for tseq in c ])
            ])

        return template('testdiff',boilerplate=boilerplate(),dtesttable=dtesttable,ctesttable=ctesttable,clone=clone,
            kvetch="Test diff: {0}, live: {1}, clone: {2}".format("/".join(map(str,d)), "/".join(map(str,l)), "/".join(map(str,c))))
    else:
        return failpage("Mystery request {0}".format(which))

def dictdiff(livedict, clonedict):
    """
    diff live vs. clone dictionaries
    return (l, c, d) lists of live only, clone only, and different
    """
    
    l = list(set(livedict.keys()) - set(clonedict.keys())) # keys only in live
    c = list(set(clonedict.keys()) - set(livedict.keys())) # keys only in clone
    d = [ lk for lk in iter(livedict) if lk in clonedict and livedict[lk] != clonedict[lk] ] # keys for changed entries
    return (l, c, d)

def diffize(k, livedicts, clonedicts):
    """
    make an array of the diffed dicts for the
    items in array k
    """
    return [ diffize1(livedicts[ix], clonedicts[ix]) for ix in k ]

def diffize1(livedict, clonedict):
    """
    diff a single pair of dicts
    """
    import difflib

    dd = {}
    for (dx, dv) in livedict.items():
        if dv == clonedict[dx]:            # field unchanged
            dd[dx] = escape(str(dv))
        else:
            dr = str(dv).strip()
            cr = str(clonedict[dx]).strip()
            sm = difflib.SequenceMatcher(lambda x: x in " \t\n", dr, cr)
            comp = ""
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    comp += escape(dr[i1:i2])
                elif tag == 'replace':
                    comp += u'<div class="del">{0}</div><div class="add">{1}</div>'.format(escape(dr[i1:i2]), escape(cr[j1:j2]))
                elif tag == 'delete':    
                    comp += u'<div class="del">{0}</div>'.format(escape(dr[i1:i2]))
                elif tag == 'insert':    
                    comp += u'<div class="add">{0}</div>'.format(escape(cr[j1:j2]))
                else:
                    comp += "??? tag " + tag
            dd[dx] = comp
    return dd
'''
    
@view('failpage')
def failpage(why):
    """ return a failure page
    """
    return dict(boilerplate=boilerplate(),
        kvetch=why)

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='./static')

# special cases
@route('/favicon.ico')
def favicon():
    return static_file("favicon.ico", root='./static')


if __name__=="__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "debug":
        # please do not change this, it's how a Standcore internal VM is set up
        run(host='10.0.2.15', port=8800, debug=True)
    else:
        run(server="cgi", debug=True)
