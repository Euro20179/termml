import parser
import sys
import shutil

try: file = sys.argv[1]
except Exception:
    file = "test.tml"
#    print("No file given (use - for stdin)")
#    exit(2)


if file == "-":
    html = sys.stdin.read()
else:
    with open(file, "r") as f:
        html = f.read()

p = parser.TMLParser()
p.feed(html)

#print(parser.document.children)

print(parser.parseChildren(parser.document), end="")