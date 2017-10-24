#!/bin/bash

version="1.03"
program=${0##*/}
progdir=${0%/*}

# ----------------------------------------------------------------------
# Utility to find an executable
# ----------------------------------------------------------------------

lookfor() {
    default="$1"; shift
    for b in "$@"; do
	found=$(type -p "$b" 2>/dev/null)
	if [ -n "$found" ]; then
	    if [ -x "$found" ]; then
		echo "$found"
		return
	    fi
	fi
    done
    echo "$default"
}

AWK=$(lookfor gawk gawk nawk awk)

# ----------------------------------------------------------------------
# Strip headers and footers, end-of-line whitespace and \r (CR)
# ----------------------------------------------------------------------
strip() {
    $AWK '
				{ gsub(/\r/, ""); }
				{ gsub(/[ \t]+$/, ""); }

/\[?[Pp]age [0-9ivx]+\]?[ \t\f]*$/{ next;	}

/^[ \t]*\f/			{ newpage=1; next; }

/^ *Internet.Draft.+[12][0-9][0-9][0-9] *$/	{ newpage=1; next; }
/^ *INTERNET.DRAFT.+[12][0-9][0-9][0-9] *$/	{ newpage=1; next; }
/^ *Draft.+[12][0-9][0-9][0-9] *$/		{ newpage=1; next; }
/^RFC.+[0-9]+$/			{ newpage=1; next; }
/^draft-[-a-z0-9_.]+.*[0-9][0-9][0-9][0-9]$/ { newpage=1; next; }
/(Jan|Feb|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|Sep|Oct|Nov|Dec) (19[89][0-9]|20[0-9][0-9]) *$/ && pagelength < 3  { newpage=1; next; }
newpage && $0 ~ /^ *draft-[-a-z0-9_.]+ *$/ { newpage=1; next; }
/^[^ \t]/			{ sentence=1; }
/[^ \t]/			{
				   if (newpage) {
				      if (sentence) {
					 outline++; print "";
				      }
				   } else {
				      if (haveblank) {
					  outline++; print "";
				      }
				   }
				   haveblank=0;
				   sentence=0;
				   newpage=0;
				}
/[.:][ \t]*$/			{ sentence=1; }
/^[ \t]*$/			{ haveblank=1; next; }
				{ outline++; print; }
' $1
}

if [ "$1" = "--version" ]; then
    echo -e "$program\t$version"; exit 0;
fi

strip "$@"
