PARENTHESIS = "()[]{}"
MODIFIERS = "&,"
SEPARATORS = PARENTHESIS + MODIFIERS

SPLITTERS = SEPARATORS + "="

COMMENT = "$"

SPACERS = "|"

CONFIGS = [
    "a:",  # Frequency of a4 and @P1
    "T:",  # Temperament
    "CL:",  # Comma-list
    "SG:",  # Subgroup
    "C:",  # Constraints
    "CRD:",  # Comma reduction search depth
    "WF:",  # Oscillator waveform
    "L:",  # Unit-length
    "Q:",  # Tempo
    "G:",  # Gain
    "F:",  # Flags
]


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
        self.done = False
        self.peeked_token = None
        self.reading_config_value = False
        self.reading_first_token = True

    def __iter__(self):
        return self

    def __next__(self):
        was_first_token = self.reading_first_token
        self.reading_first_token = False
        if self.peeked_token is not None:
            token_obj = self.peeked_token
            self.peeked_token = None
            return token_obj
        if self.done:
            raise StopIteration
        whitespace = ""
        token = ""
        commenting = False
        while True:
            character = self.reader.read(1)
            if not character:
                if token:
                    return Token(token, whitespace)
                else:
                    self.done = True
                    return Token(None, whitespace)
            # Peek emulation
            pos = self.reader.tell()
            next_character = self.reader.read(1)
            next_but_one_character = self.reader.read(1)
            self.reader.seek(pos)

            if self.reading_config_value:
                token += character
                if next_character == "\n":
                    self.reading_config_value = False
                    return Token(token, whitespace)
                continue

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

                if token in CONFIGS and (was_first_token or whitespace[0] == "\n"):
                    self.reading_config_value = True
                    return Token(token, whitespace)

                if next_character in SPLITTERS or token in SEPARATORS or next_character.isspace():
                    return Token(token, whitespace)

    def peek(self):
        self.peeked_token = next(self)
        return self.peeked_token


if __name__ == "__main__":
    from io import StringIO

    reader = StringIO("""
        $ Test string
        T:whatever
        CL:51/50,77/75
        P1 M3-=m7+ m3+[0] (P1 M3- P5)[2] m9+2v5&10c&-5Hz 1,5/4,3/2
        |: P1 | P5 | -P4 :|
        |:M3i|-M2:|  $ comment
        P1[1/2]
    """)
    lexer = Lexer(reader)
    for token in lexer:
        print(token)
