from typing import List
import re
import math

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
        elif len(color) == 6:



class Element:
    def __init__(self, tag, attrs, parent=Document, children=None):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List[Element] = children or []
        self.styles = []
        self.gap = 1 #the multiplier for the gap, 1 is normal 2, is twice the default
        self.bottomGap = 1
        self.topGap = 1
        self._parseAtters()
        self.selfClosing = False

    def _parseAtters(self):
        for attr, value in self.attrs:
            if attr == "color":
                color = COLORS.get(value)
                if not color: color = parseColor(value)
                self.styles.append(color)
            elif attr in ("background", "bg", "background-color", "bg-color"):
                color = BACKGROUND_COLORS.get(value)
                if not color: color = parseColor(value)
                self.styles.append(color)
            elif attr == "gap":
                self.gap = int(value)

            elif attr == "top-gap":
                self.topGap = int(value)
            elif attr == "bottom-gap":
                self.bottomGap = int(value)

    def addChild(self, element):
        self.children.append(element) 

    def _calculateNewLines(self, fallback=""):
        if self.topGap != 1:
            topNewLines = "\n" * self.topGap
        elif self.gap != 1:
            topNewLines = "\n" * self.gap
        else: topNewLines = fallback

        if self.bottomGap != 1:
            bottomNewLines = "\n" * self.bottomGap
        elif self.gap != 1:
            bottomNewLines = "\n" * self.gap
        else: bottomNewLines = fallback

        return topNewLines, bottomNewLines

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + parseChildren(self) + bottomLines

    def __repr__(self):
        return f'<{self.tag}{self.attrs}>{self.children}</{self.tag}>'

class BoldElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["bold"])

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[1m" + parseChildren(self) + "\033[0m" + bottomLines

class HRElement(Element):
    def __init__(self, cols, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selfClosing = True
        self.cols = cols

    def render(self):
        topLines, bottomLines = self._calculateNewLines(fallback="\n")
        return topLines + "\033[9m" + (" " * self.cols) + "\033[0m" + bottomLines

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
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[3m" + parseChildren(self) + "\033[0m" + bottomLines

class UnderlineElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["underline"])

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[4m" + parseChildren(self) + "\033[0m" + bottomLines

class BlinkElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["blinking"])

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[5m" + parseChildren(self) + "\033[0m" + bottomLines

class ReverseElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["inverse"])

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[7m" + parseChildren(self) + "\033[0m" + bottomLines

class InvisibleElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["invisible"])

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[8m" + parseChildren(self) + "\033[0m" + bottomLines

class StrikethroughElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles.append(TEXT_STYLES["strikethrough"])

    def render(self):
        topLines, bottomLines = self._calculateNewLines()
        return topLines + "\033[9m" + parseChildren(self) + "\033[0m" + bottomLines

class ParagraphElement(Element):
    def render(self):
        return "\n\n" + parseChildren(self) + ("\n\n" * self.gap)

class BreakElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selfClosing = True
    def render(self):
        return "\n" * self.gap


class TextElement:
    def __init__(self, text, parent=None):
        self.text = re.sub('^\\s*',"", text) #remove pre whitespace
        self.text = re.sub("\\s{2,}$", " ", self.text) #remove excess whitespace after
        self.text = self.text.replace("\n", "") #no new lines
        self.parent = parent
        self.styles = self.parent.styles

    def render(self):
        return self.text + "\033[0m"

    def __repr__(self):
        return f'{self.text}'


def parseChildren(element: Element):
    text = ""
    for child in element.children:
        for style in child.parent.styles:
            text += f'\033[{style}m'
        for style in child.styles:
            text += f'\033[{style}m'
        text += child.render()
    return text

SELF_CLOSING_TAGS = ("br", "hr")