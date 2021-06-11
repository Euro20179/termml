from typing import List
import re
import math
from os import system
from shutil import get_terminal_size

cols, lines = get_terminal_size()

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

class Document:
    def __init__(self, children):
        self.Parent = None
        self.children = children
        self.innerHTML = ""
        self.styles = tuple()
        self.textCase = "auto"
        self.x = "auto"
        self.whitespace = "auto"
        self.tag = "!DOCUMENT"

    def addChild(self, element):
        self.children.append(element)

    def __repr__(self):
        return "<!DOCUMENT>"

document = Document([])

def parseColor(color):
    if color[-1] == "m":
        return color.strip("m")
    elif color[0] == "#":
        color = color[1:]
        if len(color) == 3:
            r, g, b = color
            r = int(r, 16) * math.floor(256 / 15)
            g = int(g, 16) * math.floor(256 / 15)
            b = int(b, 16) * math.floor(256 / 15)
            return f'38;2;{r};{g};{b}'

def stringToInt(string, default=0):
    if string.isnumeric():
        return int(string)
    return default

class Element:
    def __init__(self, tag, attrs, parent=Document, children=None, **kwargs):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List[Element] = children or []
        self.styles = []
        self.gap = kwargs.get("gap") or 0 #the multiplier for the gap, 1 is normal 2, is twice the default
        self.bottomGap = kwargs.get("bottomGap") or 0
        self.topGap = kwargs.get("topGap") or 0
        self.textCase = kwargs.get("textCase") or "auto"
        self.x = kwargs.get("x") or "auto"
        self.whitespace = "auto"
        self._parseAttrs()
        self.selfClosing = False

    def _parseAttrs(self):
        for attr, value in self.attrs:
            attr = attr.lower()
            if attr == "color":
                color = COLORS.get(value)
                if not color: color = parseColor(value)
                self.styles.append(("fg", color))
            elif attr in ("background", "bg", "background-color", "bg-color"):
                color = BACKGROUND_COLORS.get(value)
                if not color: color = parseColor(value)
                self.styles.append(("bg", color))
            elif attr in ("bold", "b"):
                self.styles.append(("text-style", TEXT_STYLES["bold"]))
            elif attr in ("d", "dim"):
                self.styles.append(("text-style", TEXT_STYLES["dim"]))
            elif attr in ("italic", "i"): 
                self.styles.append(("text-style", TEXT_STYLES["italic"]))
            elif attr in ("underline", "u"):
                self.styles.append(("text-style", TEXT_STYLES["underline"]))
            elif attr == "blink":
                self.styles.append(("text-style", TEXT_STYLES["blinking"]))
            elif attr in ("negative", "inverse"):
                self.styles.append(("text-style", TEXT_STYLES["inverse"]))
            elif attr in ("invisible", "inv", "hidden"):
                self.styles.append(("text-style", TEXT_STYLES["invisible"]))
            elif attr in ("strikethrough", "s"):
                self.styles.append(("text-style", TEXT_STYLES["strikethrough"]))
            elif attr == "whitespace":
                self.whitespace = value
            elif attr == "gap":
                self.gap = stringToInt(value)
            elif attr == "top-gap":
                self.topGap = stringToInt(value)
            elif attr == "bottom-gap":
                self.bottomGap = stringToInt(value)
            elif attr == "text-case":
                self.textCase = value
            elif attr == "x":
                self.x = stringToInt(value)

    def addChild(self, element):
        self.children.append(element) 

    def _calculateNewLines(self, fallback=""):
        if self.topGap != 0:
            topNewLines = "\n" * self.topGap
        elif self.gap != 0:
            topNewLines = "\n" * self.gap
        else: topNewLines = fallback

        if self.bottomGap != 0:
            bottomNewLines = "\n" * self.bottomGap
        elif self.gap != 0:
            bottomNewLines = "\n" * self.gap
        else: bottomNewLines = fallback

        return topNewLines, bottomNewLines

    @staticmethod
    def renderStyle(style):
        name, value = style
        if name in ("fg", "bg", "text-style"): 
            yield f"\033[{value}m"
        elif name == "cursor-location":
            yield f'\033[{value}'

    def preRender(self, topLines):
        for style in self.styles:
            yield from Element.renderStyle(style)
        yield topLines

    def render(self):
        yield parseChildren(self)

    def postRender(self, bottomLines):
        yield bottomLines

    def __repr__(self):
        return f'<{self.tag}{self.attrs}>{self.children}</{self.tag}>'

class BoldElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["bold"]))

class TitleElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, gap=1, textCase="upper", x="center")
        self.styles.append(("text-style", TEXT_STYLES["underline"]))

class HRElement(Element):
    def __init__(self, cols, *args, **kwargs):
        super().__init__(*args, **kwargs, gap=1)
        self.selfClosing = True
        self.cols = cols
        self.styles.append(("text-style", "9"))

    def render(self):
        yield " " * self.cols

class DimElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["dim"]))
class ItalicElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["italic"]))

class UnderlineElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["underline"]))

class BlinkElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["blinking"]))

class ReverseElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["inverse"]))

class InvisibleElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["invisible"]))

class StrikethroughElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(("text-style", TEXT_STYLES["strikethrough"]))

class ParagraphElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, gap=1)

class BreakElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selfClosing = True
    def render(self):
        yield "\n" * self.gap

class ClearElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        system("clear")
        self.selfClosing = True


class TextElement:
    def __init__(self, text, parent=None):
        self.parent = parent
        self.text = text
        if self.parent.whitespace == "auto":
            self.text = re.sub('\\s{2,}',"", self.text) #remove pre whitespace
            self.text = self.text.replace("\n", "") #no new lines
        self.styles = self.parent.styles

    def _calculateX(self):
        pos = self.parent.x
        if pos == "auto": return 0
        if type(pos) == int or pos.isnumeric(): return int(pos)
        if pos == "center":
            return cols // 2 - len(self.text)


    def _calculateNewLines(self):
        return "", ""

    def preRender(self, topLines):
        x = self._calculateX()
        if not x: yield ""
        else: yield f"\033[{x}G"

    def render(self):
        if self.parent.textCase in ("capital", "upper"):
            yield self.text.upper()
        elif self.parent.textCase in ("lowercase", "lower"):
            yield self.text.lower()
        else: yield self.text + "\033[0m"

    def postRender(self, bottomLines):
        yield ""

    def __repr__(self):
        return f'{self.text}'


def parseChildren(element: Element):
    text = ""
    for child in element.children:
        for style in child.parent.styles:
            for r in Element.renderStyle(style):
                text += r
        topLines, bottomLines = child._calculateNewLines()
        for t in child.preRender(topLines):
            text += t
        for t in child.render(): text += t
        for t in child.postRender(bottomLines): text += t
    return text

SELF_CLOSING_TAGS = ("br", "hr", "clear")
