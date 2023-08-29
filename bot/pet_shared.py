# .----------------------------------------------
# | Utilities
# '----------------------------------------------

def separate_first_word(text, lowercase_first=True):
	space = text.find(" ")
	command = text
	arg = ""
	if space >= 0:
		command = text[0:space]
		arg = text[space+1:]
	if lowercase_first:
		command = command.lower()
	return (command, arg)
