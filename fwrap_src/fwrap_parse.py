from fwrap_src import pyf_iface as pyf
from fparser import api

from nose.tools import set_trace

def generate_ast(fsrcs):
    ast = []
    for src in fsrcs:
        block = api.parse(src, analyze=True)
        tree = block.content
        for proc in tree:
            if proc.blocktype == 'subroutine':
                fargs = _get_args(proc)
                ast.append(pyf.Subroutine(name=proc.name, args=fargs))
            elif proc.blocktype == 'function':
                ast.append(pyf.Function(name=proc.name, args=(), return_type=pyf.default_integer))
            else:
                raise FwrapParseError("unknown fortran construct %r." % proc)
    return ast


def _get_args(proc):
    args = []
    for argname in proc.args:
        p_arg = proc.get_variable(argname)
        p_typedecl = p_arg.get_typedecl()
        dtype = _get_dtype(p_typedecl)
        name = p_arg.name
        intent = _get_intent(p_arg)
        if p_arg.is_scalar():
            args.append(pyf.Argument(name=name, dtype=dtype, intent=intent))
        elif p_arg.is_array():
            p_dims = p_arg.get_array_spec()
            dims = []
            for dim in p_dims:
                if dim == ('',''):
                    dims.append(':')
                elif len(dim) == 1:
                    dims.append(dim[0])
                else:
                    raise RuntimeError("can't handle dimension(x:y) declarations yet...")
            args.append(pyf.Argument(name=name, dtype=dtype, intent=intent, dimension=dims))
        else:
            raise RuntimeError("argument %s is neither a scalar or an array (derived type?)" % p_arg)
    return args

def _get_intent(arg):
    intents = []
    if arg.is_intent_in():
        intents.append("in")
    if arg.is_intent_inout():
        intents.append("inout")
    if arg.is_intent_out():
        intents.append("out")
    if not intents:
        raise RuntimeError("argument has no intent specified, '%s'" % arg)
    if len(intents) > 1:
        raise RuntimeError("argument has multiple intents specified, '%s', %s" % (arg, intents))
    return intents[0]

name2type = {
        'integer' : pyf.default_integer,
        'doubleprecision' : pyf.default_dbl,
        'complex' : pyf.default_complex,
        'character' : pyf.default_character,
        }

def _get_dtype(typedecl):
    # import pdb; pdb.set_trace()
    if not typedecl.is_intrinsic():
        raise RuntimeError("only intrinsic types supported ATM...")
    return name2type[typedecl.name]
