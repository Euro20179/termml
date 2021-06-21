from typing import List
import re
import math
import random
from os import system
from shutil import get_terminal_size
from tml.cssparser import parseStyleSheet, GLOBAL_STYLES
import os

cols, lines = get_terminal_size()

TAB = "^(    )"

def setTab(t):
    global TAB
    TAB = t

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


#TODO: add support for rgb() and hsl() and possibly cymk()
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
    elif color in COLORS.keys():
        if fg: return COLORS[color]
        else: return BACKGROUND_COLORS[color]
    return f"{{INVALID COLOR: {color}}}"

#returns all children of an element that are TextElements
def yieldTextChildren(element):
    for child in element.children:
        if isinstance(child, TextElement):
            yield child
        else:
            yield from yieldTextChildren(child)

def stringToInt(string, default=0):
    if string.isnumeric():
        return int(string)
    return default

class Element:
    def __init__(self, tag, attrs, parent, children=None, **kwargs):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent or document
        self.children: List[Element] = children or []
        self._class = ""
        #styles are things that work in ansi escape sequences, everything else will be an attribute
        #this is a bit redundant, and is a bit messy i'd like to remove it
        self.styles = {}
        self.gap = kwargs.get("gap") or 0 #the multiplier for the gap, 1 is normal 2, is twice the default
        self.bottomGap = kwargs.get("bottomGap") or 0
        self.topGap = kwargs.get("topGap") or 0
        self.textCase = kwargs.get("textCase") or "auto"
        self.x = kwargs.get("x") or "auto"
        self.whitespace = kwargs.get("whitespace") or "auto"
        self.preText = kwargs.get('preText') or ""
        self.preText = str(self.preText)
        self.postText = kwargs.get("postText") or ""
        self.postText = str(self.postText)
        self.specialAttrs = kwargs.get("specialAttrs", {})
        self.selfClosing = False
        self.inherit = parent.inherit;
        if not isinstance(self, BeforeElement) and not isinstance(self, AfterElement): self.before = BeforeElement("::before", [], self)
        if not isinstance(self, BeforeElement) and not isinstance(self, AfterElement): self.after = AfterElement("::after", [], self)

    def getElementChildren(self):
        return tuple(x for x in self.children if not isinstance(x, TextElement))

    def getFirstChild(self, element=None):
        for child in self.children:
            if isinstance(child, TextElement): continue
            if not element or element == child.tag: return child

    def getLastChild(self, element=None):
        for child in self.children[::-1]:
            if isinstance(child, TextElement): continue
            if not element or element == child.tag: return child

    def parseGlobalStyles(self):
        for selector, properties in GLOBAL_STYLES.items():
            _, _, pc, pe = selector
            if "no-inherit" in pc: self.inherit = False
            if self.matchesSelector(selector):
                instance = self
                if pe:
                    if pe == "before": instance = self.before
                    elif pe == "after": instance = self.after
                for attr, value in properties.items():
                    if attr != "text-style":
                        value = value[0]
                        instance._parseAttrs([(attr, value)])
                    elif attr == "text-style":
                        for i in value:
                            instance._parseAttrs([(attr, i)])

    def _parseAttrs(self, attrs=None):
        for attr, value in (attrs or self.attrs):
            value = str(value)
            attr = attr.lower()
            if attr == "color":
                color = COLORS.get(value)
                if not color: color = parseColor(value)
                self.styles["color"] = color
            elif attr in ("background", "bg", "background-color", "bg-color"):
                color = BACKGROUND_COLORS.get(value)
                if not color: color = parseColor(value, False)
                self.styles["background"] = color
            #text-style is a list of text styles, (bold, italic, etc)
            #any css element that will be comma separated will be a list
            elif attr == "text-style":
                if not self.styles.get("text-style"): self.styles["text-style"] = []
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
            elif attr == "pre-text":
                self.before.children.append(TextElement(value, self.before))
            elif attr == "post-text":
                self.after.children.append(TextElement(value, self.after))
            elif attr in self.specialAttrs.keys():
                self.specialAttrs[attr](value)

    def addChild(self, element):
        self.children.append(element) 

    #this will get called after inline styles are applied,
    #so it checks to make sure that that isn't true
    def _setInitialColor(self, color):
        if not self.styles.get("color"):
            self.styles["color"] = color

    def _setInitialBGColor(self, color):
        if not self.styles.get("background"):
            self.styles["background"] = color

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
        yield topLines
        yield parseChildren(self.before)

    def renderPreText(self):
        yield "\033[0m"
        for style in self.styles.items():
            yield from Element.renderStyle(style)

    def renderPostText(self):
        yield "\033[0m"
        yield parseChildren(self.after)

    def matchesSelector(self, selector):
        t, value, pc, pe = selector
        if "first-child" in pc:
            firstChild = self.parent.getFirstChild()
            if firstChild and id(firstChild) != id(self):
                return False
        if "last-child" in pc:
            lastChild = self.parent.getLastChild()
            if lastChild and id(lastChild) != id(self):
                return False
        if "first-instance" in pc:
            firstInstance = self.parent.getFirstChild(element=self.tag)
            if firstInstance and id(firstInstance) != id(self): return False
        elif "last-instance" in pc:
            lastInstance = self.parent.getLastChild(element=self.tag)
            if lastInstance and id(lastInstance) != id(self): return False
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

