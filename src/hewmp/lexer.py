PARENTHESIS = "()[]{}"
MODIFIERS = "&,"
SEPARATORS = PARENTHESIS + MODIFIERS

SPLITTERS = SEPARATORS + "="

COMMENT = "$"

SPACERS = "|"

PLAY_CONTROL = ("|:", ":|", "|>", ">|")

TRACK_START = "---"

CONFIGS = [
    "BF:",  # Frequency of base note and @P1
    "BN:",  # Base note, default a4 and J4
    "T:",  # Temperament
    "ET:",  # Equal temperament
    "CL:",  # Comma-list
    "SG:",  # Subgroup
    "C:",  # Constraints
    "CRD:",  # Comma reduction search depth
    "L:",  # Unit-length
    "Q:",  # Tempo
    "G:",  # Groove
    "V:",  # Volume
    "N:",  # Notation
    "I:",  # Instrument (Program Change)
    "MP:",  # Max polyphony
    "F:",  # Flags
]


class Token:
    def __init__(self, value, whitespace, index, line, column):
        self.value = value
        self.whitespace = whitespace
        self.index = index
        self.line = line
        self.column = column

    def is_end(self):
        return self.value is None

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r})".format(self.__class__.__name__, self.value, self.whitespace, self.index, self.line, self.column)


class Lexer:
    def __init__(self, reader):
        self.reader = reader
        self.done = False
        self.peeked_token = None
        self.reading_config_value = False
        self.on_a_new_line = True
        self.reading_string = False
        self.reading_escape = False
        self.index = 0
        self.line = 0
        self.column = 0

    def __iter__(self):
        return self

    def __next__(self):
        was_on_a_new_line = self.on_a_new_line
        self.on_a_new_line = False
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
            self.index += 1
            self.column += 1
            token_obj = Token(token, whitespace, self.index, self.line, self.column)
            if not character:
                if token:
                    return token_obj
                else:
                    self.done = True
                    token_obj.value = None
                    return token_obj
            # Peek emulation
            pos = self.reader.tell()
            next_character = self.reader.read(1)
            next_but_one_character = self.reader.read(1)
            self.reader.seek(pos)

            if self.reading_config_value and not commenting:
                token += character
                if next_character == "\n" or next_character in COMMENT:
                    self.reading_config_value = False
                    token_obj.value = token
                    return token_obj
                continue

            if self.reading_string:
                if character == '"' and not self.reading_escape:
                    self.reading_string = False
                    return token_obj
                if character == "$" and not self.reading_escape:
                    self.reading_escape = True
                else:
                    token += character
                    self.reading_escape = False
                continue

            token_obj.value = token

            if character == "\n":
                commenting = False
                self.on_a_new_line = True
                self.line += 1
                self.column = 0
                token_obj.value = character
                return token_obj
            elif character.isspace():
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

            token_obj.value = token
            token_obj.whitespace = whitespace

            if token:
                if token == TRACK_START and was_on_a_new_line:
                    return token_obj
                if token in PLAY_CONTROL:
                    return token_obj
                if next_character in (":", ">") and next_but_one_character == "|":
                    return token_obj
                if character not in (":", ">") and next_character in SPACERS:
                    return token_obj
                if token in SPACERS and next_character not in (":", ">"):
                    return token_obj

                if token in CONFIGS and was_on_a_new_line:
                    self.reading_config_value = True
                    return token_obj

                if next_character in SPLITTERS or token in SEPARATORS or next_character.isspace():
                    return token_obj

    def peek(self):
        self.peeked_token = next(self)
        return self.peeked_token
