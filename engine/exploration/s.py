#!/usr/bin/env python3
import sys
import dis

opcount = 0

def profilef(frame, event, arg):
    if event == "c_call":
        print(frame)
        print(event)
        print(arg)

def tracef(frame, event, arg):
    if event == "call":
        frame.f_trace_opcodes = True
        print(frame)
        return tracef
    if event == "opcode":
        global opcount
        opcount += 1
        #print(dis.opname[frame.f_code.co_code[frame.f_lasti]])
        #print(event)
        #print(arg)

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
s2 = """
#import math
x = "arvid"
y = x.join(["a","b"])

#s = math.factorial(100)

l = sorted([3,2])

def hi():
    return 2

l2 = hi()
"""
m = 0
if m==0:
    sys.setprofile(profilef)
    exec(s2)
elif m==1:
    sys.settrace(tracef)
    exec(s2)
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
