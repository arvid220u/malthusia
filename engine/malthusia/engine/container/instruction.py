import dis
from types import SimpleNamespace

class Instruction(SimpleNamespace):
    def __init__(self, instruction, original: bool):
        vals = {a: b for a,b in zip(dis.Instruction._fields, instruction)}
        vals["orig_offset"] = vals["offset"]
        vals["original"] = original
        vals["has_orig_offset"] = original
        assert((original and vals["offset"] is not None) or (not original and vals["offset"] is None))
        vals["orig_jump_target_offset"] = None
        super().__init__(**vals)

    def calculate_orig_jump_target_offset(self):
        assert(self.offset is not None)
        assert(self.original)
        assert(self.is_jumper())
        assert(self.offset == self.orig_offset)
        if self.is_rel_jumper():
            self.orig_jump_target_offset = self.orig_offset + self.arg + 2
        elif self.is_abs_jumper():
            self.orig_jump_target_offset = self.arg
        else:
            assert(False)

    def is_jumper(self):
        return self.is_rel_jumper() or self.is_abs_jumper()

    def is_rel_jumper(self):
        return self.opcode in dis.hasjrel

    def is_abs_jumper(self):
        return self.opcode in dis.hasjabs

    def is_extended_arg(self):
        return self.opcode == dis.opmap["EXTENDED_ARG"]

    @classmethod
    def ExtendedArgs(self):
        return Instruction(dis.Instruction(
            opcode=dis.opmap["EXTENDED_ARG"],
            opname='EXTENDED_ARG',
            arg=1,
            argval=1,
            argrepr="",
            offset=None,
            starts_line=None,
            is_jump_target=False
        ), original=False)

    def calculate_jump_arg(self, orig_to_curr_offset):
        assert(self.is_jumper())
        assert(self.orig_jump_target_offset is not None)
        assert(self.orig_jump_target_offset in orig_to_curr_offset)

        target_offset = orig_to_curr_offset[self.orig_jump_target_offset]

        if self.is_abs_jumper():
            return target_offset
        elif self.is_rel_jumper():
            return target_offset - self.offset - 2
        else:
            assert(False)