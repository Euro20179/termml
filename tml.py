#!/bin/python
import parser
import sys
import shutil
import argparse

p = argparse.ArgumentParser()
p.add_argument("file", help="the file to read from (use - for stdin)")
args = p.parse_args()
file = args.file

if file == "-":
    html = sys.stdin.read()
else:
    with open(file, "r") as f:
        html = f.read()

p = parser.TMLParser()
p.feed(html)

#print(parser.document.children)

print(parser.parseChildren(parser.document), end="")
