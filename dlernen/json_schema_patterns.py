##########################################################
#
#                   Patterns
#
##########################################################

# must contain at list 1 non-whitespace character
STRING_PATTERN = r"""\S"""

# for names, leading/trailing whitespace is prohibited.
NAME_PATTERN = r"""^\S(.*\S)*$"""

# may not contain any whitespace
WORD_PATTERN = r"""^\S+$"""

ID_PATTERN = WORD_PATTERN

# separate regex for multiline strings.
MULTILINE_STRING_PATTERN = r"""\S"""

ATTRIBUTES = 'attributes'
DEFINITION = 'definition'

