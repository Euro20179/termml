# TML

tml is a markup language specifically designed to be displayed in terminals, it is interpreted at runtime with `tml.py` however you can write the output to a file, although it will be missing features.

*WARNING:* currently this program will not work unless you install it

Features missing when not interprated at runtime
* hr (horizontal rules), the length is calculated at runtime, so if written, the line may be too long/short
* title, the center position is calculated at runtime, may be off when written to a file

## Installation

```sh
git clone https://github.com/euro20179/tml
cd tml
make install
```

Uninstall:
```sh
make uninstall
```

or

```sh
pip uninstall tml
```

### Example

a sample tml file
```tml
<p color="blue">Hello</p>
<br>
<b>some bold text</b>
<br>
<i>some italic text</i>
```

### How it works
the interprater uses python's builtin html.parser module to parse html, therefore comments, entities (`&lt;`), and anything else like that should work