class BeforeElement(Element):
    pass

class AfterElement(Element):
    pass

class Document(Element):
    def __init__(self, children):
        self.parent = None
        self.children = children
        self.innerHTML = ""
        self.styles = {}
        self.textCase = "auto"
        self.x = "auto"
        self.whitespace = "auto"
        self.tag = "!DOCUMENT"
        self.preText = ""
        self.inherit = True

    def addChild(self, element):
        self.children.append(element)

    def __repr__(self):
        return "<DOCUMENT>"

document = Document([])

class ExecElement(Element):
    def __init__(self, *args, **kwargs):
        self.cache = True
        super().__init__(*args, specialAttrs={
            "no-cache": setattr(self, "cache", False)
            }, **kwargs)
        self.args = ""
        self.execCache = None

    def addArg(self, arg):
        self.args += arg

    def execute(self):
        if not self.args: return ""
        if eval(os.environ.get("_TML_SAFEMODE")): return ""
        if self.execCache is None and self.cache:
            self.execCache = os.popen(self.args).read()
        elif not self.cache:
            return os.popen(self.args).read()
        return self.execCache

class ArgElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, specialAttrs={
            "value": lambda v: self.parent.addArg(v + " "),
            "v": lambda v: self.parent.addArg(v + " "),
            "all": lambda v: setattr(self.parent, "args", self.parent.args + v)
            }, **kwargs)
        self.selfClosing = True

class OutputElement(Element):
    def __init__(self, *args, **kwargs):
        self.replace = ""
        super().__init__(*args, specialAttrs={
            "replace": lambda v: setattr(self, "replace", v)
            }, whitespace="pre", **kwargs)

    def preRender(self, *args):
        output = self.parent.execute()
        if not self.replace: self.children.append(TextElement(output, self))
        else:
            for child in yieldTextChildren(self):
                if child:
                    child.text = child.text.replace(self.replace, output)
        yield from super().preRender(*args)


class AnchorElement(Element):
    def __init__(self, *args, **kwargs):
        self.linkColor = COLORS["blue"]
        super().__init__(*args, specialAttrs={
            "link-color": lambda v: setattr(self, "linkColor", parseColor(v)),
            "href": lambda v: setattr(self, "href", v)
            }, **kwargs)
        self._setInitialColor(COLORS["blue"])

    def render(self):
        if getattr(self, "href", None) is not None:
            yield f'[{parseChildren(self)}\033[{self.styles["color"]}m]\033[{self.linkColor}m({self.href})\033[0m'
        else:
            yield f'{parseChildren(self)}\033[0m'

class ListElement(Element):
    pass

class OrderedListElement(Element):
    def __init__(self, *args, count=1, topGap=1, **kwargs):
        self.count = count
        super().__init__(*args, **kwargs, bottomGap=1, topGap=topGap, preText=str(self.count) + " ")

class UnorderedListElement(Element):
    def __init__(self, *args, marker="* ", topGap=0, **kwargs):
        super().__init__(*args, **kwargs, bottomGap=1, topGap=topGap, preText=marker)

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

