from html.parser import HTMLParser
from typing import List
from elements import *
from shutil import get_terminal_size

cols, lines = get_terminal_size()
class TMLParser(HTMLParser):
    currTag = document
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
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
        elif tag == "title": e = TitleElement(tag, attrs, parent=self.currTag)
        elif tag == "clear": e = ClearElement(tag, attrs, parent=self.currTag)
        elif tag == "css": e = CSSElement(tag, attrs, parent=self.currTag)
        elif tag == "a": e = AnchorElement(tag, attrs, parent=self.currTag)
        elif tag in ("l", "list"): e = ListElement(tag, attrs, parent=self.currTag)
        elif tag == "uli": 
            if self.currTag.tag == "l":
                try: topGap = 0 if self.currTag.children[-1].tag == "uli" else 1
                except IndexError: topGap = 1
            else: topGap = 1
            e =  UnorderedListElement(tag, attrs, parent=self.currTag, topGap=topGap)
        elif tag == "oli": 
            if self.currTag.tag == "l":
                try: count = self.currTag.getElementChildren()[-1].count + 1
                except IndexError: count = 1
                except AttributeError: count = 1
            else: count = 1
            #setting this top gap, puts 2 olis close to each other
            e = OrderedListElement(tag, attrs, parent=self.currTag, count=count, topGap=0 if count > 1 else 1)
        else: e = Element(tag, attrs, parent=self.currTag)
        self.currTag.addChild(e)
        if not e.selfClosing: self.currTag = e

    def handle_endtag(self, tag):
        if tag not in SELF_CLOSING_TAGS: self.currTag = self.currTag.parent

    def handle_data(self, data):
        if data == "\n": return
        self.currTag.addChild(TextElement(data, self.currTag))
