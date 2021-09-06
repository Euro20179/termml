from enum import Enum
from string import ascii_letters, printable
from typing import List, Union, Tuple

GLOBAL_STYLES = {}

class TOKENS(Enum):
    dot = 0
    hashtag = 1
    openCurly = 2
    closeCurly = 3
    comma = 4
    value = 5
    className = 9
    tagName = 10
    idName = 11
    propertyName = 6
    colon = 7
    endProperty = 8
    comment = 12
    pseudoClassValue = 13
    pseudoElementValue = 14

class Token:
    def __init__(self, _type, value):
        self.type = _type
        self.value = value

    def __repr__(self):
        return f'[T:{self.type}: {self.value}]'

class CSSLexer:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tokens = [Token(-1, "")]
        self._i = -1

    def feed(self, text):
        self.reset()
        self.text = text
        self.parse()

    def parse(self):
        inBlock = False
        selectorType = ""
        for char in self:
            if char == ".":
                self.tokens.append(Token(TOKENS.dot, "."))
                selectorType = "class"
            elif char == "#":
                self.tokens.append(Token(TOKENS.hashtag, "#"))
                selectorType = "id"
            elif char == "{":
                self.tokens.append(Token(TOKENS.openCurly, "{"))
                inBlock = True
            elif char == "}":
                self.tokens.append(Token(TOKENS.closeCurly, "}"))
                inBlock = False
                selectorType = ""
            elif char == ":":
                self.tokens.append(Token(TOKENS.colon, ":"))
            elif char == "," and inBlock:
                self.tokens.append(Token(TOKENS.comma, ","))
            elif char == ";" and inBlock:
                self.tokens.append(Token(TOKENS.endProperty, ";"))
            elif char in printable and inBlock and self.tokens[-1].type in (TOKENS.colon, TOKENS.comma):
                self.tokens.append(Token(TOKENS.value, self.createValue(exclude=";,}")))
            elif char in ascii_letters + "-" and inBlock:
                self.tokens.append(Token(TOKENS.propertyName, self.createPropertyName()))
            elif char == "/" and self.previewNext() == "/":
                self.tokens.append(Token(TOKENS.comment, self.createComment()))
                next(self)
            elif char in ascii_letters + "-" and not inBlock and self.tokens[-1].type != TOKENS.colon:
                if not selectorType: tt = TOKENS.tagName
                elif selectorType == "class": tt = TOKENS.className
                elif selectorType == "id": tt = TOKENS.idName
                self.tokens.append(Token(tt, self.createValue(exclude=":;,{ \"'")))
            elif char in ascii_letters + "-" and not inBlock and len(self.tokens) >=2 and self.tokens[-2].type == TOKENS.colon and self.tokens[-1].type == TOKENS.colon:
                self.tokens.append(Token(TOKENS.pseudoElementValue, self.createValue(exclude="{: ")))
            elif char in ascii_letters + "-" and not inBlock and self.tokens[-1].type == TOKENS.colon:
                self.tokens.append(Token(TOKENS.pseudoClassValue, self.createValue(exclude="{: ")))

    def createComment(self):
        text = ""
        while self.currChar not in "\n":
            text += self.currChar
            try: next(self)
            except StopIteration: break
        self.back()
        return text

    def createValue(self, exclude=";,{"):
        name = ""
        inString = ""
        strip = True
        while self.currChar not in exclude or inString:
            if self.currChar in '"\'' and not inString:
                strip = False
                inString = self.currChar
                try: next(self)
                except StopIteration: return name
                continue
            elif inString and self.currChar == inString:
                inString = ""
                try: next(self)
                except StopIteration: return name
                continue
            name += self.currChar
            try: next(self)
            except StopIteration: break
        self.back()
        return name.strip() if strip else name
        
    def createPropertyName(self):
        name = ""
        while self.currChar not in ":};":
            name += self.currChar
            try: next(self)
            except StopIteration: break
        self.back()
        return name.strip()

    def back(self):
        self._i -= 1

    def previewNext(self):
        try: return self.text[self._i + 1]
        except IndexError: return None

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i >= len(self.text):
            raise StopIteration
        self.currChar = self.text[self._i]
        return self.currChar

class Rule:
    def __init__(self, selectorType=None, selectorValue=None, **properties):
        self.selectorType = selectorType
        self.selectorValue = selectorValue
        self.properties = properties
        self.pseudoClasses = []
        self.pseudoElement = ""

    def __repr__(self):
        return f"""{self.selectorType}: {self.selectorValue}{{
    {self.properties}            
}}
"""
    
class CSSParser:
    def __init__(self):
        self.reset()

    def reset(self):
        self.styles = []
        self._i = 1

    def feed(self, tokens):
        self.reset()
        self.tokens = tokens
        self.ruleList = []
        self.parse()

    def selector(self):
        rule = Rule()
        self.ruleList.append(rule)
        if self.currTok.type == TOKENS.tagName:
            rule.selectorType = "tag"
        elif self.currTok.type == TOKENS.idName:
            rule.selectorType = "id"
        elif self.currTok.type == TOKENS.className:
            rule.selectorType = "class"
        rule.selectorValue = self.currTok.value
        next(self)
        if self.currTok.type == TOKENS.colon:
            next(self)
            if self.currTok.type == TOKENS.colon:
                next(self)
                rule.pseudoElement = self.currTok.value
            else: rule.pseudoClasses = self.pseudoClass()
        rule.properties = self.rules()


    def rules(self):
        properties = {}
        currPropertyName = ""
        propertyValue = []
        while self.currTok.type != TOKENS.closeCurly:
            if self.currTok.type == TOKENS.propertyName:
                currPropertyName = self.currTok.value
            elif self.currTok.type == TOKENS.value:
                propertyValue += [self.currTok.value]
            elif self.currTok.type == TOKENS.endProperty:
                properties[currPropertyName] = propertyValue.copy()
                propertyValue.clear()
            next(self)
        self.back()
        return properties

    def pseudoClass(self):
        Class = [self.currTok.value]
        next(self)
        if self.currTok.type == TOKENS.colon:
            next(self)
            Class += self.pseudoClass()
        return Class

         
    def back(self):
        self._i -= 1
        self.currTok = self.tokens[self._i]

    def parse(self):
        for token in self:
            if token.type in (TOKENS.hashtag, TOKENS.dot):
                next(self)
                self.selector()
            elif token.type == TOKENS.tagName:
                self.selector()
                self.pseudoClass()

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i >= len(self.tokens): raise StopIteration
        self.currTok = self.tokens[self._i]
        return self.tokens[self._i]


p = CSSParser()
l = CSSLexer()
def parseStyleSheet(fp):
    with open(fp, "r") as f:
        text = f.read()
    l.feed(text)
    p.feed(l.tokens)
    for rule in p.ruleList:
        GLOBAL_STYLES[(rule.selectorType, rule.selectorValue, tuple(rule.pseudoClasses), rule.pseudoElement)] = rule.properties
    return GLOBAL_STYLES
