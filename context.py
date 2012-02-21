# Copyright (c) 2007 Jakub Wilk <jwilk@jwilk.net>

'''Context analysis of Javalette syntax trees.'''

import syntax
import type
import builtins

__all__ = ['add_pdf', 'validate', 'inspect']

def validate(program):
	'''Look for type mismatches.
	Check for proper variable usage.
	Check if every function returns.'''
	return program.validate()

def add_pdf(program):
	'''Add built-in functions/procedures to the syntax tree.'''
	program.contents += builtins.pdf_function.construct_all()

def inspect(program):
	'''Bind variable references to their declarations.
	Bind statements to functions in which they appear.
	Check if there is 'main' function with a correct type.
	'''
	ok = True
	name_dict = {}
	for function in program.contents:
		if name_dict.has_key(function.name):
			InspectError(function.position, "Redefinition of function '%s' " % function.name).warn()
			ok = False
		else:
			name_dict[function.name] = [function]
	if not name_dict.has_key('main'):
		InspectError(None, "Missing function 'main'").warn()
	for function in program.contents:
		ok &= inspect_function(function, name_dict)
	return ok

def inspect_function(function, name_dict):
	if function.name == 'main' and function.type != type.main_t:
		syntax.TypeMismatch(function.position,
			"Incorrect type of function 'main': <%s> provided but <%s> expected" %
			(function.type, syntax.main_t)).warn()
	return inspect_block(function, function.value, name_dict)

def update_bindings(widget, name_dict):
	ok = True
	for var_ref in widget.get_var_refs():
		var_name = var_ref.ident
		if name_dict.has_key(var_name):
			var_ref.bind = name_dict[var_name][-1]
		else:
			ok = False
			InspectError(var_ref.position, "Variable '%s' undeclared" % var_name).warn()
	return ok

def inspect_block(function, block, name_dict, next_uid = 0):
	ok = True
	varset = set()
	for statement in block.contents:
		statement.bind_to_function(function)
		if isinstance(statement, syntax.declaration):
			for variable in statement.variables:
				ok &= update_bindings(variable, name_dict)
				varname = variable.name
				variable.uid = '#%x' % next_uid
				next_uid += 1
				if varname in varset:
					InspectError(variable.position, "Redeclaration of variable '%s'" % varname).warn()
					ok = False
				else:
					if not name_dict.has_key(varname):
						name_dict[varname] = []
					name_dict[varname] += variable,
					varset.add(varname)
		elif isinstance(statement, syntax.block):
			ok &= inspect_block(function, statement, name_dict, next_uid)
		else:
			ok &= update_bindings(statement, name_dict)
			for subblock in statement.get_blocks():
				ok &= inspect_block(function, subblock, name_dict, next_uid)
	for varname in varset:
		name_dict[varname].pop()
		if len(name_dict[varname]) == 0:
			name_dict.pop(varname)
	return ok

from error import JtError

class InspectError(JtError):
	pass

# vim:ts=4 sw=4