from io import StringIO
from lexer import Lexer


def test_lexer():
    reader = StringIO("""
        $ Global config
        T:whatever
        Q:1/5=777
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
    """)
    lexer = Lexer(reader)
    result = [token.value for token in lexer]
    expected_result = [
        'T:', 'whatever', 'Q:', '1/5=777', 'G:', '9/15=2 3 5 7 2', '---', 'P1', 'M3-', '=m7+', 'm3+', '[', '0', ']', '(', 'P1', 'M3-', 'P5', ')',
        '[', '2', ']', 'm9+2v5', '&', '10c', '&', '-5Hz', '&', '11.1deg', '1', ',', '5/4', ',', '3/2', '|:', 'P1', 'P5', '-P4', ':|',
        '|:', 'M3i', '-M2', ':|', '|>', 'P1', 'P4', 'P4', '>|', 'P1', '[', '1/2', ']', '"User $ "message"!', 'P4', '|:', 'P1', 'M3', ':|',
        '---', 'M2', 'M2', 'M2', '---', 'P5', ',', 'P4', None
    ]
    assert result == expected_result


if __name__ == "__main__":
    test_lexer()
