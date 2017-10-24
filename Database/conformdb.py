#!/usr/bin/env python3
import pymysql
import datetime, json, os.path, time

'''
Utility functions used by other programs that access the test plan database.
All calls for database access should go through this module.
It is symlinked into the directories that need it.
'''

# The MySQL password for user dnsconf
dbuser = "dnsconf"
dbname = "dnsconf"
UserPassword = "NitPicky"

# mysql escape string
def mses(instring):
    return instring.replace("\\","\\\\").replace("'","\\'")

# get rid ot pesky carriage returns
def uncr(s):
    if not s:
        return s                        # null or something
    if "\r" in s:
        logthis("whacked a carriage return")
        return s.replace("\r","")
    return s

##### Log stuff, mostly for debugging
def logthis(instring):
    logfilename = "/tmp/conformdb-log.txt"
    if not(os.path.exists(logfilename)):
        try:
            createf = open(logfilename, mode="w")
            createf.close()
        except:
            return("Failed to create log file %s." % logfilename)
        try:
            os.chmod(logfilename, 0o0666)
        except:
            return("Failed to chmod 0666 on log file %s." % logfilename)
    try:
        logf = open(logfilename, mode="a")
    except:
        return("Was not able to append to %s." % logfilename)
    logf.write("{0} {1}\n".format(time.strftime("%Y-%m-%d-%H-%M-%S"), instring))
    logf.close()
    return()


