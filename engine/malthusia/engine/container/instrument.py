import dis
import math
import logging
import os
import sys
from types import CodeType
from .instruction import Instruction

logger = logging.getLogger(__name__)

class Instrument:
    """
    A class for instrumenting specific methods (e.g. sort) as well as instrumenting competitor code
    """
    def __init__(self, runner):
        self.runner = runner

    def instrumented_sorted(self, iterable, key=None, reverse=False):
        cost = len(iterable) * int(math.log(len(iterable) + 3))
        self.runner.multinstrument_call(cost)
        if not key and not reverse:
            return sorted(iterable)
        elif not reverse:
            return sorted(iterable, key=key)
        elif not key:
            return sorted(iterable, reverse=reverse)
        return sorted(iterable, key=key, reverse=reverse)

    # note: this does basically the same thing as sys.settrace. perhaps switch to sys.settrace?
    @staticmethod
    def instrument(bytecode):
        """
        The primary method of instrumenting code, which involves injecting a bytecode counter between every instruction to be executed

        :param bytecode: a code object, the bytecode submitted by the player
        :return: a new code object that has been injected with our bytecode counter
        """

        # Ensure all code constants (e.g. list comprehensions) are also instrumented.
        new_consts = []
        for i, constant in enumerate(bytecode.co_consts):
            if type(constant) == CodeType:
                new_consts.append(Instrument.instrument(constant))
            else:
                new_consts.append(constant)
        new_consts = tuple(new_consts)

        logger.debug(dis.Bytecode(bytecode).dis())

        instructions = list(dis.get_instructions(bytecode))

        orig_linestarts = list(dis.findlinestarts(bytecode))

        function_name_index = len(bytecode.co_names)  # we will be inserting our __instrument__ call at the end of co_names

        # the injection, which consists of a function call to an __instrument__ method which increments bytecode
        # these three instructions will be inserted between every line of instrumented code
        injection = [
            dis.Instruction(opcode=116, opname='LOAD_GLOBAL', arg=function_name_index, argval='__instrument__', argrepr='__instrument__', offset=None, starts_line=None, is_jump_target=False),
            dis.Instruction(opcode=131, opname='CALL_FUNCTION', arg=0, argval=0, argrepr=0, offset=None, starts_line=None, is_jump_target=False),
            dis.Instruction(opcode=1, opname='POP_TOP', arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=False)
        ]
        injection = [Instruction(inst, original=False) for inst in injection]
        # extends the opargs so that it can store the index of __instrument__
        inserted_extended_args = 0
        function_name_index >>= 8
        while function_name_index > 0: #(255 = 2^8 -1 = 1 oparg)
            if inserted_extended_args >= 3:
                # we can only insert 3! so abort!
                raise SyntaxError("Too many extended_args wanting to be inserted; possibly too many co_names (more than 2^32).")
            injection = [
                Instruction.ExtendedArgs()
            ] + injection
            inserted_extended_args += 1
            function_name_index >>= 8

        # convert every instruction into our own instruction format, which adds a couple of fields.
        for i, instruction in enumerate(instructions):
            instructions[i] = Instruction(instruction, original=True)

        # now compute jump offset for every jumper
        for i, instruction in enumerate(instructions):
            if instruction.is_jumper():
                instruction.calculate_orig_jump_target_offset()
                logger.debug(f"instr {instruction.offset} orig jump target offset: {instruction.orig_jump_target_offset}")

        # We then inject the injection before every call, except for those following an EXTENDED_ARGS.
        new_instructions = []
        for (cur, last) in zip(instructions, [None]+instructions[:-1]):

            if last is not None and last.is_extended_arg():
                new_instructions.append(cur)
                continue

            for inject in injection:
                new_instructions.append(inject)

            new_instructions.append(cur)

        instructions = new_instructions

        # Iterate through instructions. If it's a jumper, calculate the new correct offset. For each new offset, if it
        # is too large to fit in the current number of EXTENDED_ARGS, inject a new EXTENDED_ARG before it. If you never
        # insert a new EXTENDED_ARGS, break out of the loop.
        fixed = False
        while not fixed:
            logger.debug("trying to fix the instruction jumps")
            fixed = True

            # calculate new offsets
            for i, instruction in enumerate(instructions):
                instruction.offset = 2*i

            # calculate map from orig_offset to cur_offset
            orig_to_curr_offset = {}
            for i, instruction in enumerate(instructions):
                if not instruction.original:
                    continue
                cur_offset = instruction.offset
                for prev_instr in instructions[max(i-3,0):i][::-1]:
                    if prev_instr.is_extended_arg():
                        cur_offset -= 2
                        assert(cur_offset == prev_instr.offset)
                    else:
                        break
                # we want to make sure to instrument the jumped-to instruction too, so that we cannot get infinite self loops
                orig_to_curr_offset[instruction.orig_offset] = cur_offset - len(injection)*2

            # now transform each jumper's argument to point to the cur offset instead of the orig offset
            new_instructions = []
            cur_extended_args = []
            for instruction in instructions:
                if instruction.is_extended_arg():
                    cur_extended_args.append(instruction)
                    continue
                if not instruction.is_jumper():
                    new_instructions.extend(cur_extended_args)
                    new_instructions.append(instruction)
                    cur_extended_args = []
                    continue

                real_arg = instruction.calculate_jump_arg(orig_to_curr_offset)
                instruction.arg = real_arg

                real_arg >>= 8
                cur_extended_args_i = len(cur_extended_args) - 1
                while real_arg > 0:
                    if cur_extended_args_i > -1:
                        cur_extended_args_i -= 1
                    else:
                        cur_extended_args = [Instruction.ExtendedArgs()] + cur_extended_args
                        # this causes us to have to redo everything again
                        fixed = False
                    real_arg >>= 8
                assert(cur_extended_args_i == -1) # we may never decrease the offsets, or something went very wrong (we only add instructions, which should monotonically increase offsets)
                assert(len(cur_extended_args) <= 3) # max 3 extended args

                new_instructions.extend(cur_extended_args)
                new_instructions.append(instruction)
                cur_extended_args = []

            assert(len(cur_extended_args)==0)
            instructions = new_instructions

        # calculate new offsets
        for i, instruction in enumerate(instructions):
            instruction.offset = 2*i

        # calculate map from orig_offset to cur_offset
        orig_to_curr_offset = {}
        for i, instruction in enumerate(instructions):
            if not instruction.original:
                continue
            cur_offset = instruction.offset
            for prev_instr in instructions[max(i-3,0):i][::-1]:
                if prev_instr.is_extended_arg():
                    cur_offset -= 2
                    assert(cur_offset == prev_instr.offset)
                else:
                    break
            # we want to make sure to instrument the jumped-to instruction too, so that we cannot get infinite self loops
            orig_to_curr_offset[instruction.orig_offset] = cur_offset - len(injection)*2

        logger.debug(f"near-final instructions: {instructions}")

        # translate line numbers into curr offset
        # this algorithm deduced from https://github.com/python/cpython/blob/3.9/Objects/lnotab_notes.txt#L56
        curr_linestarts = [(orig_to_curr_offset[offset], lineno) for offset, lineno in orig_linestarts]
        new_lnotab = []
        if len(curr_linestarts) > 0:
            logger.debug(f"orig linestarts: {orig_linestarts}")
            logger.debug(f"lnotab: {[int(x) for x in bytecode.co_lnotab]}")
            logger.debug(f"first line: {bytecode.co_firstlineno}")
            if curr_linestarts[0][1] != bytecode.co_firstlineno:
                curr_linestarts = [(0,bytecode.co_firstlineno)] + curr_linestarts
            for cur, last in zip(curr_linestarts[1:],curr_linestarts[:-1]):
                bytesdiff = cur[0] - last[0]
                linediff = cur[1] - last[1]
                while bytesdiff > 255:
                    new_lnotab += [255, 0]
                    bytesdiff -= 255
                if linediff >= 0:
                    while linediff > 127:
                        new_lnotab += [bytesdiff, 127]
                        linediff -= 127
                        bytesdiff = 0
                    if linediff > 0 or bytesdiff > 0:
                        new_lnotab += [bytesdiff, linediff]
                else:
                    while linediff < -128:
                        new_lnotab += [bytesdiff, -128]
                        linediff -= -128
                        bytesdiff = 0
                    if linediff < 0 or bytesdiff > 0:
                        new_lnotab += [bytesdiff, linediff]
        else:
            assert(len(bytecode.co_lnotab) == 0)
        # convert signed linediff to unsigned
        for i, x in enumerate(new_lnotab):
            if x < 0:
                new_lnotab[i] = x + 2**8
        new_lnotab = bytes(new_lnotab)


        # convert args into 256-space
        new_instructions = []
        cur_extended_args = []
        for instruction in instructions:
            if instruction.is_extended_arg():
                cur_extended_args.append(instruction)
                continue
            if instruction.arg is None:
                assert(len(cur_extended_args) == 0)
                new_instructions.append(instruction)
                continue

            real_arg = instruction.arg
            logger.debug(f"real arg: {real_arg}")
            logger.debug(f"cur extended args: {cur_extended_args}")
            instruction.arg = real_arg % 256
            real_arg >>= 8

            cur_extended_args_i = len(cur_extended_args) - 1
            while real_arg > 0:
                assert(cur_extended_args_i > -1)
                # modify the existing extended args
                cur_extended_args[cur_extended_args_i].arg = real_arg % 256
                cur_extended_args_i -= 1
                real_arg >>= 8
            assert(cur_extended_args_i == -1) # we may never decrease the offsets, or something went very wrong (we only add instructions, which should monotonically increase offsets)
            assert(len(cur_extended_args) <= 3) # max 3 extended args

            new_instructions.extend(cur_extended_args)
            new_instructions.append(instruction)
            cur_extended_args = []

        assert(len(cur_extended_args)==0)
        instructions = new_instructions

        # Finally, we repackage up our instructions into a byte string and use it to build a new code object
        assert(all([inst.arg is None or (0 <= inst.arg and inst.arg < 256) for inst in instructions]))
        byte_array = [[inst.opcode, 0 if inst.arg is None else inst.arg] for inst in instructions]
        new_code = bytes(sum(byte_array, []))

        # Make sure our code can locate the __instrument__ call
        new_names = tuple(bytecode.co_names) + ('__instrument__', )

        # return Instrument.build_code(bytecode, new_code, new_names, new_consts, new_lnotab)
        return Instrument.build_code(bytecode, new_code, new_names, new_consts, new_lnotab)

    @staticmethod
    def build_code(old_code, new_code, new_names, new_consts, new_lnotab):
        """Helper method to build a new code object because Python does not allow us to modify existing code objects"""
        if sys.version_info >= (3, 8):
            return CodeType(old_code.co_argcount,
                            old_code.co_posonlyargcount,
                            old_code.co_kwonlyargcount,
                            old_code.co_nlocals,
                            old_code.co_stacksize,
                            old_code.co_flags,
                            new_code,
                            new_consts,
                            new_names,
                            old_code.co_varnames,
                            old_code.co_filename,
                            old_code.co_name,
                            old_code.co_firstlineno,
                            new_lnotab,
                            old_code.co_freevars,
                            old_code.co_cellvars)
        else:
            return CodeType(old_code.co_argcount,
                            old_code.co_kwonlyargcount,
                            old_code.co_nlocals,
                            old_code.co_stacksize,
                            old_code.co_flags,
                            new_code,
                            new_consts,
                            new_names,
                            old_code.co_varnames,
                            old_code.co_filename,
                            old_code.co_name,
                            old_code.co_firstlineno,
                            new_lnotab,
                            old_code.co_freevars,
                            old_code.co_cellvars)
