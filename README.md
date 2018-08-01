Usage
=====

+ `arm-none-eabi-objdump -SD -j .text BINARY.elf  | python3 ~/objdump2html/objdump2html.py  > out.html`
+ Open `out.html` in browser

Limitations
==========
Currently only supports ARM objdump outputs.