class HeaderElement(Element):
    def __init__(self, tag, *args, **kwargs):
        super().__init__(tag, *args, **kwargs, gap=1)
        self.count = int(tag.strip("h"))
        self.preColor = self._getPreColor()

    def _getPreColor(self):
        if self.count == 1:
            return f'\033[{parseColor("#92F6C7")}m'
        elif self.count == 2: 
            return f'\033[{parseColor("#11C6C7")}m'
        elif self.count == 3:
            return f'\033[{parseColor("#00687A")}m'
        elif self.count == 4:
            return f'\033[{parseColor("#525596")}m'
        elif self.count == 5:
            return f'\033[{parseColor("#5B3575")}m'
        elif self.count == 6:
            return f'\033[{parseColor("#501F34")}m'
        return f'\033[{parseColor("#343434")}m'

    def renderPreText(self):
        yield self.preColor
        if self.count > 1:
            yield f'██{"█" * (self.count - 1)} '
        else: yield "██ "

class ParagraphElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, gap=1)

class BreakElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, topGap=1)
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
        super().__init__(*args, specialAttrs={"href": lambda v: parseStyleSheet(v)}, **kwargs)
        self.selfClosing = True

class BlackElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["black"])

class BGBlackElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["black"])

class RedElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["red"])

class BGRedElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["red"])

class GreenElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["green"])

class BGGreenElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["green"])

class YellowElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["yellow"])

class BGYellowElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["yellow"])

class BlueElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["blue"])

class BGBlueElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["blue"])

class MagentaElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["magenta"])

class BGMagentaElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["magenta"])

class CyanElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["cyan"])

class BGCyanElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["cyan"])

class WhiteElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialColor(COLORS["white"])

class BGWhiteElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setInitialBGColor(BACKGROUND_COLORS["white"])

class MetaElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, specialAttrs={
            "tab": lambda v: setTab(v),
            "href": lambda v: parseStyleSheet(v)
            }, **kwargs)
        self.selfClosing = True

class TextElement:
    def __init__(self, text, parent=None):
        self.parent = parent
        self.text = text
        self.tag = "textNode"
        self.styles = self.parent.styles

    def _calculateX(self):
        pos = self.parent.x
        if pos == "auto": return 0
        if type(pos) == int or pos.isnumeric(): return int(pos)
        if pos == "center":
            return (cols // 2) - round(len(self.text) / 2)

    def _calcWhitespace(self):
        self.text = re.sub(TAB, "", self.text, flags=re.MULTILINE)
        if self.parent.whitespace == "auto":
            self.text = re.sub('\\s{2,}'," ", self.text) #remove pre whitespace
            self.text = re.sub('^\\s*',"", self.text) #remove pre whitespace
            self.text = self.text.replace("\n", "") #no new lines

    def _calculateNewLines(self):
        return "", ""

    def preRender(self, topLines):
        x = self._calculateX()
        if not x: yield ""
        else: yield f"\033[{x}G"

    def renderPreText(self):
        yield ""

    def renderPostText(self):
        yield ""

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

def renderStyles(child):
    for style in child.parent.styles.items():
        if child.parent.inherit:
            for r in Element.renderStyle(style):
                yield r


def parseChildren(element: Element):
    text = ""
    for child in element.children:
        #apply styles to elements if not TextElement
        if not isinstance(child, TextElement):
            child._parseAttrs()
            child.parseGlobalStyles()
        else:
            child._calcWhitespace()
        #renders the styles 3 times (before start, before main, before end) in case they are cleared
        for style in renderStyles(child):
            text += style
        topLines, bottomLines = child._calculateNewLines()
        #preRender should render stuff like \033[31m (colors/ansi escapes) and newLines
        #postRender should render \033[0m and newLines
        #preRenderText should render text that comes before the main text (similar to ::before in css)
        #render should render the main text in the element
        #postRenderText should render text that comes after to the main text (similar to ::after in css)
        for t in child.preRender(topLines): text += t
        for style in renderStyles(child):
            text += style
        for t in child.renderPreText(): text += t
        for style in renderStyles(child):
            text += style
        for t in child.render(): text += t
        for t in child.renderPostText(): text += t
        for t in child.postRender(bottomLines): text += t

    return text

SELF_CLOSING_TAGS = ("br", "hr", "clear", "css", "arg", "meta")
