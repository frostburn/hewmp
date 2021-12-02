# coding: utf-8
WA = "2.3"
WA_TEMPERAMENTS = {
    "blackwood": ["256/243"],  # No fives 5tet
    "compton": ["531441/524288"],  # No fives 12tet
}

YANOWA = "2.5"
YANOWA_TEMPERAMENTS = {
    "augmented": ["128/125"],  # No threes 3tet
}

YA = "2.3.5"
YA_TEMPERAMENTS = {
    # Exotemperaments
    "father": ["15/16"],
    "bug": ["27/25"],
    # Main sequence
    "dicot": ["25/24"],
    "meantone": ["81/80"],
    "mavila": ["135/128"],
    "porcupine": ["250/243"],
    "dimipent": ["648/625"],
    "diaschismic": ["2048/2025"],
    "magic": ["3125/3072"],
    "ripple": ["6561/6250"],
    "hanson": ["15625/15552"],
    "negripent": ["16875/16384"],
    "tetracot": ["20000/19683"],
    "superpyth": ["20480/19683"],
    "helmholtz": ["32805/32768"],
    "sensipent": ["78732/78125"],
    "passion": ["262144/253125"],
    "würschmidt": ["393216/390625"],
    "wurschmidt": ["393216/390625"],
    "wuerschmidt": ["393216/390625"],
    "amity": ["1600000/1594323"],
    "orson": ["2109375/2097152"],
    # Bonus
    "vishnu": ["6115295232/6103515625"],
    "luna": ["274877906944/274658203125"],

    # Special
    "wronecki": ["531441/500000"],  #  period is 1\6

    # Equal temperament meets
    "5tet": ["16/15", "27/25"],  # father | bug
    "7tet": ["25/24", "81/80"],  # dicot | meantone
    "8tet": ["16/15", "648/625"],  # father | dimipent
    "9tet": ["128/125", "135/128"],  # augmented | mavila
    "10tet": ["25/24", "256/243"],  # dicot | blackwood
    "11tet": ["135/128", "262144/253125"],  # mavila | passion
    "12tet": ["81/80", "128/125"],  # meantone | augmented
    "13tet": ["25/24", "262144/253125"],  # dicot | passion
    "14tet": ["27/25", "2048/2025"],  # bug | diaschismic
    "15tet": ["128/125", "256/243"],  # augmented | blackwood
    "16tet": ["135/128", "648/625"],  # mavila | dimipent
    "17tet": ["25/24", "20480/19683"],  # dicot | superpyth
    "19tet": ["81/80", "3125/3072"],  # meantone | magic
    "22tet": ["250/243", "2048/2025"],  # porcupine | diaschismic
    "23tet": ["135/128", "6561/6250"],  # mavila | ripple
    "25tet": ["256/243", "3125/3072"],  # blackwood | magic
    "27tet": ["128/125", "20480/19683"],  # augmented | superpyth
    "28tet": ["648/625", "16875/16384"],  # dimipent | negripent
    "29tet": ["250/243", "16875/16384"],  # porcupine | negripent
    "31tet": ["81/80", "393216/390625"],  # meantone | würschmidt
    "32tet": ["648/625", "20480/19683"],  # dimipent | superpyth
    "34tet": ["2028/2025", "20000/19683"],  # diaschismic | tetracot
    "35tet": ["3125/3072", "6561/6250"],  # magic | ripple
    "37tet": ["250/243", "393216/390625"],  # porcupine | würschmidt
    "41tet": ["3125/3072", "20000/19683"],  # magic | tetracot
    "46tet": ["2028/2025", "78732/78125"],  # diaschismic | sensipent
    "47tet": ["6561/6250", "16875/16384"],  # ripple | negripent
    "48tet": ["16875/16384", "20000/19683"],  # negripent | tetracot
    "49tet": ["20480/19683", "262144/253125"],  # superpyth | passion
    "53tet": ["15625/15552", "32805/32768"],  # hanson | helmholtz
}

ZA = "2.3.7"
ZA_TEMPERAMENTS = {
    "archy": ["64/63"],
    "slendric": ["1029/1024"],
}

YAZA = "2.3.5.7"
YAZA_TEMPERAMENTS = {
    "srutal": ["2048/2025", "4375/4374"],
}

LA = "2.3.11"
LA_TEMPERAMENTS = {
    "alpharabian": ["131769/131072"],
    "betarabian": ["243/242", "131769/131072"],  # 24tet
}

YAZALA = "2.3.5.7.11"
YAZALA_TEMPERAMENTS = {
    "rastmic": ["243/242"],
    "unimarv": ["225/224", "385/384"],
}

ZALANOWA = "2.7.11"
ZALANOWA_TEMPERAMENTS = {
    "orgone": ["65536/65219"],
    "cloudy": ["16807/16384"],
    "orga": ["5767168/5764801"],
    "orgone18": ["2662/2401", "65536/65219"],  # No threes 18tet
    "cloudy20": ["14641/14336", "16807/16384"],  # No threes 20tet
    "orga21": ["1372/1331", "5767168/5764801"],  # No threes 21tet
}

ISLAND_TEMPERAMENTS = {
    "island": [["676/675"], "2.3.5.7.11.13"],
    "parizekmic": [["676/675"], "2.3.5.13"],
    "barbados": [["676/675"], "2.3.13/5"],
    "pinkan": [["676/675", "1216/1215"], "2.3.13/5.19/5"],
}

TEMPERAMENTS = {
    "neutral": [["243/242"], "2.3.11"],
    "latho": [["1053/1024"], "2.3.13"],
    "negra": [["49/48", "65/64", "91/90"], "2.3.5.7.13"],
    "hunt": [["4131/4096"], "2.3.17"],
    "boethius": [["513/512"], "2.3.19"],
    "hdiminished": [["131072/130321"], "2.19"],
    "haugmented": [["33698267/33554432"], "2.323"],
    "12teth": [["131072/130321", "33698267/33554432"], "2.17.19"],  # No threes 12tet
}

_ = [
    (WA_TEMPERAMENTS, WA),
    (YANOWA_TEMPERAMENTS, YANOWA),
    (YA_TEMPERAMENTS, YA),
    (ZA_TEMPERAMENTS, ZA),
    (YAZA_TEMPERAMENTS, YAZA),
    (LA_TEMPERAMENTS, LA),
    (YAZALA_TEMPERAMENTS, YAZALA),
    (ZALANOWA_TEMPERAMENTS, ZALANOWA),
]

for temperaments, subgroup in _:
    for key, value in temperaments.items():
        TEMPERAMENTS[key] = (value, subgroup)

TEMPERAMENTS.update(ISLAND_TEMPERAMENTS)
