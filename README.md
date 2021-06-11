# TML

tml is a markup language specifically designed to be displayed in terminals, it is interpreted at runtime with `main.py` however you can write the output to a file, although it will be missing features.

Features missing when not interprated at runtime
* hr (horizontal rules), the length is calculated at runtime, so if written, the line may be too long/short

a sample tml file
```tml
<p color="blue">Hello</p>
<br>
<b>some bold text</b>
<br>
<i>some italic text</i>
```
