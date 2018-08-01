
import sys
import re
import xml.sax.saxutils as _saxutils
import pprint


class ISA:
    def is_func_def(self, line: str):
        raise NotImplemented

    def get_func_def_name(self, line: str):
        raise NotImplemented

    def is_func_call(self, line: str):
        raise NotImplemented

    def get_func_call_name(self, line: str):
        raise NotImplemented

    def is_section_start(self, line: str):
        raise NotImplemented

    def get_section_name(self, line: str):
        raise NotImplemented

RE_FUNC = "<([a-zA-Z_]+)>"
RE_FUNC_DEF = "[0-9a-z]+ <([a-zA-Z_]+)>:"
RE_FUNC_CALL = "bl +[0-9a-z]+ <([a-zA-Z_]+)>"
S_SECTION_START = "Disassembly of section"
RE_SECTION_NAME = "Disassembly of section .([a-z\._A-Z0-9]+)"

class ARM(ISA):
    def __init__(self):
        self.re_func_def = re.compile(RE_FUNC_DEF)
        self.re_func_call = re.compile(RE_FUNC)
        self.re_sec_name = re.compile(RE_SECTION_NAME)

    def is_func_def(self, line):
        res_func_def = self.re_func_def.findall(line)
        return res_func_def != []

    def get_func_def_name(self, line: str):
        return self.re_func_def.findall(line)[0]

    def is_func_call(self, line: str):
        split_line = line.split('\t')
        if len(split_line) > 1 and split_line[-2] == 'bl':
            return self.re_func_call.findall(split_line[-1].split(' ')[-1]) != []
        return False

    def get_func_call_name(self, line: str):
        split_line = line.split('\t')
        if len(split_line) > 1 and split_line[-2] == 'bl':
            return self.re_func_call.findall(split_line[-1].split(' ')[-1])[0]
        return False

    def is_section_start(self, line: str):
        return line.startswith(S_SECTION_START)

    def get_section_name(self, line: str):
        return self.re_sec_name.findall(line)[0]

def get_escaped_html(line: str):
    return _saxutils.escape(line,
                            {
                                ' ': '&nbsp;',
                                '\t': '&emsp;'
                            })


re_func_def = re.compile(RE_FUNC_DEF)

all = []
current_section = []
funcs = []
func_defs = {}
func_calls = {}
section_starts = {}
rev_func_calls = {}
within_func = ""
isa_model = ARM()
line_no = 0


def get_func_def_map(func_def: str):
    if func_def not in func_defs:
        func_defs[func_def] = \
            {
                'line_no':0
            }

    return func_defs[func_def]


def get_func_call_map(func_name: str):
    if func_name not in func_calls:
        func_calls[func_name] = \
            {
                'line_no':[],
                'call_from':[]
            }

    return func_calls[func_name]


for line in sys.stdin.readlines():
    if isa_model.is_func_def(line):
        func_def_name = isa_model.get_func_def_name(line)
        get_func_def_map(func_def_name)['line_no'] = line_no

        within_func = func_def_name # scope
    elif isa_model.is_func_call(line):
        func_name = isa_model.get_func_call_name(line)

        get_func_call_map(func_name)['call_from'].append(within_func)
        get_func_call_map(func_name)['line_no'].append(line_no)

        rev_func_calls[line_no] = func_name
    elif isa_model.is_section_start(line):
        section_starts[isa_model.get_section_name(line)] = line_no
    all.append(line)

    line_no +=1

rev_funcs = {}
func_calls_from_line_nos = {}


def get_rev_func(func_line_no: int) -> list:
    if func_line_no not in rev_funcs:
        rev_funcs[func_line_no] = []

    return rev_funcs[func_line_no]


for call_line_no, func_name in rev_func_calls.items():
    func_line_no = get_func_def_map(func_name)['line_no']
    get_rev_func(func_line_no).append(call_line_no)
    func_calls_from_line_nos[call_line_no] = func_line_no

line_no = 0
print("<!DOCTYPE HTML>")
print("<html><title>objdump output</title>")
print("<body>")
for line in all:
    if line_no not in func_calls_from_line_nos:

        if line_no in rev_funcs:
            print("<code>Refs: ")
            for ref in rev_funcs[line_no]:
                print("<a href=\"#%s\">%s</a>" % (ref, ref))
            print("</code>")
            print("</br>")

        if line_no in rev_funcs:
            print("<span style=\"color:red\"><code id=\"%s\">%s</code></span>" % (line_no, get_escaped_html(line)))
        else:
            print("<code id=\"%s\">%s</code>" % (line_no, get_escaped_html(line)))
    else:

        print("<code id=\"%s\"><a href=\"#%s\">%s</a></code>" % (line_no,func_calls_from_line_nos[line_no], get_escaped_html(line)))
    print("<br/>")
    line_no += 1

print("</body></html>")