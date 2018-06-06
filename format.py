#!/usr/bin/env python3

from io import StringIO
from itertools import zip_longest

import math
import re
import sys

# TODO:

# 'v' and '#' prefix parameters

# ~p : plural

# ~r : numbers, in many variants

# ~f : fixed float
# ~e : exponential float
# ~g : general float
# ~$ : monetary float

# ~_ : conditional newline
# ~< : logical block
# ~i : indent

# ~/ : call function

# ~t : tabulate
# ~< : justification
# ~> : end justfification
# ~* : goto

# ~[ : conditional expression
# ~] : end conditional expression
# ~{ : iteration
# ~} : end iteration
# ~; : clause separator
# ~^ : escape upward

# ~? : recursive processing


# ~<newline> : ignored newline

# ~u : lost u directive https://gigamonkeys.wordpress.com/2010/10/07/lost-u-directive/

# PROBABLY DON'T IMPLEMENT

# ~| : page feed (ignore)
# ~w : write (maybe not applicable--very Lisp centric)

ends     = {'[':']', '{':'}', '(':')'}
arg_pat  = re.compile("(-?\d+)|('.)|()")
at_colon = re.compile('[:@]{0,2}')

classes = {}

def directive(char):
    def decorator(clazz):
        classes[char.lower()] = clazz
        return clazz
    return decorator

class Formatter:

    "Base class for formatters."

    def __init__(self, params, at, colon):
        self.params = params
        self.at     = at
        self.colon  = colon

    def __repr__(self):
        return '<{} {} at: {}; colon: {}>'.format(self.__class__.__name__, self.params, self.at, self.colon)

    def param(self, idx, default):
        return self.params[idx] if idx < len(self.params) else default

    def get_params(self, *defaults):
        return list(a or b for a, b in zip_longest(self.params, defaults))

    def emit(self, args, pos, newline, file):
        """
        Emit the appropriate text and return the new position in args
        and a boolean indicating whether the last character emitted
        was a newline.
        """
        raise Exception("Abstract method.")


class Text(Formatter):

    "Trivial formatter that emits literal text."

    def __init__(self, text):
        super().__init__([], False, False)
        self.text = text

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.text)

    def emit(self, args, pos, newline, file):
        print(self.text, end='', file=file)
        return pos, self.text[-1] == '\n'


@directive('c')
class Character(Formatter):

    "~c: character formatter. We don't bother with all the options since they are pretty Lisp specific."

    def emit(self, args, pos, newline, file):
        print(args[pos], end='', file=file)
        return pos + 1, args[pos] == '\n'


@directive('%')
class Newline(Formatter):

    "~% : newline formatter"

    def emit(self, args, pos, newline, file):
        times = self.get_params(1)[0]
        for i in range(times):
            print('', file=file)
        return pos, True


@directive('&')
class Freshline(Formatter):

    "~& : freshline"

    def emit(self, args, pos, newline, file):
        times = self.get_params(1)[0]
        if not newline:
            print('', file=file)
        for i in range(times - 1):
            print('', file=file)
        return pos, True


@directive('r')
class Number(Formatter):

    def emit(self, args, pos, newline, file):
        print(args[pos], end='', file=file)
        return pos + 1, False


class IntegerFormatter(Formatter):

    def to_string(self, n, padded, e):
        return self.fmt.format(e + n)[1:] if padded else self.fmt.format(n)

    def commafy(self, n, comma, comma_int):
        n = abs(n)
        e = self.base ** comma_int

        s = self.to_string(n % e, n >= e, e)
        n = n // e
        while n > 0:
            s = self.to_string(n % e, n >= e, e) + comma + s
            n = n // e
        return s

    def emit(self, args, pos, newline, file):
        n = args[pos]
        col, pad, comma, comma_int = self.get_params(0, ' ', ',', 3)
        sign = '-' if n < 0 else ('+' if self.at else '')
        base = sign + (self.commafy(n, comma, comma_int) if self.colon else self.to_string(n, False, 0))
        print_padded(base, col, pad, file)
        return pos + 1, False


