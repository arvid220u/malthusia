#!/usr/bin/env python3
import sys
import dis

opcount = 0

def tracef(frame, event, arg):
    if event == "call":
        frame.f_trace_opcodes = True
        return tracef
    if event == "opcode":
        global opcount
        opcount += 1
        print(dis.opname[frame.f_code.co_code[frame.f_lasti]])
        print(event)
        print(arg)

def instrument():
    global opcount
    opcount += 1
    print("instrumenting")


s = """
x = 1
y = x+1
l = [1,2]
for li in l:
    x += li
l = sorted(l)
d = ().__class__.__base__.__subclasses__()
print(d)
"""
m = 2
if m==1:
    sys.settrace(tracef)
    exec(s)
    print(f"opcount: {opcount}")
elif m == 2:
    from malthusia.engine.container.instrument import Instrument
    c = compile(s, "source", "exec")
    ci = Instrument.instrument(c)
    exec(ci, {"__builtins__": {"__instrument__": instrument, "sorted": __builtins__.sorted, "print": print}})
    print(f"opcount: {opcount}")
    #dis.dis(ci)
else:
    dis.dis(s)
