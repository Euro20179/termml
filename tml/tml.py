#!/bin/python
try: from tml import parser
except ImportError: 
    print("try installing tml, and running the installed version")
    exit(1)
import sys
import shutil
import argparse
import os

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", help="the file to read from (use - for stdin)")
    p.add_argument("-s", "--safe", help="safe mode, disable the <exec> element", action="store_const", const=True, dest="safeMode")
    args = p.parse_args()
    file = args.file
    os.environ["_TML_SAFEMODE"] = os.environ.get("_TML_SAFEMODE") or str(args.safeMode)
    if file == "-":
        html = sys.stdin.read()
    else:
        with open(file, "r") as f:
            html = f.read()

    p = parser.TMLParser()
    p.feed(html)

#print(parser.document.children)

    print(parser.parseChildren(parser.document), end="")
