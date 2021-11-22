PARENTHESIS = "()[]{}"
MODIFIERS = "&,"
SEPARATORS = PARENTHESIS + MODIFIERS

SPLITTERS = SEPARATORS + "="

COMMENT = "$"

SPACERS = "|"

class Token:
    def __init__(self, value, whitespace):
        self.value = value
        self.whitespace = whitespace

    def is_end(self):
        return self.value is None

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.value, self.whitespace)


class Lexer:
    def __init__(self, reader):
        self.reader = reader
        self.current_whitespace = ""
        self.current_token = ""
        self.done = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.done:
            raise StopIteration
        whitespace = ""
        token = ""
        commenting = False
        while True:
            character = self.reader.read(1)
            if not character:
                break
            # Peek emulation
            pos = self.reader.tell()
            next_character = self.reader.read(1)
            next_but_one_character = self.reader.read(1)
            self.reader.seek(pos)

            if character == "|" and next_character == ":":
                token += character
            elif character.isspace() or (character in SPACERS and token != ":"):
                if character == "\n":
                    commenting = False
                whitespace += character
            elif character in COMMENT:
                commenting = True
                whitespace += character
            elif not commenting:
                token += character
            else:
                whitespace += character

            if token:
                if token in ("|:", ":|"):
                    return Token(token, whitespace)
                if next_character == ":" and next_but_one_character == "|":
                    return Token(token, whitespace)
                if character != ":" and next_character in SPACERS:
                    return Token(token, whitespace)
                if next_character in SPLITTERS or token in SEPARATORS or next_character.isspace():
                    return Token(token, whitespace)
        self.done = True
        return Token(None, whitespace)


if __name__ == "__main__":
    from io import StringIO

    reader = StringIO("""
        $ Test string
        P1 M3-=m7+ m3+[0] (P1 M3- P5)[2] m9+2v5&10c&-5Hz 1,5/4,3/2
        |: P1 | P5 | -P4 :|
        |:M3i|-M2:|  $ comment
        P1[1/2]
    """)
    lexer = Lexer(reader)
    for token in lexer:
        print(token)
