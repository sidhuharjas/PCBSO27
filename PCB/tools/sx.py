"""Minimal KiCad s-expression reader/writer (no KiCad needed)."""
import re
TOK = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+)')
class Sym(str): pass
def parse(text):
    pos = 0; stack = [[]]
    for m in TOK.finditer(text):
        t = m.group(1)
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1].replace('\\"', '"').replace('\\\\', '\\'))  # python str = quoted string
        else:
            stack[-1].append(Sym(t))
    return stack[0][0]
def dump(x, ind=0):
    if isinstance(x, list):
        if not x: return '()'
        # one-line if all atoms and short
        if all(not isinstance(i, list) for i in x) or (len(x) < 8 and sum(len(dump(i)) for i in x) < 90 and all(not (isinstance(i, list) and any(isinstance(j, list) for j in i)) for i in x)):
            return '(' + ' '.join(dump(i) for i in x) + ')'
        pad = '\t' * (ind + 1)
        out = '(' + dump(x[0])
        for i in x[1:]:
            if isinstance(i, list):
                out += '\n' + pad + dump(i, ind + 1)
            else:
                out += ' ' + dump(i)
        return out + '\n' + '\t' * ind + ')'
    if isinstance(x, Sym): return str(x)
    if isinstance(x, str): return '"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(x, float): 
        s = ('%.6f' % x).rstrip('0').rstrip('.'); return s if s not in ('', '-0') else '0'
    return str(x)
def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]
def first(node, name):
    r = find(node, name); return r[0] if r else None