@directive('d')
class Decimal(IntegerFormatter):
    base = 10
    fmt = '{:d}'


@directive('b')
class Binary(IntegerFormatter):
    base = 2
    fmt = '{:b}'


@directive('o')
class Octal(IntegerFormatter):
    base = 8
    fmt = '{:o}'


@directive('x')
class Hex(IntegerFormatter):
    base = 16
    fmt = '{:x}'


class ObjectFormatter(Formatter):

    """
    ~mincolA inserts spaces on the right, if necessary, to make the
    width at least mincol columns. The @ modifier causes the spaces
    to be inserted on the left rather than the right.

    ~mincol,colinc,minpad,padcharA is the full form of ~A, which
    allows control of the padding. The string is padded on the right
    (or on the left if the @ modifier is used) with at least minpad
    copies of padchar; padding characters are then inserted colinc
    characters at a time until the total width is at least mincol. The
    defaults are 0 for mincol and minpad, 1 for colinc, and the space
    character for padchar.
    """

    def emit(self, args, pos, newline, file):
        mincol, colinc, minpad, padchar = self.get_params(0, 1, 0, ' ')
        s = self.to_string(args[pos])
        padding = padchar * (minpad + (colinc * math.ceil((mincol - (len(s) + minpad))/colinc)))
        text = padding + s if self.at else s + padding
        print(text, end='', file=file)
        return pos + 1, text[-1] == '\n'

@directive('a')
class Aesthetic(ObjectFormatter):
    def to_string(self, o): return str(o)


@directive('s')
class Standard(ObjectFormatter):
    def to_string(self, o): return repr(o)


@directive('(')
class CaseConversion(Formatter):

    """
    With no flags, every uppercase character is converted to the corresponding lowercase character.

    ~:( capitalizes all words, as if by string-capitalize.

    ~@( capitalizes just the first word and forces the rest to lower case.

    ~:@( converts every lowercase character to the corresponding uppercase character.
    """

    def __init__(self, params, at, colon, formatters):
        super().__init__(params, at, colon)
        self.formatters = formatters

    def emit(self, args, pos, newline, file):
        s, p, nl = emit(self.formatters, args, pos, newline, file=None)

        if not (self.at or self.colon):  s = s.lower()
        elif self.colon and not self.at: s = string_capitalize(s)
        elif self.at and not self.colon: s = s.capitalize()
        elif self.at and self.colon:     s = s.upper()

        print(s, end='', file=file)
        return p, nl

@directive('p')
class Plural(Formatter):
    """
    If arg is not eql to the integer 1, a lowercase s is printed; if arg is eql to 1, nothing is printed. If arg is a floating-point 1.0, the s is printed.
    ~:P does the same thing, after doing a ~:* to back up one argument; that is, it prints a lowercase s if the previous argument was not 1.
    ~@P prints y if the argument is 1, or ies if it is not. ~:@P does the same thing, but backs up first.
    """

    def emit(self, args, pos, newline, file):
        if self.colon: pos -= 1
        if args[pos] == 1:
            ending = '' if not self.at else 'y'
        else:
            ending = 's' if not self.at else 'ies'
        print(ending, end='', file=file)
        return pos + 1, newline and ending == ''


def print_padded(s, columns, pad_char, file):
    for i in range(columns - len(s)):
        print(pad_char, end='', file=file)
    print(s, end='', file=file)


def string_capitalize(s):
    return ''.join(s.capitalize() if re.fullmatch(r'\w+', s) else s for s in re.split(r'([^\w])', s))


