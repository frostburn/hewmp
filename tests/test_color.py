from hewmp.color import parse_comma

COMMAS = {
    "Sawa": [8, -5],
    "Lalawa": [-19, 12],

    "Gubi": [4, -1, -1],  # "16/15",
    "Yoyo": [-3, -1, 2],  # "25/24",
    "Gugu": [0, 3, -2],  # "27/25",
    "Gu": [-4, 4, -1],  # "81/80",
    "Trigu": [7, 0, -3],
    "Layobi": [-7, 3, 1],
    "Triyo": [1, -5, 3],
    "Quadgu": [3, 4, -4],
    "Sagugu":  [11, -4, -2],
    "Laquinyo": [-10, -1, 5],
    "Quingu": [-1, 8, -5],
    "Tribiyo": [-6, -5, 6],
    "Laquadyo": [-14, 3, 4],
    "Saquadyo": [5, -9, 4],
    "Sayo": [12, -9, 1],
    "Layo": [-15, 8, 1],
    "Sepgu": [2, 9, -7],
    "Saquingu": [18, -4, -5],
    "Saquadbigu": [17, 1, -8],
    "Saquinyo": [9, -13, 5],
    "Lasepyo": [-21, 3, 7],
    "Sasepbigu": [23, 6, -14],
    "Sasa-quintrigu": [38, -2, -15],
    "Zo": [2, -3, 0, 1],  # 28/27
    "Zozo": [-4, -1, 0, 2],  # 49/48
    "Ru": [6, -2, 0, -1],  # 64/63
    "Trizo": [-2, -4, 0, 3],
    "Triru": [-1, 6, 0, -3],
    "Latrizo": [-10, 1, 0, 3],
    "Laruru": [-7, 8, 0, -2],
    "Laquinzo": [-14, 0, 0, 5],
    "Quinru": [3, 7, 0, -5],
    "Laquadru": [-3, 9, 0, -4],
    "Laru": [-13, 10, 0, -1],
    "Lalu": [-6, 6, 0, 0, -1],
    "Trilo": [-4, -4, 0, 0, 3],
    "Thuthu": [9, -1, 0, 0, 0, -2],
    "Latho": [-10, 4, 0, 0, 0, 1],
    "Satritho": [0, -7, 0, 0, 0, 3],
}
# TODO
"""
Saquadru    [16 -3 -4]
Latribiru     [1 10 -6]
Latriru  [-9 11 -3]
Saquinzo     [5 -12 5]
Sepru   [7 8 -7]
Sasa-zozo     [15 -13 2]
iLo     33/32
Lulu      243/242

Satrilu [12 -1 -3]
Salu       [13 -6 -1]
Quadlo  [-9 -3 4]
Salolo    [9 -10 2]
Laquadlo     [-17 2 4]
Saquinlo     [-3 -9 5]
Quinlu    [11 4 -5]
Latrilu  [-7 11 -3]
Salo        [14 -11 1]
Lalolo    [-18 7 2]
Tribilo   [-16 -3 6]
Thu    27/26
Thotho    169/162
Thuthu   [9 -1 -2]
Latho     [-10 4 1]
Satritho     [0 -7 3]
Trithu   [8 2 -3]
Satho      [9 -8 1]
Quadtho   [-10 -3 4]
Laquadthu       [-1 10 -4]
Lathuthu     [-10 11 -2]
Sathu     [18 -9 -1]
Quinthu   [9 6 -5]
Latritho    [-19 5 3]
"""

if __name__ == '__main__':
    for name, target in COMMAS.items():
        monzo = parse_comma(name)
        assert (monzo[:len(target)] == target).all()

    assert parse_comma("trizogu")[2] == -3
    assert parse_comma("trizo-agu")[2] == -1

    assert (parse_comma("Thotrilu-agu")[:6] == [9, 0, -1, 0, -3, 1]).all()
    assert (parse_comma("Bizozogu")[:4] == [-5, -1, -2, 4]).all()
