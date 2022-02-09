from io import StringIO
from hewmp.lexer import Lexer


def test_lexer():
    text = """
        $ Global config
        T:whatever
        Q:1/5=777  $ Somewhat speedily
        G:9/15=2 3 5 7 2
        --- $ Start of first track
        $ Test comment
        P1 M3-=m7+ m3+[0] (P1 M3- P5)[2] m9+2v5&10c&-5Hz&11.1deg 1,5/4,3/2
        |: P1 | P5 | -P4 :|
        |:M3i|-M2:|  $ comment
        $ Play from here instead
        |> P1 P4 P4 >|
        $ Stop before you reach here
        P1[1/2] "User $$ $"message$"!" P4
        $|: P1 M2 :|
        |: P1 M3 :|
        --- $ Next track
        M2 M2 M2
        ---
        P5,P4
        =M-[~][!2]
        (P1,M2,M2,M2)[~ !1]
        =M-7[< r R E7 vv 2]
    """
    reader = StringIO(text)
    lexer = Lexer(reader)
    tokens = list(lexer)
    token = tokens[2]
    assert text[:token.index][-len(token.value):] == "T:"
    assert token.value == "T:"
    assert token.index == 35
    assert token.line == 2
    assert token.column == 10
    result = [token.value for token in tokens]
    expected_result = [
        '\n', '\n', 'T:', 'whatever', '\n', 'Q:', '1/5=777  ', '\n', 'G:', '9/15=2 3 5 7 2', '\n', '---', '\n', '\n', 'P1', 'M3-', '=m7+', 'm3+',
        '[', '0', ']', '(', 'P1', 'M3-', 'P5', ')', '[', '2', ']', 'm9+2v5', '&', '10c', '&', '-5Hz', '&', '11.1deg', '1', ',', '5/4', ',', '3/2',
        '\n', '|:', 'P1', '|', 'P5', '|', '-P4', ':|', '\n', '|:', 'M3i', '|', '-M2', ':|', '\n', '\n', '|>', 'P1', 'P4', 'P4', '>|', '\n', '\n', 'P1',
        '[', '1/2', ']', '"User $ "message"!', 'P4', '\n', '\n', '|:', 'P1', 'M3', ':|', '\n', '---', '\n', 'M2', 'M2', 'M2', '\n', '---', '\n', 'P5', ',',
        'P4', '\n', '=M-', '[', '~', ']', '[', '!2', ']', '\n', '(', 'P1', ',', 'M2', ',', 'M2', ',', 'M2', ')', '[', '~', '!1', ']', '\n', '=M-7',
        '[', '<', 'r', 'R', 'E7', 'vv', '2', ']', '\n', None
    ]
    assert result == expected_result
    last_token = None
    for token in tokens:
        if token.value == "G:":
            assert last_token.whitespace == '$ Somewhat speedily'
        last_token = token


if __name__ == "__main__":
    test_lexer()
