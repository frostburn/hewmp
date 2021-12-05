PARENTHESIS = "()[]{}"
MODIFIERS = "&,"
SEPARATORS = PARENTHESIS + MODIFIERS

SPLITTERS = SEPARATORS + "="

COMMENT = "$"

SPACERS = "|"

PLAY_CONTROL = ("|:", ":|", "|>", ">|")

TRACK_START = "---"

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
    "G:",  # Groove
    "V:",  # Volume
    "ED:",  # Equal divisions of a harmonic
    "EDN:",  # Harmonic to divide
    "N:",  # Notation
    "I:",  # Instrument (Program Change)
    "MP:",  # Max polyphony
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
        self.reading_string = False
        self.reading_escape = False

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

            if self.reading_string:
                if character == '"' and not self.reading_escape:
                    self.reading_string = False
                    return Token(token, whitespace)
                if character == "$" and not self.reading_escape:
                    self.reading_escape = True
                else:
                    token += character
                    self.reading_escape = False
                continue

            if character == "|" and next_character in (":", ">") and not commenting:
                token += character
            elif character.isspace() or (character in SPACERS and token not in (":", ">")):
                if character == "\n":
                    commenting = False
                whitespace += character
            elif character in COMMENT:
                commenting = True
                whitespace += character
            elif not commenting:
                token += character
                if character == '"':
                    self.reading_string = True
                    self.reading_escape = False
            else:
                whitespace += character

            if token:
                if token == TRACK_START and (was_first_token or "\n" in whitespace):
                    return Token(token, whitespace)
                if token in PLAY_CONTROL:
                    return Token(token, whitespace)
                if next_character in (":", ">") and next_but_one_character == "|":
                    return Token(token, whitespace)
                if character not in (":", ">") and next_character in SPACERS:
                    return Token(token, whitespace)

                if token in CONFIGS and (was_first_token or "\n" in whitespace):
                    self.reading_config_value = True
                    return Token(token, whitespace)

                if next_character in SPLITTERS or token in SEPARATORS or next_character.isspace():
                    return Token(token, whitespace)

    def peek(self):
        self.peeked_token = next(self)
        return self.peeked_token