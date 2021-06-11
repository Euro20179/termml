import parser
import sys
import shutil

lines, cols = shutil.get_terminal_size()

try: file = sys.argv[1]
except Exception:
    print("No file given (use - for stdin)")
    exit(2)

if file == "-":
    html = sys.stdin.read()
else:
    with open(file, "r") as f:
        html = f.read()

p = parser.TMLParser()
p.feed(html)

#print(parser.document.children)

print(parser.parseChildren(parser.document), end="")