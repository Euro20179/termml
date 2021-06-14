from typing import List
import re
import math
import random
from os import system
from shutil import get_terminal_size
from cssparser import parseStyleSheet, GLOBAL_STYLES

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
        self.styles = {}
        self.textCase = "auto"
        self.x = "auto"
        self.whitespace = "auto"
        self.tag = "!DOCUMENT"

    def addChild(self, element):
        self.children.append(element)

    def __repr__(self):
        return "<!DOCUMENT>"

document = Document([])

def parseColor(color, fg=True):
    if color[-1] == "m":
        return color.strip("m")
    elif color[0] == "#":
        try:
            color = color[1:]
            if len(color) == 3:
                r, g, b = color
                r = int(r, 16) * math.floor(256 / 15)
                g = int(g, 16) * math.floor(256 / 15)
                b = int(b, 16) * math.floor(256 / 15)
            elif len(color) in (6, 8):
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
            return f'38;2;{r};{g};{b}' if fg else f'48;2;{r};{g};{b}'
        except Exception: pass
    return "{{INVALID COLOR}"

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
        self._class = ""
        self.styles = {}
        self.gap = kwargs.get("gap") or 0 #the multiplier for the gap, 1 is normal 2, is twice the default
        self.bottomGap = kwargs.get("bottomGap") or 0
        self.topGap = kwargs.get("topGap") or 0
        self.textCase = kwargs.get("textCase") or "auto"
        self.x = kwargs.get("x") or "auto"
        self.whitespace = "auto"
        self._parseAttrs()
        self.selfClosing = False
        self.parseGlobalStyles()

    def parseGlobalStyles(self):
        for selector, properties in GLOBAL_STYLES.items():
            if self.matchesSelector(selector):
                for attr, value in properties.items():
                    if attr != "text-style":
                        value = value[0]
                    self._parseAttrs([(attr, value)])

    def _parseAttrs(self, attrs=None):
        for attr, value in (attrs or self.attrs):
            attr = attr.lower()
            if attr == "color":
                color = COLORS.get(value)
                if not color: color = parseColor(value)
                self.styles["color"] = color
            elif attr in ("background", "bg", "background-color", "bg-color"):
                color = BACKGROUND_COLORS.get(value)
                if not color: color = parseColor(value, False)
                self.styles["background"] = color
            elif attr == "text-style":
                self.styles["text-style"] = []
                if isinstance(value, str):
                    value = value.split(",")
                for v in value:
                    v = v.strip()
                    if v in ("bold", "b"):
                        self.styles["text-style"].append(TEXT_STYLES["bold"])
                    elif v in ("d", "dim"):
                        self.styles["text-style"].append(TEXT_STYLES["dim"])
                    elif v in ("i", "italic"):
                        self.styles["text-style"].append(TEXT_STYLES["italic"])
                    elif v in ("u", "underline"):
                        self.styles["text-style"].append(TEXT_STYLES["underline"])
                    elif v == "blink":
                        self.styles["text-style"].append(TEXT_STYLES["blink"])
                    elif v in ("negative", "inverse"):
                        self.styles["text-style"].append(TEXT_STYLES["inverse"])
                    elif v in ("invisible", "inv", "hidden"):
                        self.styles["text-style"].append(TEXT_STYLES["invisible"])
                    elif v in ("s", "strikethrough"):
                        self.styles["text-style"].append(TEXT_STYLES["strikethrough"])
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
                if value == "center": self.x = "center"
                else: self.x = stringToInt(value)
            elif attr == "cursor-location":
                self.styles["cursor-location"] = value
            elif attr == "class": 
                self._class = value

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
        if not isinstance(style, list) and not isinstance(style, tuple): return ""
        name, value = style
        if name in ("color", "background", "text-style"): 
            if isinstance(value, list):
                for v in value:
                    yield f"\033[{v}m"
            else: yield f"\033[{value}m"
        elif name == "cursor-location":
            if isinstance(value, list):
                for v in value:
                    yield f"\033[{v}m"
            else: yield f'\033[{value}'

    def preRender(self, topLines):
        for style in self.styles.items():
            yield from Element.renderStyle(style)
        yield topLines

    def matchesSelector(self, selector):
        t, value = selector
        if t == "tag" and self.tag == value:
            return True
        elif t == "class" and self._class == value:
            return True
        return False

    def render(self):
        yield parseChildren(self)

    def postRender(self, bottomLines):
        yield bottomLines

    def __repr__(self):
        return f'<{self.tag}{self.attrs}>{self.children}</{self.tag}>'

class BoldElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["bold"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["bold"]]

class TitleElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, gap=1, textCase="upper", x="center")
        try: self.styles["text-style"].append(TEXT_STYLES["underline"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["underline"]]

class HRElement(Element):
    def __init__(self, cols, *args, **kwargs):
        super().__init__(*args, **kwargs, gap=1)
        self.selfClosing = True
        self.cols = cols
        try: self.styles["text-style"].append(TEXT_STYLES["strikethrough"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["strikethrough"]]

    def render(self):
        yield " " * self.cols

class DimElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["dim"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["dim"]]

class ItalicElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["italic"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["italic"]]

class UnderlineElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["underline"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["underline"]]

class BlinkElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["underline"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["underline"]]

class ReverseElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["inverse"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["inverse"]]
        

class InvisibleElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["invisible"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["invisible"]]

class StrikethroughElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try: self.styles["text-style"].append(TEXT_STYLES["strikethrough"])
        except KeyError: self.styles["text-style"] = [TEXT_STYLES["strikethrough"]]

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

class CSSElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.attrs:
            if k == "href":
                parseStyleSheet(v)
                break
        self.selfClosing = True

class TextElement:
    def __init__(self, text, parent=None):
        self.parent = parent
        self.text = text
        self.tag = "textNode"
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
        elif self.parent.textCase == "random":
            yield "".join((x.upper() if random.random() > .5 else x.lower() for x in self.text))
        elif self.parent.textCase == "mix":
            yield "".join((x.upper() if i % 2 == 0 else x.lower() for i, x in enumerate(self.text)))
        else: yield self.text + "\033[0m"

    def postRender(self, bottomLines):
        yield ""

    def __repr__(self):
        return f'{self.text}'


def parseChildren(element: Element):
    text = ""
    for child in element.children:
        for style in child.parent.styles.items():
            for r in Element.renderStyle(style):
                text += r
        topLines, bottomLines = child._calculateNewLines()
        for t in child.preRender(topLines):
            text += t
        for t in child.render(): text += t
        for t in child.postRender(bottomLines): text += t
    return text

SELF_CLOSING_TAGS = ("br", "hr", "clear", "css")