def parse_spec(spec, pos, end=None):
    formatters = []
    p_start = pos
    p = pos
    while p < len(spec):
        c = spec[p]
        if c == '~':
            if p > p_start:
                formatters.append(Text(spec[p_start:p]))

            if p + 1 < len(spec) and spec[p + 1] == end:
                return formatters, p + 2
            else:
                formatter, p = parse_directive(spec, p + 1, end)
                p_start = p
                formatters.append(formatter)
        else:
            p += 1

    if p > p_start:
        formatters.append(Text(spec[p_start:p]))

    return formatters


def parse_directive(spec, pos, end):

    args, p      = parse_args(spec, pos)
    at, colon, p = parse_at_colon(spec, p)

    char = spec[p].lower()

    if char == '~':
        return Text('~'), p + 1
    elif char in '[{(':
        formatters, p = parse_spec(spec, p + 1, end=ends[char])
        return classes[char](args, at, colon, formatters), p
    elif char in ']})':
        raise Exception("Unexpected ~{}".char)
    else:
        return classes[char](args, at, colon), p + 1



def parse_args(spec, pos):
    "Read comma-delimited list of args."
    args = []
    p = pos
    while p < len(spec):
        m = arg_pat.match(spec, p)
        if m:
            if m.group(1):
                args.append(int(m.group(1)))
            elif m.group(2):
                args.append(m.group(2)[1])
            else:
                args.append(None)
            p = m.end()

        if spec[p] != ',':
            break
        else:
            p += 1
    return args, p


def parse_at_colon(spec, pos):
    m = at_colon.match(spec, pos)
    s = m.group(0)
    return '@' in s, ':' in s, m.end()


def emit(formatters, args, pos, newline, file=sys.stdout):
    string_output = file is None

    if string_output:
        file = StringIO()

    p, nl = pos, newline
    for f in formatters:
        p, nl = f.emit(args, p, nl, file)

    if string_output:
        text = file.getvalue()
        file.close()
        return text, p, nl
    else:
        return None, p, nl


def format(spec, *args, **kwargs):
    "Emit formatted output."
    s, _, _ = emit(parse_spec(spec, 0), args, 0, True, **kwargs)
    return s


if __name__ == '__main__':

    def check(spec, args, expected):
        out = format(spec, *args, file=None)
        if out != expected:
            print('FAIL: format("{}", {}) returned "{}" expected "{}"'.format(spec, args, out, expected))
        else:
            print('PASS: format("{}", {})'.format(spec, args))

    check('~&Hello', [], 'Hello')
    check('~%Hello', [], '\nHello')
    check('~:d', [1234567], '1,234,567')
    check("~,,'.,4:d", [1234567], '123.4567')
    check("~2,'0d", [3], '03')
    check("~4,'0d-~2,'0d-~2,'0d", [2018, 6, 5], '2018-06-05')
    check("~10d", [123], "       123")
    check("~:d", [1000000], "1,000,000")
    check("~b", [100], "1100100")
    check("~b", [12341234213], "1011011111100110000100101000100101")
    check("~,,' ,4:b", [12341234213], "10 1101 1111 1001 1000 0100 1010 0010 0101")
    check("~o", [1234], "2322")
    check("~x", [0xcafebabe], "cafebabe")
    check("~:@(~x~)", [0xcafebabe], "CAFEBABE")
    check('~a', [10], '10')
    check('~10a', [10], '10        ')
    check('~10@a', [10], '        10')
    check('~s', [10], '10')
    check('~10s', [10], '10        ')
    check('~10@s', [10], '        10')
    check('~(~a~)', ['The quick brown fox'], 'the quick brown fox')
    check('~:(~a~)', ['The quick brown fox'], 'The Quick Brown Fox')
    check('~@(~a~)', ['The quick brown fox'], 'The quick brown fox')
    check('~:@(~a~)', ['The quick brown fox'], 'THE QUICK BROWN FOX')
    check("pig~p", [1], "pig")
    check("pig~p", [10], "pigs")
    check("~d pig~:p", [1], "1 pig")
    check("~d pig~:p", [10], "10 pigs")
