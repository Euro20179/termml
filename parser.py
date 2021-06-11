from html.parser import HTMLParser
from typing import List
from elements import *
from shutil import get_terminal_size

cols, lines = get_terminal_size()
class TMLParser(HTMLParser):
    currTag = document
    def handle_starttag(self, tag, attrs):
        if tag in ("b", "bold", "strong"): e = BoldElement(tag, attrs, parent=self.currTag)
        elif tag in ("d", "dim"): e = DimElement(tag, attrs, parent=self.currTag)
        elif tag in ("i", "italic", "em", "emphasis"): e = ItalicElement(tag, attrs, parent=self.currTag)
        elif tag in ("u", "underline"): e = UnderlineElement(tag, attrs, parent=self.currTag)
        elif tag == "blink": e = BlinkElement(tag, attrs, parent=self.currTag)
        elif tag in ("negative", "inverse"): e = ReverseElement(tag, attrs, parent=self.currTag)
        elif tag in ("invisible", "inv"): e = InvisibleElement(tag, attrs, parent=self.currTag)
        elif tag in ("s", "strikethrough", "del"): e = StrikethroughElement(tag, attrs, parent=self.currTag)
        elif tag == "p": e = ParagraphElement(tag, attrs, parent=self.currTag)
        elif tag == "br": e = BreakElement(tag, attrs, parent=self.currTag)
        elif tag == "hr": e = HRElement(cols, tag, attrs, parent=self.currTag)
        else: e = Element(tag, attrs, parent=self.currTag)
        self.currTag.addChild(e)
        if not e.selfClosing: self.currTag = e

    def handle_endtag(self, tag):
        if tag not in SELF_CLOSING_TAGS: self.currTag = self.currTag.parent

    def handle_data(self, data):
        self.currTag.addChild(TextElement(data, self.currTag))
