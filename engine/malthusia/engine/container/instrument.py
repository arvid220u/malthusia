import dis
import math
import logging
import collections.abc
import os
import sys
from types import CodeType
from .instruction import Instruction

logger = logging.getLogger(__name__)

# from https://stackoverflow.com/a/1409284
def actual_kwargs():
    """
    Decorator that provides the wrapped function with an attribute 'actual_kwargs'
    containing just those keyword arguments actually passed in to the function.
    """
    def decorator(function):
        def inner(*args, **kwargs):
            inner.actual_kwargs = kwargs
            return function(*args, **kwargs)
        return inner
    return decorator

class Instrument:
    """
    Instrument injects and modifies the bytecode of a code object, to:
    (1) Call __instrument__ before each user instruction (which increments the bytecode counter)
    (2) Modify the code in other ways, e.g. by reraising dangerous exceptions
    """
    DANGEROUS_EXCEPTIONS = ["RecursionError", "MemoryError", "KeyboardInterrupt", "OSError", "SystemError", "SystemExit", "OutOfBytecode"]

    @staticmethod
    def reraise_dangerous_exceptions(instructions, names, consts, stacksize):

        added_names = ["_" + x for x in Instrument.DANGEROUS_EXCEPTIONS]

        name_indices = {}
        for i, name in enumerate(names):
            for added_name in added_names:
                if name == added_name:
                    name_indices[name] = i
        for added_name in added_names:
            if added_name not in name_indices:
                name_indices[added_name] = len(names)
                names = names + (added_name, )

        logger.debug(f"reraise dangerous exceptions, names: {names}")

        extra_stacksize = 0

        # find every load_method and insert a nice little injection
        new_instructions = []
        insert_before_orig_offset = {}
        for instruction_index, instruction in enumerate(instructions):
            if not instruction.original:
                continue

            if instruction.orig_offset in insert_before_orig_offset:
                new_instructions.extend(insert_before_orig_offset[instruction.orig_offset])
                del insert_before_orig_offset[instruction.orig_offset]

            if dis.opname[instruction.opcode] == "SETUP_FINALLY":

                previous_except_loc = instruction.orig_jump_target_offset
                assert (previous_except_loc is not None)

                new_except_loc = instruction.orig_jump_target_offset - 0.7

                instruction.orig_jump_target_offset = new_except_loc

                extra_stacksize = max(extra_stacksize, 1 + len(Instrument.DANGEROUS_EXCEPTIONS))

                injection = [
                    dis.Instruction(opcode=dis.opmap["DUP_TOP"], opname="DUP_TOP", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                ]
                for dangerous_exception in Instrument.DANGEROUS_EXCEPTIONS:
                    dangerous_exception = "_" + dangerous_exception
                    injection.append(
                        dis.Instruction(opcode=dis.opmap["LOAD_GLOBAL"], opname="LOAD_GLOBAL", arg=name_indices[dangerous_exception], argval=dangerous_exception, argrepr=dangerous_exception, offset=None, starts_line=None, is_jump_target=None),
                    )
                injection.extend([
                    dis.Instruction(opcode=dis.opmap["BUILD_TUPLE"], opname="BUILD_TUPLE", arg=len(Instrument.DANGEROUS_EXCEPTIONS), argval=len(Instrument.DANGEROUS_EXCEPTIONS), argrepr="", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["COMPARE_OP"], opname="COMPARE_OP", arg=10, argval="exception match", argrepr="exception match", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["POP_JUMP_IF_FALSE"], opname="POP_JUMP_IF_FALSE", arg=previous_except_loc, argval=previous_except_loc, argrepr="", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["POP_TOP"], opname="POP_TOP", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["POP_TOP"], opname="POP_TOP", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["POP_TOP"], opname="POP_TOP", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["RAISE_VARARGS"], opname="RAISE_VARARGS", arg=0, argval=0, argrepr="", offset=None, starts_line=None, is_jump_target=None),
                    # the next operation should never be executed hopefully!!
                    dis.Instruction(opcode=255, opname="NOT_A_LEGAL_OPERATION", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                ])
                injection = [Instruction(inst, original=False) for inst in injection]
                for inject in injection:
                    if inject.is_jumper():
                        inject.orig_jump_target_offset = inject.arg

                injection[0].orig_offset = new_except_loc
                injection[0].has_orig_offset = True

                new_injection = []
                for inject in injection:
                    if not isinstance(inject.arg, int) or inject.arg < 2**8 or inject.is_jumper():
                        new_injection.append(inject)
                        continue
                    else:
                        arg = inject.arg
                        inserted_extended_args = 0
                        arg >>= 8
                        while arg > 0:
                            if inserted_extended_args >= 3:
                                # we can only insert 3! so abort!
                                raise SyntaxError("Too many extended_args wanting to be inserted; possibly too many co_names (more than 2^32).")
                            new_injection.append(Instruction.ExtendedArgs())
                            inserted_extended_args += 1
                            arg >>= 8
                        new_injection.append(inject)

                injection = new_injection

                insert_before_orig_offset[previous_except_loc] = injection

            new_instructions.append(instruction)

        instructions = new_instructions
        stacksize += extra_stacksize

        return instructions, names, consts, stacksize

    @staticmethod
    def replace_builtin_methods(instructions, names, consts, stacksize):
        # this is generally done in a better way by overriding _getattr_. so most often we probably don't want to use this

        extra_stacksize = 0

        added_names = ["__safe_type__", "__module__"]
        added_consts = ["builtins"]

        for instruction in instructions:
            if dis.opname[instruction.opcode] == "LOAD_METHOD":
                added_names.append("__instrumented_" + names[instruction.arg])

        name_indices = {}
        for i, name in enumerate(names):
            for added_name in added_names:
                if name == added_name:
                    name_indices[name] = i
        for added_name in added_names:
            if added_name not in name_indices:
                name_indices[added_name] = len(names)
                names = names + (added_name, )
        const_indices = {}
        for i, const in enumerate(consts):
            for added_const in added_consts:
                if const == added_const:
                    const_indices[const] = i
        for added_const in added_consts:
            if added_const not in const_indices:
                const_indices[added_const] = len(consts)
                consts = consts + (added_const, )


        # ALSO DO THIS FOR MATH ??
        # find every load_method and insert a nice little injection
        new_instructions = []
        for instruction in instructions:
            if not instruction.original:
                continue
            if dis.opname[instruction.opcode] == "LOAD_METHOD":

                method_name = names[instruction.arg]
                instrumented_method_name = "__instrumented_" + method_name

                extra_stacksize = max(extra_stacksize, 3)

                injection = [
                    dis.Instruction(opcode=dis.opmap["DUP_TOP"], opname="DUP_TOP", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["LOAD_GLOBAL"], opname="LOAD_GLOBAL", arg=name_indices["__safe_type__"], argval="__safe_type__", argrepr="__safe_type__", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["ROT_TWO"], opname="ROT_TWO", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["CALL_FUNCTION"], opname="CALL_FUNCTION", arg=1, argval=1, argrepr="", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["LOAD_ATTR"], opname="LOAD_ATTR", arg=name_indices["__module__"], argval="__module__", argrepr="__module__", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["LOAD_CONST"], opname="LOAD_CONST", arg=const_indices["builtins"], argval="builtins", argrepr="builtins", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["COMPARE_OP"], opname="COMPARE_OP", arg=2, argval="==", argrepr="==", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["POP_JUMP_IF_FALSE"], opname="POP_JUMP_IF_FALSE", arg=instruction.orig_offset, argval=instruction.orig_offset, argrepr="", offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["LOAD_GLOBAL"], opname="LOAD_GLOBAL", arg=name_indices[instrumented_method_name], argval=instrumented_method_name, argrepr=instrumented_method_name, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["ROT_TWO"], opname="ROT_TWO", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["JUMP_ABSOLUTE"], opname="JUMP_ABSOLUTE", arg=instruction.orig_offset + 2, argval=instruction.orig_offset + 2, argrepr="", offset=None, starts_line=None, is_jump_target=None),
                ]
                injection = [Instruction(inst, original=False) for inst in injection]
                for inject in injection:
                    if inject.is_jumper():
                        inject.orig_jump_target_offset = inject.arg

                new_injection = []
                for inject in injection:
                    if not isinstance(inject.arg, int) or inject.arg < 2**8 or inject.is_jumper():
                        new_injection.append(inject)
                        continue
                    else:
                        arg = inject.arg
                        inserted_extended_args = 0
                        arg >>= 8
                        while arg > 0:
                            if inserted_extended_args >= 3:
                                # we can only insert 3! so abort!
                                raise SyntaxError("Too many extended_args wanting to be inserted; possibly too many co_names (more than 2^32).")
                            new_injection.append(Instruction.ExtendedArgs())
                            inserted_extended_args += 1
                            arg >>= 8
                        new_injection.append(inject)

                injection = new_injection

                new_instructions.extend(injection)

            new_instructions.append(instruction)

        instructions = new_instructions
        stacksize += extra_stacksize

        return instructions, names, consts, stacksize

    @staticmethod
    def instrument_binary_multiply(instructions, names, consts, stacksize):

        extra_stacksize = 0

        added_names = ["__instrument_binary_multiply__"]

        name_indices = {}
        for i, name in enumerate(names):
            for added_name in added_names:
                if name == added_name:
                    name_indices[name] = i
        for added_name in added_names:
            if added_name not in name_indices:
                name_indices[added_name] = len(names)
                names = names + (added_name, )

        # find every binary_multiply and insert a nice little injection
        new_instructions = []
        for instruction in instructions:
            if not instruction.original:
                continue
            if dis.opname[instruction.opcode] == "BINARY_MULTIPLY":

                extra_stacksize = max(extra_stacksize, 3)

                injection = [
                    dis.Instruction(opcode=dis.opmap["DUP_TOP_TWO"], opname="DUP_TOP_TWO", arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None),
                    dis.Instruction(opcode=dis.opmap["LOAD_GLOBAL"], opname='LOAD_GLOBAL', arg=name_indices["__instrument_binary_multiply__"], argval='__instrument_binary_multiply__', argrepr='__instrument_binary_multiply__', offset=None, starts_line=None, is_jump_target=False),
                    dis.Instruction(opcode=dis.opmap["ROT_THREE"], opname='ROT_THREE', arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=False),
                    dis.Instruction(opcode=dis.opmap["CALL_FUNCTION"], opname='CALL_FUNCTION', arg=2, argval=2, argrepr="", offset=None, starts_line=None, is_jump_target=False),
                    dis.Instruction(opcode=dis.opmap["POP_TOP"], opname='POP_TOP', arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=False)
                ]
                injection = [Instruction(inst, original=False) for inst in injection]

                new_injection = []
                for inject in injection:
                    if not isinstance(inject.arg, int) or inject.arg < 2**8 or inject.is_jumper():
                        new_injection.append(inject)
                        continue
                    else:
                        arg = inject.arg
                        inserted_extended_args = 0
                        arg >>= 8
                        while arg > 0:
                            if inserted_extended_args >= 3:
                                # we can only insert 3! so abort!
                                raise SyntaxError("Too many extended_args wanting to be inserted; possibly too many co_names (more than 2^32).")
                            new_injection.append(Instruction.ExtendedArgs())
                            inserted_extended_args += 1
                            arg >>= 8
                        new_injection.append(inject)

                injection = new_injection

                new_instructions.extend(injection)

            new_instructions.append(instruction)

        instructions = new_instructions
        stacksize += extra_stacksize

        return instructions, names, consts, stacksize

    # note: this does basically the same thing as sys.settrace. perhaps switch to sys.settrace?
    @staticmethod
    @actual_kwargs()
    def instrument(bytecode: CodeType, replace_builtins=False, instrument=True, instrument_binary_multiply=True, reraise_dangerous_exceptions=True) -> CodeType:
        """
        The primary method for instrumenting code, which involves injecting a bytecode counter between every instruction to be executed, among other things.

        :param bytecode: a code object, the bytecode submitted by the player
        :return: a new code object that has been injected with our bytecode counter
        """

        for const in bytecode.co_consts:
            if isinstance(const, collections.abc.Sized):
                if len(const) > 1000:
                    raise SyntaxError(f"Literal with more than 1000 characters. Names, literals and constants can consist of at most 1000 characters. Cause: {const}")

        for name in bytecode.co_names:
            if isinstance(name, collections.abc.Sized):
                if len(name) > 1000:
                    raise SyntaxError(f"Name with more than 1000 characters. Names, literals and constants can consist of at most 1000 characters. Cause: {name}")

        # IMPL NOTE: only original instructions can be jump targets!!!!!

        # Ensure all code constants (e.g. list comprehensions) are also instrumented.
        new_consts = []
        for i, constant in enumerate(bytecode.co_consts):
            if type(constant) == CodeType:
                new_consts.append(Instrument.instrument(constant, **Instrument.instrument.actual_kwargs))
            else:
                new_consts.append(constant)
        new_consts = tuple(new_consts)

        logger.debug("BEGIN uninstrumented code:")
        logger.debug(dis.Bytecode(bytecode).dis())
        logger.debug("END uninstrumented code")

        instructions = list(dis.get_instructions(bytecode))
        # convert every instruction into our own instruction format, which adds a couple of fields.
        for i, instruction in enumerate(instructions):
            instructions[i] = Instruction(instruction, original=True)
        # now compute jump offset for every jumper
        for i, instruction in enumerate(instructions):
            if instruction.is_jumper():
                instruction.calculate_orig_jump_target_offset()
                logger.debug(f"instr {instruction.offset} orig jump target offset: {instruction.orig_jump_target_offset}")

        orig_linestarts = list(dis.findlinestarts(bytecode))


        # original setup done

        new_names = tuple(bytecode.co_names)
        new_stacksize = bytecode.co_stacksize

        # replace builtins
        if replace_builtins:
            instructions, new_names, new_consts, new_stacksize = Instrument.replace_builtin_methods(instructions, new_names, new_consts, new_stacksize)

        if instrument_binary_multiply:
            instructions, new_names, new_consts, new_stacksize = Instrument.instrument_binary_multiply(instructions, new_names, new_consts, new_stacksize)

        if reraise_dangerous_exceptions:
            instructions, new_names, new_consts, new_stacksize = Instrument.reraise_dangerous_exceptions(instructions, new_names, new_consts, new_stacksize)

        # Make sure our code can locate the __instrument__ call
        function_name_index = len(new_names)  # we will be inserting our __instrument__ call at the end of co_names
        new_names = new_names + ('__instrument__', )

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

        if not instrument:
            injection = []
        else:
            new_stacksize += 1

        # We then inject the injection before every call, except for those following an EXTENDED_ARGS.
        new_instructions = []
        for (cur, last) in zip(instructions, [None]+instructions[:-1]):

            # we don't want to count our other injected instructions. that wouldn't be fair
            if not cur.original:
                new_instructions.append(cur)
                continue

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
                if not instruction.has_orig_offset:
                    continue
                cur_offset = instruction.offset
                for prev_instr in instructions[max(i-3,0):i][::-1]:
                    if prev_instr.is_extended_arg():
                        cur_offset -= 2
                        assert(cur_offset == prev_instr.offset)
                    else:
                        break
                # we want to make sure to instrument the jumped-to instruction too, so that we cannot get infinite self loops
                if instruction.original:
                    cur_offset -= len(injection)*2
                orig_to_curr_offset[instruction.orig_offset] = cur_offset

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
            if not instruction.has_orig_offset:
                continue
            cur_offset = instruction.offset
            for prev_instr in instructions[max(i-3,0):i][::-1]:
                if prev_instr.is_extended_arg():
                    cur_offset -= 2
                    assert(cur_offset == prev_instr.offset)
                else:
                    break
            # we want to make sure to instrument the jumped-to instruction too, so that we cannot get infinite self loops
            if instruction.original:
                cur_offset -= len(injection)*2
            orig_to_curr_offset[instruction.orig_offset] = cur_offset

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

        # return Instrument.build_code(bytecode, new_code, new_names, new_consts, new_lnotab)
        final_code = Instrument.build_code(bytecode, new_stacksize, new_code, new_names, new_consts, new_lnotab)

        logger.debug("FINAL CODE:")
        logger.debug(dis.Bytecode(final_code).dis())
        logger.debug("END final code")

        return final_code

    @staticmethod
    def build_code(old_code, new_stacksize, new_code, new_names, new_consts, new_lnotab):
        """Helper method to build a new code object because Python does not allow us to modify existing code objects"""
        if sys.version_info >= (3, 8):
            return CodeType(old_code.co_argcount,
                            old_code.co_posonlyargcount,
                            old_code.co_kwonlyargcount,
                            old_code.co_nlocals,
                            new_stacksize,
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
                            new_stacksize,
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