class Conformdb:
    """ Operations on the Conformance database
    """

    def __init__(self, user=""):
        self.User = user
        self.Connection = pymysql.connect(user=dbuser, passwd=UserPassword, db=dbname)
        pymysql.paramstyle="format"

        # get user privs
        Cursor = self.Connection.cursor()
        try:
            Cursor.execute("SELECT userpriv,userwho FROM users WHERE username=%s",(user,))
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])
        if Cursor.rowcount > 0:
            (self.UserPriv, self.UserWho) = Cursor.fetchone()
        else:
            self.UserPriv = ""
            self.UserWho = ""
            
        # handle cloning
        # allow editing of cloned database
        if self.UserPriv and "Clone" in self.UserPriv:
            self.UserPriv += ",Edit"
            self._prefix = self.User + "_"
        else:
            self._prefix = ""

        # remember table names
        self.tables =  ("basedoc", "requirement", "tests")
        self._basedocschema = None
        self._requirementschema = None
        self._testschema = None

    def getuserinfo(self):
        """ get user info in a dict
        """
        # censor down to Edit or nothing to avoid confusing client
        # code
        return (True, { "userpriv": "Edit" if self.UserPriv and "Edit" in self.UserPriv else "", "userwho": self.UserWho })

    def clearbasedoc(self):
        """ clear out basedoc table in preparation for loading
            returns (true, "") or (false, reason)
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")
        Cursor = self.Connection.cursor()
        try:
            Cursor.execute("TRUNCATE {0}basedoc".format(self._prefix))
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])
        return (True, "")

    ### basedoc
    def listbasedoc(self, name=None, doctype=None):
        """ get a list of base docs optionally by name 
            returns (False, "reason")
            (True, [ dictofdocfields, ... ]) list of docs
        """
        Cursor = self.Connection.cursor()
        # set up conditions
        Conditions = ""
        cargs = []
        if name:
            Conditions = " WHERE bdname like %s"
            cargs.append ("%"+name+"%")
        if doctype:
            if Conditions:
                Conditions += " AND bddoctype=%s"
            else:
                Conditions += " WHERE bddoctype=%s"
            cargs.append(doctype)

        sql = "SELECT * FROM {0}basedoc {1} ORDER BY bdrfcno,bdname".format(self._prefix, Conditions)
        try:
            Cursor.execute(sql, cargs)
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])
        thenamelist = [ d[0] for d in Cursor.description ]
        therecords = [ dict(zip(thenamelist, i)) for i in Cursor.fetchall() ]

        return (True, therecords)

    def getbasedoc(self, seqno=None, name=None, rfcno=None):
        """ get a doc by seqno, name, or rfc number
            should only match one document
            returns (True, dict) or (False, "reason")
        """
        # contruct SQL conditions to fetch what should be one record
        SQLConditions = ""
        SQLArgs = []
        if seqno:
            if not isinstance(seqno, int):
                return (False, "sequence number not int")
            SQLConditions = "bdseqno=%s"
            SQLArgs.append(seqno)
        if name:
            if SQLConditions:
                SQLConditions += " OR "
            SQLConditions += "bdname=%s"
            SQLArgs.append(name)
        if rfcno:
            if not isinstance(rfcno, int):
                return (False, "RFC number not int")
            if SQLConditions:
                SQLConditions += " OR "
            SQLConditions += "bdrfcno=%s"
            SQLArgs.append(rfcno)
        if not SQLConditions:
            return (False, "No selection criteria")

        SQLCmd = "SELECT * FROM {0}basedoc WHERE {1}".format(self._prefix, SQLConditions)
        Cursor = self.Connection.cursor()
        try:
            Cursor.execute(SQLCmd, SQLArgs)
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])
        thenamelist = [ d[0] for d in Cursor.description ]
        if Cursor.rowcount < 1:
            return (False, "No such base document")
        if Cursor.rowcount > 1:
            return (False, "Ambiguous base document")
        basedoc = list(Cursor.fetchone())
        
        # smash dates back into strings
        for fn in ("bdupdated","bdadded"):
            if fn in thenamelist:
                i = thenamelist.index(fn)
                basedoc[i] = basedoc[i].isoformat(' ')

        return (True, dict(zip(thenamelist, basedoc)))

    def putbasedoc(self, seqno=None, name=None, rfcno=None, text=None, doctype=None, errata=None,
        ediff=None, thstat="None", comment=None, dstat="Active"):
        """ insert or replace a doc in the basedoc table
            return (True. seqno) if it worked, (False, "ugh") if not
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")
        if seqno is not None and not isinstance(seqno, int):
            return (False, "sequence number not int")
        if rfcno is not None and not isinstance(rfcno, int):
            return (False, "RFC number not int")
        Cursor = self.Connection.cursor()
        # get existing version if any
        (rval, CurrentDoc) = self.getbasedoc(seqno, name, rfcno)
        if not rval and "Ambiguous" in CurrentDoc:
            return (rval, CurrentDoc)
        try:                            # catch all of the mysql errors
            if rval:
                # save current version
                seqno = CurrentDoc["bdseqno"]   # use the same sequence number when replacing
                try:
                    Cursor.execute("INSERT INTO {0}basedoc_history (SELECT * FROM {0}basedoc WHERE bdseqno=%s)".format(self._prefix), (seqno,))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])
                SQLCmd = "REPLACE"
                added = CurrentDoc['bdadded'] # preserve create time
            else:
                SQLCmd = "INSERT"
                added = None
            SQLCmd += """ INTO {0}basedoc(bdseqno, bdname, bddoctype, bdrfcno, bdtext, bderrata, bdediff, bdthstat,
                bdcomment, bddstat, bduser, bdadded) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""".format(self._prefix)
            try:
                Cursor.execute(SQLCmd, (seqno, name, doctype, rfcno, uncr(text), uncr(errata), uncr(ediff),
                    thstat, uncr(comment), dstat,  self.User, added))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, args.err[1])

        if not seqno:
            seqno = Cursor.lastrowid      # seqno of row just inserted
        self.Connection.commit()
        return (True, seqno)

    def _updatearg(self, aname, avalue):
        if avalue == False:
            return
        if self.sqlstr:
            self.sqlstr += ", "
        self.sqlstr += "{0}=%s".format(aname)
        self.sqlargs.append(avalue)

    def updatebasedoc(self, seqno=None, name=False, rfcno=False, text=False, doctype=False, errata=False,
        ediff=False, thstat=False, comment=False, dstat=False):
        """ insert or replace a doc in the basedoc table
            return true if it worked, false if not
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")
        if not seqno:
            return (False, "Need sequence number")

        if not isinstance(seqno, int):
            return (False, "sequence number not int")
        if rfcno is not None and rfcno is not False and not isinstance(rfcno, int):
            return (False, "RFC number not int")
        # create INSERT arguments for whatever has changed
        self.sqlstr = ""
        self.sqlargs = []
        self._updatearg("bdname", name)
        self._updatearg("bdrfcno", rfcno)
        self._updatearg("bdtext", uncr(text))
        self._updatearg("bddoctype", doctype)
        self._updatearg("bderrata", uncr(errata))
        self._updatearg("bdediff", uncr(ediff))
        self._updatearg("bdthstat", thstat)
        self._updatearg("bdcomment", uncr(comment))
        self._updatearg("bddstat", dstat)
        if not self.sqlstr:
            return (False, "Nothing to change")
        cur = self.Connection.cursor()
        try:
            # save current version
            try:
                cur.execute("INSERT INTO {0}basedoc_history (SELECT * FROM {0}basedoc WHERE bdseqno=%s)".format(self._prefix), (seqno,))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

            # make UPDATE command and run it
            self.sqlargs.append(seqno)
            sql = "UPDATE {0}basedoc SET {1} WHERE bdseqno=%s".format(self._prefix, self.sqlstr)
            try:
                cur.execute(sql, self.sqlargs)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        self.Connection.commit()
        return (True, "")

    def deletebasedoc(self, bdseqno=None, bdcomment=None):
        """ delete entries from basedocs by seqno, or string in bdcomment
            return (False, "errmsg")
            or (True, (list of seqnos deleted)
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")

        if bdseqno is not None and not isinstance(bdseqno, int):
            return (False, "Base document number not int")
        if not bdseqno and not bdcomment:
            return (False, "Nothing to delete")
        if bdseqno and bdcomment:
            return (False, "Too much to delete")

        cur = self.Connection.cursor()

        try:
            if bdseqno:
                snlist = [bdseqno]            # just the one
            else:
                sql = "SELECT bdseqno FROM {0}basedoc WHERE bdcomment LIKE %s".format(self._prefix)
                try:
                    cur.execute(sql, ('%'+bdcomment+'%',))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])
                snlist = [ r[0] for r in cur.fetchall() ]
                if not snlist:
                    return (False, "Comment matches no records")

            # archive and delete tests
            # need to make temp table of test seqnos due to mysql limits
            sql = """CREATE TEMPORARY TABLE tseqno (SELECT tseqno FROM {0}basedoc NATURAL JOIN {0}requirement
            NATURAL JOIN {0}tests
            WHERE bdseqno IN ({1}))""".format(self._prefix, ",".join(map(str,snlist)))
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

            sql = "INSERT INTO {0}tests_history (SELECT * FROM {0}tests WHERE tseqno IN (SELECT tseqno FROM tseqno))".format(self._prefix)
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

            sql = "DELETE FROM {0}tests WHERE tseqno IN (SELECT tseqno FROM tseqno)".format(self._prefix)
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        
            # archive and delete requirements, same deal
            sql = """CREATE TEMPORARY TABLE rseqno (SELECT rseqno FROM {0}basedoc NATURAL JOIN {0}requirement
                WHERE bdseqno IN ({1}))""".format(self._prefix, ",".join(map(str,snlist)))
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        
            sql = "INSERT INTO {0}requirement_history (SELECT * FROM {0}requirement WHERE rseqno IN (SELECT rseqno FROM rseqno))".format(self._prefix)
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

            sql = "DELETE FROM {0}requirement WHERE rseqno IN (SELECT rseqno FROM rseqno)".format(self._prefix)
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        
            # archive and delete base docs
            sql = "INSERT INTO {0}basedoc_history (SELECT * FROM {0}basedoc WHERE bdseqno IN ({1}))".format(self._prefix, ",".join(map(str,snlist)))
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

            sql = "DELETE FROM {0}basedoc WHERE bdseqno IN ({1})".format(self._prefix, ",".join(map(str,snlist)))
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
            try:
                cur.execute("DROP TEMPORARY TABLE tseqno, rseqno")
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        self.Connection.commit()

        return (True, snlist)

    def getbasedocschema(self):
        """ return schema of basedoc table
        mostly so console can automatically adapt the
        enum and set selections
        """

        if not self._basedocschema:
            cur = self.Connection.cursor()
            cur.execute("SHOW COLUMNS FROM {0}basedoc".format(self._prefix))
            # turn into a dict keyed by field name
            self._basedocschema = { f[0]: f[1:] for f in cur.fetchall() }
        return (True, self._basedocschema)


    ### requirements
    def listrequirement(self, seqno=None, getall=False):
        """ get requirements for a base doc
            returns (False, "reason")
            (True, [dict(), dict(), ...]) list of requirements as dicts
            getall gets all requirements
            note that dates are not smashed back into strings
        """
        if getall:
            Cursor = self.Connection.cursor()
            SQLCmd = "SELECT * FROM {0}requirement ORDER BY rstart".format(self._prefix)
            try:
                Cursor.execute(SQLCmd)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
            pass
        else:
            if not seqno and not getall:
                return (False, "Need base document sequence number")
            if not isinstance(seqno, int):
                return (False, "Sequence number not int")
            Cursor = self.Connection.cursor()
            SQLCmd = "SELECT * FROM {0}requirement WHERE bdseqno=%s ORDER BY rstart".format(self._prefix)
            try:
                Cursor.execute(SQLCmd, (seqno,))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        thenamelist = [ d[0] for d in Cursor.description ]
        therecords = [ dict(zip(thenamelist, i)) for i in Cursor.fetchall() ]
        return (True, therecords)
            
    def getrequirement(self, seqno=None):
        """ get requirements for a base doc
            returns (False, "reason")
            (True, dict)
        """
        if not seqno:
            return (False, "Need requirement sequence number")
        if not isinstance(seqno, int):
            return (False, "Sequence number not int")
        Cursor = self.Connection.cursor()
        SQLCmd = "SELECT * FROM {0}requirement WHERE rseqno=%s".format(self._prefix)
        try:
            Cursor.execute(SQLCmd, (seqno,))
            thenamelist = [ d[0] for d in Cursor.description ]
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        if Cursor.rowcount < 1:
            return (False, "No such requirement")
        
        # smash dates into strings
        req = list(Cursor.fetchone())
        for fn in ("rupdated","radded"):
            if fn in thenamelist:
                i = thenamelist.index(fn)
                req[i] = req[i].isoformat(' ')
        
        return (True, dict(zip(thenamelist, req)))

    def putrequirement(self, rseqno=None, bdseqno=None, rsameas=None, rstart=None, rlength=None, rtext=None,
        rtype=None, rcomment=None, replaces=None, replacedby=None):
        """ insert or replace an entry in the requirement table
            note that replaces updates a different record, replaces updates this record; add either or both
            if rseqno is set it's an update, otherwise an add
            return
                (True, seqno)
                (False, "error message")
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")

        if rseqno is not None and not isinstance(rseqno, int):
            return (False, "Requirement sequence number not int")
        if not bdseqno or not rstart or not rlength or not rtext:
            return (False, "Need a base doc, defined range and text")
        if not isinstance(bdseqno, int):
            return (False, "Base doc sequence number not int")
        if not isinstance(rstart, int):
            return (False, "Start position not int")
        if not isinstance(rlength, int):
            return (False, "Section length not int")

        Cursor = self.Connection.cursor()
        try:
            # see if it already exists
            if rseqno:
                (rval, curreq) = self.getrequirement(seqno=rseqno)
                if not rval:
                    return (rval, curreq)   # nothing to replace
                try:
                    Cursor.execute("INSERT INTO {0}requirement_history (SELECT * FROM {0}requirement WHERE rseqno=%s)".format(self._prefix), (rseqno,))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])
                SQLCmd = "REPLACE"
                radded = curreq['radded']   # preserve original create time
                if not replacedby:
                    replacedby = curreq['rreplacedby'] # preserve current if not explicitly set
            else:
                SQLCmd = "INSERT"  # new requirement
                radded = None
            SQLCmd += """ INTO {0}requirement(rseqno, bdseqno, rsameas, rstart, rlength, rtext, rtype, rcomment, rreplacedby, ruser, radded)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""".format(self._prefix)
            try:
                Cursor.execute(SQLCmd, (rseqno, bdseqno, rsameas, rstart, rlength, uncr(rtext), rtype, uncr(rcomment), replacedby, self.User, radded))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
            if not rseqno:
                rseqno = Cursor.lastrowid      # seqno of row just inserted

            # update replaced row if need be
            if replaces:
                try:
                    Cursor.execute("UPDATE {0}requirement SET rreplacedby=%s WHERE rseqno=%s".format(self._prefix), (rseqno,replaces))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])
        except pymysql.err.Error as err:
            self.Connection.rollback()
            if err.args[0] == 1062:
                return (False, "Duplicate requirement range") # 
            return (False, err.args[1])

        self.Connection.commit()
        return (True, rseqno)

    def updaterequirement(self, rseqno=None, bdseqno=False, rsameas=False, rstart=False, rlength=False, rtext=False,
        rtype=False, rcomment=False, replaces=False, replacedby=False, ruser=False):
        """ update an entry in the requirement table
            note that replaces updates a different record, replaces updates this record; add either or both
            rseqno must be set
            return
                (True, "")
                (False, "error message")
        """

        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")
        if not rseqno:
            return (False, "Need sequence number")
        if not isinstance(rseqno, int):
            return (False, "Requirement sequence number not int")
        if bdseqno is not None and bdseqno is not False and not isinstance(bdseqno, int):
            return (False, "Base doc sequence number not int")
        if rsameas is not None and rsameas is not False and not isinstance(rsameas, int):
            return (False, "rsameas position not int")
        if rstart is not None and rstart is not False and not isinstance(rstart, int):
            return (False, "Start position not int")
        if rlength is not None and rlength is not False and not isinstance(rlength, int):
            return (False, "Section length not int")
        if replaces is not None and replaces is not False and not isinstance(replaces, int):
            return (False, "Replaces not int")
        if replacedby is not None and replacedby is not False and not isinstance(replacedby, int):
            return (False, "Replacedby not int")

        # create INSERT arguments for whatever has changed
        self.sqlstr = ""
        self.sqlargs = []
        self._updatearg("bdseqno", bdseqno)
        self._updatearg("rsameas", rsameas)
        self._updatearg("rstart", rstart)
        self._updatearg("rlength", rlength)
        self._updatearg("rtext", uncr(rtext))
        self._updatearg("rtype", rtype)
        self._updatearg("rcomment", uncr(rcomment))
        self._updatearg("rreplacedby", replacedby)
        self._updatearg("ruser", ruser)
        
        if not self.sqlstr and not replaces:
            return (False, "Nothing to change")
        cur = self.Connection.cursor()
        try:
            # handle replaces specially, delete any previous, then set
            # this one
            if replaces:
                try:
                    cur.execute("UPDATE {0}requirement SET rreplacedby=NULL where rreplacedby=%s".format(self._prefix), (rseqno,))
                    cur.execute("UPDATE {0}requirement SET rreplacedby=%s where rseqno=%s".format(self._prefix), (rseqno,replaces))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])

            # could be no change here if only changed replaces
            if self.sqlstr:
                # save current version
                try:
                    cur.execute("INSERT INTO {0}requirement_history (SELECT * FROM {0}requirement WHERE rseqno=%s)".format(self._prefix), (rseqno,))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])

                # make UPDATE command and run it
                self.sqlargs.append(rseqno)
                sql = "UPDATE {0}requirement SET {1} WHERE rseqno=%s".format(self._prefix, self.sqlstr)
                try:
                    cur.execute(sql, self.sqlargs)
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])

        except pymysql.err.Error as err:
            self.Connection.rollback()
            if err.args[0] == 1062:
                return (False, "Duplicate range")
            return (False, err.args[1])

        self.Connection.commit()
        return (True, "")

    def deleterequirement(self, rseqno=None, rcomment=None):
        """ delete entries from requirement by seqno, or string in rcomment
            return (False, "errmsg")
            or (True, (list of seqnos deleted)
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")

        if not rseqno and not rcomment:
            return (False, "Nothing to delete")
        if rseqno and rcomment:
            return (False, "Too much to delete")
        if rseqno and not isinstance(rseqno, int):
            return (False, "Requirement sequence number not int")

        cur = self.Connection.cursor()

        try:
            if rseqno:
                snlist = [rseqno]            # just the one
            else:
                sql = "SELECT rseqno FROM {0}requirement WHERE rcomment LIKE %s".format(self._prefix)
                try:
                    cur.execute(sql, ('%'+rcomment+'%',))
                except pymysql.err.Error as err:
                    self.Connection.rollback()
                    return (False, err.args[1])
                snlist = [ r[0] for r in cur.fetchall() ]
                if not snlist:
                    return (False, "Comment matches no records")

            # archive and delete tests
            # need to make temp table of test seqnos due to mysql limits
            try:
                sql = """CREATE TEMPORARY TABLE tseqno (SELECT tseqno FROM {0}requirement NATURAL JOIN {0}tests
                     WHERE rseqno IN ({1}))""".format(self._prefix, ",".join(map(str,snlist)))
                cur.execute(sql)
               
                sql = "INSERT INTO {0}tests_history (SELECT * FROM {0}tests WHERE tseqno IN (SELECT tseqno FROM tseqno))".format(self._prefix)
                cur.execute(sql)
               
                sql = "DELETE FROM {0}tests WHERE tseqno IN (SELECT tseqno FROM tseqno)".format(self._prefix)
                cur.execute(sql)
               
                # archive and delete requirements
                sql = "INSERT INTO {0}requirement_history (SELECT * FROM {0}requirement WHERE rseqno IN ({1}))".format(self._prefix, ",".join(map(str,snlist)))
                cur.execute(sql)
               
                sql = "DELETE FROM {0}requirement WHERE rseqno IN ({1})".format(self._prefix, ",".join(map(str,snlist)))
                cur.execute(sql)
               
                cur.execute("DROP TEMPORARY TABLE tseqno")
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        self.Connection.commit()

        return (True, snlist)
        
    def getrequirementschema(self):
        """ return schema of requirement table
        mostly so console can automatically adapt the
        enum and set selections
        """

        if not self._requirementschema:
            cur = self.Connection.cursor()
            cur.execute("SHOW COLUMNS FROM {0}requirement".format(self._prefix))
            # turn into a dict keyed by field name
            self._requirementschema = { f[0]: f[1:] for f in cur.fetchall() }
        return (True, self._requirementschema)


    ### tests
    def listtest(self, bdseqno=None, rseqno=None, getall=False):
        """ get tests for a requirement or for a base doc
            getall gets all tests
            returns (False, "reason")
            (True, [testdict, ...]) list of tests
        """
        if not getall:
            if not bdseqno and not rseqno :
                return (False, "Need requirement or base doc sequence number")
            if bdseqno and rseqno:
                return (False, "Overdetermined requirement and base doc sequence numbers")
            if rseqno and not isinstance(rseqno, int):
                return (False, "Requirement sequence number not int")
            if bdseqno and not isinstance(bdseqno, int):
                return (False, "Base doc sequence number not int")

        Cursor = self.Connection.cursor()
        try:
            if getall:
                SQLCmd = "SELECT * FROM {0}tests NATURAL JOIN {0}requirement ORDER BY bdseqno,rstart".format(self._prefix)
                Cursor.execute(SQLCmd)
            elif bdseqno:
                SQLCmd = "SELECT * FROM {0}tests NATURAL JOIN {0}requirement WHERE bdseqno=%s ORDER BY bdseqno,rstart".format(self._prefix)
                Cursor.execute(SQLCmd, (bdseqno,))
            else:
                SQLCmd = "SELECT * FROM {0}tests NATURAL JOIN {0}requirement WHERE rseqno=%s ORDER BY bdseqno,rstart".format(self._prefix)
                Cursor.execute(SQLCmd, (rseqno,))
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])
        thenamelist = [ d[0] for d in Cursor.description ]
        therecords = [ dict(zip(thenamelist, i)) for i in Cursor.fetchall() ]

        return (True, therecords)
            
    def gettest(self, seqno=None):
        """ get a test
            returns (False, "reason")
            (True, testdict)
            note that you can get a test even if it's replaced, need higher level code to deal with
            doing the replacement instead
        """
        if not seqno:
            return (False, "Need test sequence number")
        if not isinstance(seqno, int):
            return (False, "Test sequence number not int")
        Cursor = self.Connection.cursor()
        SQLCmd = "SELECT * FROM {0}tests where tseqno=%s".format(self._prefix)
        try:
            Cursor.execute(SQLCmd, (seqno,))
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])
        thenamelist = [ d[0] for d in Cursor.description ]
        if Cursor.rowcount < 1:
            return (False, "No such test")
        
        # smash dates into strings
        test = list(Cursor.fetchone())
        for fn in ("tupdated","tadded"):
            if fn in thenamelist:
                i = thenamelist.index(fn)
                test[i] = test[i].isoformat(' ')
        
        return (True, dict(zip(thenamelist, test)))

    def puttest(self, tseqno=None, rseqno=None, tsameas=None, ttext=None, tdut=None, tlscommand=None, toutcome=None, tneg=None,
        tcomment=None, tmasterfile=None, replaces=None, replacedby=None):
        """ insert or update a doc in the tests table
            note that replaces updates a different record, replaces updates this record; add either or both
            if tseqno is set it's an update, otherwise an add
            return
                (True, seqno)
                (False, "error message")
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")

        if not rseqno or not ttext:
            return (False, "Need a requirement, and text")
        if not isinstance(rseqno, int):
            return (False, "Requirement sequence number is not int")
        if tseqno is not None and not isinstance(tseqno, int):
            return (False, "Test sequence number is not int")
        if tsameas is not None and not isinstance(tsameas, int):
            return (False, "Same-as sequence number is not int")
        if replaces is not None and replaces is not False and not isinstance(replaces, int):
            return (False, "Replaces not int")
        if replacedby is not None and replacedby is not False and not isinstance(replacedby, int):
            return (False, "Replacedby not int")

        Cursor = self.Connection.cursor()
        # see if it already exists
        if tseqno:
            (rval, curtest) = self.gettest(seqno=tseqno)
            if not rval:
                return (rval, curtest)   # nothing to replace
            try:
                Cursor.execute("INSERT INTO {0}tests_history (SELECT * FROM {0}tests WHERE tseqno=%s)".format(self._prefix), (tseqno,))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
            SQLCmd = "REPLACE"
            tadded = curtest['tadded']   # preseve create time
        else:
            SQLCmd = "INSERT"  # new requirement
            tadded = None
        SQLCmd += """ INTO {0}tests(tseqno, rseqno, tsameas, ttext, tdut, tlscommand, toutcome, tneg, tcomment, tmasterfile, tuser, tadded, treplacedby)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""".format(self._prefix)
        try:
            Cursor.execute(SQLCmd, (tseqno, rseqno, tsameas, uncr(ttext), tdut, uncr(tlscommand), uncr(toutcome), uncr(tneg), uncr(tcomment), uncr(tmasterfile), self.User, tadded, replacedby))
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        if not tseqno:
            tseqno = Cursor.lastrowid      # seqno of row just inserted

        # update replaced row if need be
        if replaces:
            try:
                Cursor.execute("UPDATE {0}tests SET treplacedby=%s WHERE tseqno=%s".format(self._prefix), (tseqno,replaces))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
        self.Connection.commit()
        return (True, tseqno)

    def updatetest(self, tseqno=None, rseqno=False, tsameas=False, ttext=False, tdut=False, tlscommand=False, toutcome=False, tneg=False,
        tcomment=False, tmasterfile=False, tuser=False, replaces=False, replacedby=False):
        """ update an entry in the tests table
            note that replaces updates a different record, replaces updates this record; add either or both
            tseqno must be set
            return
                (True, "")
                (False, "error message")
        """

        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")
        if not tseqno:
            return (False, "Need sequence number")
        if not isinstance(tseqno, int):
            return (False, "Test sequence number is not int")
        if rseqno is not None and rseqno is not False and not isinstance(rseqno, int):
            return (False, "Requirement sequence number is not int")
        if tsameas is not None and tsameas is not False and not isinstance(tsameas, int):
            return (False, "Same-as sequence number is not int")
        if replaces is not None and replaces is not False and not isinstance(replaces, int):
            return (False, "Replaces not int")
        if replacedby is not None and replacedby is not False and not isinstance(replacedby, int):
            return (False, "Replacedby not int")

        # create INSERT arguments for whatever has changed
        self.sqlstr = ""
        self.sqlargs = []
        self._updatearg("rseqno", rseqno)
        self._updatearg("tsameas", tsameas)
        self._updatearg("ttext", uncr(ttext))
        self._updatearg("tdut", tdut)
        self._updatearg("tlscommand", uncr(tlscommand))
        self._updatearg("toutcome", uncr(toutcome))
        self._updatearg("tneg", uncr(tneg))
        self._updatearg("tcomment", uncr(tcomment))
        self._updatearg("tmasterfile", uncr(tmasterfile))
        self._updatearg("tuser", tuser)
        self._updatearg("treplacedby", replacedby)
        
        if not self.sqlstr and not replaces:
            return (False, "Nothing to change")

        cur = self.Connection.cursor()
        # handle replaces specially, delete any previous, then set
        # this one
        if replaces:
            try:
                cur.execute("UPDATE {0}tests SET treplacedby=NULL WHERE treplacedby=%s".format(self._prefix), (tseqno,))
                cur.execute("UPDATE {0}tests SET treplacedby=%s WHERE tseqno=%s".format(self._prefix), (tseqno,replaces))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

        # could be no change here if only changed replaces
        if self.sqlstr:
            # save current version
            try:
                cur.execute("INSERT INTO {0}tests_history (SELECT * FROM {0}tests WHERE tseqno=%s)".format(self._prefix), (tseqno,))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

            # make UPDATE command and run it
            self.sqlargs.append(tseqno)
            sql = "UPDATE {0}tests SET {1} WHERE tseqno=%s".format(self._prefix, self.sqlstr)
            try:
                cur.execute(sql, self.sqlargs)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

        self.Connection.commit()
        return (True, "")

    def deletetests(self, tseqno=None, tcomment=None):
        """ delete entries from tests by tseqno, or string in tcomment
            return (False, "errmsg")
            or (True, (list of seqnos deleted)
        """
        if "Edit" not in self.UserPriv:
            return (False, "Not allowed")

        if not tseqno and not tcomment:
            return (False, "Nothing to delete")
        if tseqno and tcomment:
            return (False, "Too much to delete")
        if tseqno and not isinstance(tseqno, int):
            return (False, "Test sequence number is not int")

        cur = self.Connection.cursor()

        if tseqno:
            snlist = [tseqno]            # just the one
        else:
            sql = "SELECT tseqno FROM {0}tests WHERE tcomment LIKE %s".format(self._prefix)
            try:
                cur.execute(sql, ('%'+tcomment+'%',))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
            snlist = [ r[0] for r in cur.fetchall() ]
            if not snlist:
                return (False, "Comment matches no records")

        # archive and delete tests
        sql = "INSERT INTO {0}tests_history (SELECT * FROM {0}tests WHERE rseqno IN ({1}))".format(self._prefix, ",".join(map(str,snlist)))
        try:
            cur.execute(sql)
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        sql = "DELETE FROM {0}tests WHERE tseqno IN ({1})".format(self._prefix, ",".join(map(str,snlist)))
        try:
            cur.execute(sql)
        except pymysql.err.Error as err:
            self.Connection.rollback()
            return (False, err.args[1])

        self.Connection.commit()

        return (True, snlist)

    def gettestschema(self):
        """ return schema of test table
        mostly so console can automatically adapt the
        enum and set selections
        """

        if not self._testschema:
            cur = self.Connection.cursor()
            cur.execute("SHOW COLUMNS FROM {0}tests".format(self._prefix))
            # turn into a dict keyed by field name
            self._testschema = { f[0]: f[1:] for f in cur.fetchall() }
        return (True, self._testschema)

    ### reports
    def fulldatabase(self, where="disk"):
        """ Returns a dict with three members: "basedoc", "requirement", and "tests"
            Each member is an array of the records; each record is a dict
            where="disk" means dump the result as JSON into /tmp; where="prompt" means return the JSON
        """
        cur = self.Connection.cursor()
        returndict = {}
        for thistable in self.tables:
            sql = "SELECT * FROM {0}{1}".format(self._prefix, thistable)
            try:
                cur.execute(sql)
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])
            # get the field names
            thenamelist = [ d[0] for d in cur.description ]
            therecords = [ dict(zip(thenamelist, i)) for i in cur.fetchall() ]
            # A hack to replace the text of a basedoc with a short string
            if thistable == "basedoc":
                for thisrecord in therecords:
                    thisrecord["bdtext"] = "Text of length {0}",format(len(thisrecord["bdtext"]))
            # Another hack to turn all the dates into strings
            for thisrecord in therecords:
                for thiskey in thisrecord:
                    if isinstance(thisrecord[thiskey], datetime.datetime):
                        thisrecord[thiskey] = (thisrecord[thiskey]).strftime("%Y-%m-%d-%H-%M-%S")
            returndict[thistable] = therecords
        outjson = json.dumps(returndict, indent=2)
        if where == "disk":
            tmpfileloc = "/tmp/fulldatabase.json"
            try:
                fout = open(tmpfileloc, mode="w")
                fout.write(outjson)
                fout.close()
            except:
                return (False, "Was not able to write out the file to %s" % tmpfileloc)
            return(True, "")
        elif where=="prompt":
            return (True, outjson)
        else:
            return (False, "Got a bad argument for where: %s" % where)

    def clone(self, active=True, snapshot=False):
        """ switch to or from cloned database
           active True means to use clone, active False means to use real DB
           snapshot True means to recopy the tables if they exist
           a new clone always makes a snapshot
           Clone flag in users table says whether using cloned DB
           Comment flag means allowed to clone
           HACK: in userpriv column, depends on Edit=1, Comment=2, Clone=3
           """
        if "Comment" not in self.UserPriv:
            return (False, "Cloning is not allowed for this user.")

        cur = self.Connection.cursor()
        if not active:                  # turn off cloning
            sql = "UPDATE users SET userpriv=userpriv & ~4 WHERE username=%s"
            cur.execute(sql, (self.User,))
            cur.execute("SELECT userpriv FROM users WHERE username=%s",(self.User,))
            self.UserPriv = cur.fetchone()[0]
            self.Connection.commit()
            self._prefix = ""
            # return (True, "Clone database inactive")
            return (True, "You are no longer using a clone; instead, you can view the live database.")

        # cloning active, set flags
        print("user",self.User)
        sql = "UPDATE users SET userpriv=userpriv | 4 WHERE username=%s"
        cur.execute(sql, (self.User,))
        cur.execute("SELECT userpriv FROM users WHERE username=%s",(self.User,))
        self.UserPriv = cur.fetchone()[0]

        if "Edit" not in self.UserPriv:
            self.UserPriv += ",Edit"
        self._prefix = self.User + "_"

        # make sure clone tables exist
        sqlmakeclone = (
            "CREATE TABLE IF NOT EXISTS {0}basedoc LIKE basedoc",
            "CREATE TABLE IF NOT EXISTS {0}basedoc_history LIKE basedoc_history",
            "CREATE TABLE IF NOT EXISTS {0}requirement LIKE requirement",
            "CREATE TABLE IF NOT EXISTS {0}requirement_history LIKE requirement_history",
            "CREATE TABLE IF NOT EXISTS {0}tests LIKE tests",
            "CREATE TABLE IF NOT EXISTS {0}tests_history LIKE tests_history"
        )
        for sql in sqlmakeclone:
            try:
                cur.execute(sql.format(self._prefix))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

        if not snapshot:                # see if tables already populated
            sql = "SELECT bdseqno FROM {0}basedoc LIMIT 1".format(self._prefix) 
            cur.execute(sql)
            if cur.rowcount <= 0:
                snapshot = True         # clone is empty, need to populate it

        if not snapshot:
            self.Connection.commit()
            # return (True, "Clone database active")
            return (True, "You are now using your existing clone of the live database. " \
                "You can edit this clone, but results will not appear in the live database.")

        # make a snapshot
        sqlmakesnap = (
            "TRUNCATE TABLE {0}basedoc",
            "INSERT INTO {0}basedoc (SELECT * FROM basedoc)",
            "TRUNCATE TABLE {0}basedoc_history",
            "TRUNCATE TABLE {0}requirement",
            "INSERT INTO {0}requirement (SELECT * FROM requirement)",
            "TRUNCATE TABLE {0}requirement_history",
            "TRUNCATE TABLE {0}tests",
            "INSERT INTO {0}tests (SELECT * FROM tests)",
            "TRUNCATE TABLE {0}tests_history"
        )

        for sql in sqlmakesnap:
            try:
                cur.execute(sql.format(self._prefix))
            except pymysql.err.Error as err:
                self.Connection.rollback()
                return (False, err.args[1])

        self.Connection.commit()
        # return (True, "Clone database initialized and active")
        return (True, "You are now using a new clone of the live database. " \
            "You can edit this clone, but results will not appear in the live database.")

    def getclones(self):
        """
        get the list of cloned databases
        """
        if "Comment" in self.UserPriv:
            return (True, [ self.User ]) # only see your own clone
        if "Edit" not in self.UserPriv:
            return (False, "No prefixes for you")
        cur = self.Connection.cursor()
        cur.execute('show tables like "%_basedoc"')
        return (True, [ i[0][:-8] for i in cur.fetchall() ])

    def setprefix(self, prefix):
        """
        set the clone prefix, for comparison and such
        can set it to your own if you're a clone, or to
        anyone if you're not
        """
        if not prefix:
            self._prefix = ""
        else:
            if "Comment" in self.UserPriv and prefix != self.User: # clone users can only see their own clone
                return (False, "Cannot set prefix.")

            cur = self.Connection.cursor()
            cur.execute('show tables like "{0}_basedoc"'.format(prefix))
            if not cur.fetchone():
                return (False, "No such prefix.")
            self._prefix = prefix + "_"
        return (True, "Prefix set")
        
    def dumpdb(self):
        """
        return database as a mysql dump
        Note that this is no longer in use, but might come back later
        """
        import subprocess
        
        if "Comment" in self.UserPriv or "Edit" not in self.UserPriv:
            return (False, "This user is not allowed dump database.")
        DumpCmd = ('mysqldump', '-u', dbuser, '--password={0}'.format(UserPassword), '--databases', dbname)
        try:
            DatabaseAsMySQLText = subprocess.check_output(DumpCmd, universal_newlines=True)
        except Exception as e:
            return (False, "The call to mysqldump returned failure: {}".format(e))
        return (True, DatabaseAsMySQLText)

        
#########################################################################################################
# test stub
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test conformance database')
    parser.add_argument('--userinfo', action='store_true', help="List base docs by string")
    parser.add_argument('--listbd', type=str, help="List base docs by string")
    parser.add_argument('--getbd', type=int, help="Get base doc by seq")
    parser.add_argument('--putbd', type=int, help="Put base doc: seqno, name, rfcno, text, doctype, errata, ediff, thstat, comment, dstat")
    parser.add_argument('--updbd', type=int, help="Update base doc: seqno, name, rfcno, text, doctype, errata, ediff, thstat, comment, dstat")
    parser.add_argument('--delbd', type=int, help="Delete base doc: seqno, comment")
    parser.add_argument('--bdschema', type=str, help="return basedoc schema")
    parser.add_argument('--listreq', type=int, help="List requirement by base doc")
    parser.add_argument('--allreq', help="List all requirements")
    parser.add_argument('--getreq', type=int, help="Get requirement by seq")
    parser.add_argument('--putreq', type=int, help="Put req: rseqno, bdseqno, rstart, rlength, rtext, rtype, rcomment, replaces, replacedby")
    parser.add_argument('--updreq', type=int, help="Put req: rseqno, bdseqno, rstart, rlength, rtext, rtype, rcomment, replaces, replacedby")
    parser.add_argument('--delreq', type=int, help="Delete req: seqno, comment")
    parser.add_argument('--reqschema', type=str, help="return requirement schema")
    parser.add_argument('--listtest', type=int, help="List tests by base doc")
    parser.add_argument('--alltest', help="List all tests")
    parser.add_argument('--gettest', type=int, help="Get test by seq")
    parser.add_argument('--puttest', type=int, help="Put test: rseqno, tseqno, tsameas, ttext, tdut, tlscommand, toutcome, tneg, tcomment, tmasterfile, replaces")
    parser.add_argument('--updtest', type=int, help="Put test: tseqno, rseqno, tsameas, ttext, tdut, tlscommand, toutcome, tneg, tcomment, tmasterfile, replaces, replacedby")
    parser.add_argument('--deltest', type=int, help="Delete test: seqno, comment")
    parser.add_argument('--testschema', type=str, help="return test schema")
    parser.add_argument('--user', type=str, help="User name to blame")
    parser.add_argument('--fulldatabase', type=str, help="Generate full report")
    parser.add_argument('--clone', help="Clone database: active, snapshot")
    parser.add_argument('--getclones', help="List Clone databases")
    parser.add_argument('args', type=str, nargs='*', help="Arguments to store")
    args = parser.parse_args();

    bduser = "demo"
    if args.user:
        bduser = args.user
    print("user is",bduser)

    db = Conformdb(bduser)
    if args.userinfo:
        (ret, val) = db.getuserinfo()
        if ret:
            print(val)
        else:
            print("failed",val)
    if args.listbd:
        (ret, val) = db.listbasedoc(name=args.listbd)
        if ret:
            for doc in val:
                print(doc)
        else:
            print("failed",val)
    if args.getbd:
        (ret, val) = db.getbasedoc(seqno=args.getbd)
        if ret:
            val['bdtext'] = val['bdtext'][:100] + " ..."
            print(val)
        else:
            print("failed",val)

    if args.putbd:
        print(args.args)
        a = [ None if i=='-' else i for i in args.args ]
        bdseqno = None if args.putbd == 999 else args.putbd
        (ret, val) = db.putbasedoc(seqno=bdseqno, name=a[0], rfcno=a[1], text=a[2], doctype=a[3], errata=a[4],
            ediff=a[5], thstat=a[6], comment=a[7], dstat=a[8])
        print("return",ret,val)

    if args.updbd:
        print(args.args)
        a = [ False if i=='-' else i for i in args.args ] # yes, this is a hack
        bdseqno = args.updbd
        (ret, val) = db.updatebasedoc(seqno=bdseqno, name=a[0], rfcno=a[1], text=a[2], doctype=a[3], errata=a[4],
            ediff=a[5], thstat=a[6], comment=a[7], dstat=a[8])
        print("return",ret,val)

    if args.delbd != None:
        print(args.args)
        a = [ None if i=='-' else i for i in args.args ]
        bdseqno = None if args.delbd == 0 else args.delbd
        (ret, val) = db.deletebasedoc(bdseqno=bdseqno, bdcomment=a[0])
        print("return",ret,val)

    if args.bdschema != None:
        print(args.args)
        (ret, val) = db.getbasedocschema()
        print("return",ret,val)

    if args.listreq:
        (ret, val) = db.listrequirement(seqno=args.listreq)
        if ret:
            for doc in val:
                print(doc)
        else:
            print("failed",val)

    if args.allreq:
        (ret, val) = db.listrequirement(getall=True)
        if ret:
            for doc in val:
                print(doc)
        else:
            print("failed",val)

    if args.getreq:
        (ret, val) = db.getrequirement(seqno=args.getreq)
        if ret:
            val['rtext'] = val['rtext'][:100] + " ..."
            print(val)
        else:
            print("failed",val)

    if args.putreq:
        print(args.args)
        a = [ None if i=='-' else i for i in args.args ]
        putreq = None if args.putreq==999 else args.putreq
        (ret, val) = db.putrequirement(rseqno=putreq, bdseqno=a[0], rstart=a[1], rlength=a[2], rtext=a[3],
            rtype=a[4], rcomment=a[5], replaces=a[6], replacedby=a[7])
        print("return",ret,val)

    if args.updreq:
        print(args.args)
        a = [ False if i=='-' else i for i in args.args ] # still a hack
        updreq = None if args.updreq==999 else args.updreq

        (ret, val) = db.updaterequirement(rseqno=updreq, bdseqno=a[0], rstart=a[1], rlength=a[2], rtext=a[3],
            rtype=a[4], rcomment=a[5], replaces=a[6], replacedby=a[7])
        print("return",ret,val)

    if args.delreq != None:
        print(args.args)
        a = [ None if i=='-' else i for i in args.args ]
        rseqno = None if args.delreq == 0 else args.delreq
        (ret, val) = db.deleterequirement(rseqno=rseqno, rcomment=a[0])
        print("return",ret,val)

    if args.reqschema != None:
        print(args.args)
        (ret, val) = db.getrequirementschema()
        print("return",ret,val)

    if args.listtest:
        (ret, val) = db.listtest(bdseqno=args.listtest)
        if ret:
            for doc in val:
                print(doc)
        else:
            print("failed",val)

    if args.alltest:
        (ret, val) = db.listtest(getall=True)
        if ret:
            for doc in val:
                print(doc)
        else:
            print("failed",val)

    if args.gettest:
        (ret, val) = db.gettest(seqno=args.gettest)
        if ret:
            val['ttext'] = val['ttext'][:100] + " ..."
            print(val)
        else:
            print("failed",val)

    if args.puttest:
        print(args.args)
        a = [ None if i=='-' else i for i in args.args ]
        (ret, val) = db.puttest(tseqno=a[0], rseqno=args.puttest, tsameas=a[1], ttext=a[2], tdut=a[3], tlscommand=a[4], toutcome=a[5], tneg=a[6],
        tcomment=a[7], tmasterfile=a[8], replaces=a[9])
        print("return",ret,val)

    if args.updtest:
        print(args.args)
        a = [ False if i=='-' else i for i in args.args ]
        (ret, val) = db.updatetest(tseqno=args.updtest, rseqno=a[0], tsameas=a[1], ttext=a[2], tdut=a[3], tlscommand=a[4], toutcome=a[5], tneg=a[6],
        tcomment=a[7], tmasterfile=a[8], replaces=a[8], replacedby=a[10])
        print("return",ret,val)

    if args.deltest != None:
        print(args.args)
        a = [ None if i=='-' else i for i in args.args ]
        tseqno = None if args.deltest == 0 else args.deltest
        (ret, val) = db.deletetests(tseqno=tseqno, tcomment=a[0])
        print("return",ret,val)

    if args.testschema != None:
        print(args.args)
        (ret, val) = db.gettestschema()
        print("return",ret,val)

    if args.fulldatabase != None:
        print(args.args)
        (ret, val) = db.fulldatabase(args.fulldatabase)
        print("return",ret,val)

    if args.clone:
        print(args.args)
        a = [ False if i=='-' else i for i in args.args ] # yes, this is a hack
        (ret, val) = db.clone(active=a[0], snapshot=a[1])
        print("return",ret,val)

    if args.getclones:
        (ret, val) = db.getclones()
        print("return",ret,val)
