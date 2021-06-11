from html.parser import HTMLParser
from typing import List

class Document:
    def __init__(self, children):
        self.Parent = None
        self.children = children
        self.innerHTML = ""
        self.styles = tuple()

    def addChild(self, element):
        self.children.append(element)

    def __repr__(self):
        return "<!DOCUMENT>"

document = Document([])

COLORS = {
    "black": "30",
    "default": "0",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37"
}

BACKGROUND_COLORS = {
    "black": "40",
    "red": "41",
    "green": "42",
    "yellow": "43",
    "blue": "44",
    "magenta": "45",
    "cyan": "46",
    "white": "47",
    "default": "0"
}

TEXT_STYLES = {
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
    "blinking": "5",
    "inverse": "7",
    "invisible": "8",
    "strikethrough": "9"
}

class Element:
    def __init__(self, tag, attrs, parent=Document, children=None):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List[Element] = children or []
        self.styles = []
        self.gap = 1 #the multiplier for the gap, 1 is normal 2, is twice the default
        self._parseAtters()
        self.selfClosing = False

    def _parseAtters(self):
        for attr, value in self.attrs:
            if attr == "color":
                color = COLORS.get(value)
                if not color: continue
                self.styles.append(color)
            elif attr in ("background", "bg", "background-color", "bg-color"):
                color = BACKGROUND_COLORS.get(value)
                if not color: continue
                self.styles.append(color)
            elif attr == "gap":
                self.gap = int(value)

    def addChild(self, element):
        self.children.append(element) 

    def render(self): return ""

    def __repr__(self):
        return f'<{self.tag}{self.attrs}>{self.children}</{self.tag}>'

def parseChildren(element: Element):
    text = ""
    for child in element.children:
        for style in child.parent.styles:
            text += f'\033[{style}m'
        for style in child.styles:
            text += f'\033[{style}m'
        text += child.render()
    return text

class BoldElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["bold"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[1m" + parseChildren(self) + "\033[0m" + newLines

class DimElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["dim"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[2m" + parseChildren(self) + "\033[0m" + newLines

class ItalicElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["italic"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[3m" + parseChildren(self) + "\033[0m" + newLines

class UnderlineElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["underline"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[4m" + parseChildren(self) + "\033[0m" + newLines

class BlinkElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["blinking"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[5m" + parseChildren(self) + "\033[0m" + newLines

class ReverseElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["inverse"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[7m" + parseChildren(self) + "\033[0m" + newLines

class InvisibleElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["invisible"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[8m" + parseChildren(self) + "\033[0m" + newLines

class StrikethroughElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["strikethrough"])

    def render(self):
        newLines = "\n" * self.gap if self.gap != 1 else ""
        return "\033[9m" + parseChildren(self) + "\033[0m" + newLines

class ParagraphElement(Element):
    def render(self):
        return parseChildren(self) + ("\n\n" * self.gap)

class BreakElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selfClosing = True
    def render(self):
        return "\n" * self.gap


class TextElement:
    def __init__(self, text, parent=None):
        self.text = text.strip()
        self.parent = parent
        self.styles = self.parent.styles

    def render(self):
        return self.text + "\033[0m"

    def __repr__(self):
        return f'{self.text}'

class TMLParser(HTMLParser):
    currTag = document
    def handle_starttag(self, tag, attrs):
        if tag == "b": e = BoldElement(tag, attrs, parent=self.currTag)
        elif tag == "d": e = DimElement(tag, attrs, parent=self.currTag)
        elif tag == "i": e = ItalicElement(tag, attrs, parent=self.currTag)
        elif tag == "u": e = UnderlineElement(tag, attrs, parent=self.currTag)
        elif tag == "blink": e = BlinkElement(tag, attrs, parent=self.currTag)
        elif tag == "reverse": e = ReverseElement(tag, attrs, parent=self.currTag)
        elif tag == "invisible": e = InvisibleElement(tag, attrs, parent=self.currTag)
        elif tag == "s": e = StrikethroughElement(tag, attrs, parent=self.currTag)
        elif tag == "p": e = ParagraphElement(tag, attrs, parent=self.currTag)
        elif tag == "br": e = BreakElement(tag, attrs, parent=self.currTag)
        else: e = Element(tag, attrs, parent=self.currTag)
        self.currTag.addChild(e)
        if not e.selfClosing: self.currTag = e

    def handle_endtag(self, tag):
        self.currTag = self.currTag.parent

    def handle_data(self, data):
        self.currTag.addChild(TextElement(data, self.currTag))