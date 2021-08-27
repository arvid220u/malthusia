##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""RestrictedPython package."""

# flake8: NOQA: E401

# This is a file to define public API in the base namespace of the package.
# use: isort:skip to supress all isort related warnings / errors,
# as this file should be logically grouped imports

# compile_restricted methods:
from .compile import compile_restricted  # isort:skip
from .compile import compile_restricted_eval  # isort:skip
from .compile import compile_restricted_exec  # isort:skip
from .compile import compile_restricted_function  # isort:skip
from .compile import compile_restricted_single  # isort:skip

# predefined builtins
from .Guards import safe_builtins  # isort:skip
from .Guards import safe_globals  # isort:skip
from .Limits import limited_builtins  # isort:skip
from .Utilities import utility_builtins  # isort:skip

# Helper Methods
from .PrintCollector import PrintCollector  # isort:skip
from .compile import CompileResult  # isort:skip

# Policy
from .transformer import RestrictingNodeTransformer  # isort:skip

#
from .Eval import RestrictionCapableEval
