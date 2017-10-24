#!/usr/bin/env python3

from html import escape
import csv

def mses(s):                            # mysql escape
    return s.replace('\\','\\\\').replace("'","\\'")

class Entable:
    """ turn a csv into html or SQL code
        filename is csv of pseudoformat
        defs is dict of default values to fill in
        csv format is
           Type,fieldname,caption,...
    """
    def __init__(self, filename, defs=None):
        self.csv = []
        if not defs:
            defs = dict()          # empty dictionary

        with open("table/" + filename, "r") as csvf:
            csvr = csv.reader(csvf,delimiter=',')
            for row in csvr:
                if row[0][0] == "#":    # ignore comments
                    continue
                if row[1] in defs and defs[row[1]]:
                    z = row[1]
                    d = str(defs[z]).strip()
                else:
                    d = ""
                #print(" / ".join(row))
                self.csv.append((row[0],row[1],row[2],d,row[3:]))

    def tview(self, doconf=False, noquote=False):
        """ view mode, turn into HTML, flag for confirm mode with hidden fields """
        v = ""
        # type, name, caption, default, everthing else
        for rt,rn,rc,rd,rx in self.csv:
            if rt == 'R':               # readonly, usually timestamp
                if not rd:
                    rd = "(updated)";		
                dv = rd if noquote else escape(rd)
            elif rt == 'O':             # readonly, other stuff
                if not rd:
                    continue    # skip if not defined
                dv = '<br />'.join((rd if noquote else escape(rd)).split("\n"))
            elif rt == 'K':	# komments or kode
                dv = '<br />'.join((rd if noquote else escape(rd)).split("\n"))
            elif rt in ("E","T","LT"):     # enum
                dv = rd if noquote else escape(rd)
            else:
                print("Strange type",rt)

            v += "<tr><td class=e>{0}</td><td class=v>{1}</td></tr>\n".format(rc,dv)
            if doconf and rt not in 'RO':
                v += '<input name="{0}" type=hidden value="{1}">\n'.format(rn,
                    '\\"'.join(rd.split('"')))
        return v
        
    def tviewconf(self):
        """ view confirm mode """
        return self.tview(doconf=True)

    def tedit(self, schema=None):
        """ edit mode, turn into HTML to edit the fields """
        v = ""
        # type, name, caption, default, everthing else
        for rt,rn,rc,rd,rx in self.csv:
            if rt == 'R':               # readonly, usually timestamp
                if not rd:
                    rd = "(updated)";		
                ev = escape(rd)
            elif rt == 'O':             # readonly, other stuff
                if not rd:
                    continue    # skip if not defined
                ev = '<br />'.join(escape(rd).split("\n"))
            elif rt == 'K':	# komments or kode
                ev = u'<textarea name="{0}" cols=90 rows=4>{1}</textarea>\n'.format(rn,escape(rd))
            elif rt == 'E':     # enum
                ev = '<select name="{0}" size=1>\n'.format(rn);
                if not rx:  # get fields from the enum() schema
                    fldschema = schema[rn][0]
                    if fldschema[:6] != "enum('":
                        print("??? funky enum",rn,fldschema)
                    rx = fldschema[6:-2].split("','")
                    if rd and rd not in rx:
                        print("??? no default",rd,"in",rx)
                for i in rx:
                    if rd == i:
                        ev += "<option selected>{0}</option>\n".format(i)
                    else:
                        ev += "<option>{0}</option>\n".format(i)
                ev += "</select>\n"
            elif rt == 'T':     # text
                ev = '<input type=text name="{0}" size=20 value="{1}">\n'.format(rn, escape(rd))
            elif rt == 'TL':     # long text
                ev = '<input type=text name="{0}" size=80 value="{1}">\n'.format(rn, escape(rd))
            else:
                print("Strange type",rt)
            v += "<tr><td class=e>{0}</td><td class=v>{1}</td></tr>\n".format(rc,ev)
        return v

    def tsql(self):
        """ build SQL for insert or update """
        v = ""
        # type, name, caption, default, everthing else
        for rt,rn,rc,rd,rx in self.csv:
            if rt in 'RO':             # readonly, other stuff
                continue    # nothing to change
            elif rt == 'K':	# komments or kode
                fv = filter(lambda c: c != "\r", rd)
                if len(fv) == 0:
                    v += ",{0}=NULL".format(rn)
                else:
                    v += ",{0}='{1}'".format(rn,mses(fv)+"\n")
            elif rt in 'ET':     # text or enum
                v += ",{0}='{1}'".format(rn,mses(rd))
            else:
                print("Strange type",rt)
        return v

# stub for debugging
if __name__=="__main__":
    import argparse

    parser = argparse.ArgumentParser(description='debug entable stuff')
    parser.add_argument('--view', action='store_true', help="HTML to view data");
    parser.add_argument('--viewc', action='store_true', help="HTML to view data and confirm");
    parser.add_argument('--edit', action='store_true', help="HTML to edit data");
    parser.add_argument('--sql', action='store_true', help="produce SQL code");
    parser.add_argument('srccsv', help="Source CSV")
    parser.add_argument('defs', help="Default values name, value", nargs='*')
    args = parser.parse_args();

    d = None
    if args.defs:
        d = dict(zip(*[iter(args.defs)]*2))
    e = Entable(args.srccsv, defs=d)
    print("Created entable")
    if args.view:
        print(e.tview())
        print( "============")
    if args.viewc:
        print(e.tviewconf())
        print("============")
    if args.edit:
        print( e.tedit())
        print("============")
    if args.sql:
        print(e.tsql())
        print("============")
