import sys
import re
from xml.sax import parse
from xml.sax.handler import ContentHandler

number = '\s*(-?[0-9]*(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?)'
cmd_re = re.compile('\s*([MLHVCSQTAZ]?)' + number + '\s*,?' + number, re.IGNORECASE)

def parse_num(n):
    n = n.strip()
    if n == "":
        return None
    return float(n)

def optional_p(arg):
    if arg == None:
        return ''
    if arg == int(arg):
        return str(int(arg))
    return str(arg)

def fix_path(path):
    commands = []
    first = None
    
    path = path.strip()
    while path != "":
        #print("")
        
        match = cmd_re.match(path)
        if match is None:
            print("Error in path:")
            print(path)
            sys.exit(1)
        cmd = match.group(1)
        x = parse_num(match.group(2))
        y = parse_num(match.group(3))

        #print(match.group(0))
        #print(cmd, x, y)
        commands.append((cmd, x, y))

        if first == None and cmd.lower() == "m":
            first = (x, y)
        
        path = path[match.end():]


    lastcmd = commands[-1]
    if lastcmd[0].lower() == "z" and first != None:
        commands = commands[:-1]
        commands.append(("L", first[0], first[1]))
        commands.append(lastcmd)

    path = " ".join([f"{c[0]} {optional_p(c[1])} {optional_p(c[2])}" for c in commands])
    return path

class SVGHandler(ContentHandler):
    def startElement(self, name, attrs):
        attributes = []
        for attr, val in attrs.items():
            if name.lower() == "path" and attr.lower() == "d":
                val = fix_path(val)
            attributes.append(f'{attr}="{val}"')
        
            
        print(f'<{name} {" ".join(attributes)}>')
        

    def endElement(self, name):
        print(f'</{name}>')

    def characters(self, content):
        if content.strip() != '':
            print(repr(content))

print('<?xml version="1.0" encoding="UTF-8"?>')
parse(sys.argv[1], SVGHandler())

