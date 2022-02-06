# Text2Music
Text2Music is a machine-readable notation system for writing music in (tempered) just intonation.

It supports bare ratios, edo steps, Color notation, Ups-and-Downs notation and HEWMP notation.
(The last acronym stands for Helmholtz / Ellis / Wolf / Monzo / Pakkanen).

## Writing Music Using Ratios

You can use Text2Music with minimal knowledge of music theory by writing melodies using fractional numbers.
```
1/1 5/4 3/2 2/1
```
Note frequency is initialized to 440Hz and each ratio multiplies it. Here's the same melody spelled using frequencies.
```
BF:0
@440Hz @550Hz @660Hz @880Hz
```
Or as *moving* ratios that multiply together as we go along.
```
~1/1 ~5/4 ~6/5 ~4/3
```
Plain ratios use the last moved ratio as the base so use *absolute* ratios if you want to use the initial base frequency. (Denominators of one can be dropped `2` simply means `2/1`).
```
@1 @5/4 @3/2 @2
```

## Installation
The project is still in beta so you will have to clone this repository and install manually.
I recommend setting up a [virtualenv](https://docs.python.org/3/library/venv.html) and installing the package as editable.
```
pip install -e .
```
## MIDI Output
```
python -m hewmp.parser examples/giant_steps.hewmp /tmp/giant_steps.mid
```
## Translation for Inspection
The Giant Steps example is mostly written in relative intervals. If you wish to read it in absolute pitches use the `--absolute` command line argument.
```
python -m hewmp.parser examples/giant_steps.hewmp --absolute
```
The Giant Steps example is written in relative 5-limit intervals. If you wish to read it in fractional numbers use the `--fractional` command line argument.
```
python -m hewmp.parser examples/giant_steps.hewmp --fractional
```
## JSON Output
By default the HEWMP parser outputs JSON to the standard output. The format is still under development for easy integration with custom software synths.

## Descending Intervals
To cause the pitch to fall use fractions smaller than one.
```
1 ~3/4 ~4/5 ~5/6
```
or place a minus sign before the interval (this makes more sense if you think in terms of cents).
```
1 ~-4/3 ~-5/4 ~-6/5
```

## Note Duration
Note duration is specified using square brackets `[`, `]` after a note. The default duration is `[1]` (one beat).
```
1/1[2] 6/5 3/2 9/5 2/1[2]
```

## Comments
Anything after a `$` sign is ignored until a newline is reached.
```
$ This is a comment
1 3/2 $ This another comment after two notes that play
```

## Rests
To advance time without playing a note use the rest symbol `.`.
```
1 . 5/4 3/2
```
Rests chain so `..` lasts twice as long as a single rest.

## Pedal
To extend the duration of the last played note (or rest) by one use the pedal symbol `!`. You can think of it as a loud rest that doesn't cut off the sound. To specify how much to extend the duration use `!` followed by a number inside square brackets.
```
1 !   6/5 3/2  $ The root note lasts twice as long as the other two
1[!1] 6/5 3/2  $ The same
```
Pedals chain so `!!` extends duration by two. Pedals also chain with rests so `1 !.!.` is a note of duration two followed by a rest of duration two followed by a rest. Consider it bad practice to extend rests with `!`. The proper spelling is `1 !...`.

## Soft pedal
To only extend the playing duration of the last played note use the soft pedal symbol `~`.
```
1 ~~  5/4 3/2  $ The root note rings throughout the whole arpeggio
1[~2] 5/4 3/2  $ The same
```
Soft pedal chains with plain pedals so `1 !~` is a note of duration three that takes up two units of time.

## Repeats
To repeat the last note or tuplet (useful with chords) use `R`. The pitch(es) will be the same but duration is reset to one.
```
$ Repeats are not literal so these are the same note
~3/2[2] R
```
Repeats chain with `!` so `R!` is the last note but of duration 2.
Repeats skip over rests.
```
77/62  $ Something complicated
.R..R!!.RR.R  $ Cool rhythm without having to spell it out every time
```

## Barlines
Barlines `|` can be used to visually organize your music. They have no effect on the sound.
```
1[4] | 5/4[2] 3/2[2] | 15/8 2/1[3] ||
```

### Repeated Sections
A section can be repeated by placing it between `|:` and `:|`. An optional `x` can be attached onto `:|` to specify the number of repeats other than the default two. This means that `x1` has no effect and `x0` effectively removes the section.
```
$ Section repeats are literal so the following is an ascending sequence of seven notes
|: ~9/8 :|x7
```

### Previewing a Section
You can place a playhead symbol `|>` to skip all music written before it. Use a playstop symbol `>|` to ignore everything after it.
```
$ This is skipped but the effect of going up an octave is preserved
1 ~2
$ This section is played
|> 2/3 3/4 >|
$ This section is ignored
~2 1
```

### Ties
To play a note across a barline use pedal extension.
```
1/1[2] 5/4[2]|[!4] | 3/2 2/1 1/1[2] ||
```

## Absolute Pitches
Using `@` before an interval measures the pitch from the base frequency.
```
$ Go up
~9/8 ~9/8 ~9/8
$ Reset back to 440Hz and go to 660Hz
@1 @3/2
$ Go up from there
~9/8 ~9/8 ~9/8
```

## (Root) Moving Intervals
To play a note relative to the previous one and remember it use `~`. This can be used to play local scales by using moving intervals for root motion.
```
$ ii arpeggio
 ~9/8 6/5 3/2 |
$ V arpeggio
 ~4/3 5/4 3/2 |
$ I arpeggio
 ~2/3 5/4 3/2 |
  2[3]        ||
```

## Composite intervals
You can add an octave to an interval by prefixing it with `c`.
```
1 3/2 c5/4
```
You can subtract an octave from an interval by prefixing it with `` ` ``.
```
1 3/2 `5/4
```

## Pythagorean basis
The base notation system of HEWMP and Ups-and-Downs is Pythagorean i.e. 3-limit just intonation i.e. fractions built from powers of 2 and 3.
The absolute pitches form a chain of fifths.
```
$ A chain of fifths (3/2) around the base note A4
F2 C3 G3 D4 A4 E5 B5
...
$ The same spelled using fractions
@16/81 @8/27 @4/9 @2/3 @1 @3/2 @9/4
```
Adding one to the number after an absolute pitch raises it by an octave.
```
$ Two A notes an octave apart
A4 A5
$ The same
@1 @2
```
From the basic pitches we can derive the basic set of intervals `P1`, `m2`, `M2`, `m3`, `M3`, `P4`, `d5`, `a4`, `P5`, `m6`, `M6`, `m7` and `M7`.
```
$ Perfect unison
C4 C4
C4 P1
$ Major second
C4 D4
C4 M2
$ Major third
C4 E4
C4 M3
$ Perfect fourth
C4 F4
C4 P4
$ Perfect fifth
C4 G4
C4 P5
$ Major sixth
C4 A4
C4 M6
$ Major seventh
C4 B4
C4 M7
$ Perfect octave (same as cP1)
C4 C5
C4 P8
$ Minor seventh
D4 C5
D4 m7
$ Minor sixth
E4 C5
E4 m6
$ Minor third
A4 C5
A4 m3
$ Minor second
B4 C5
B4 m2
$ Augmented fourth
F4 B4
F4 a4
$ Diminished fifth
B3 F4
B3 d5
```
Remember that in just intonation the augmented fourth `729/512` is different from the diminished fifth `1024/729`.

## Sharps and Flats
An absolute pitch can be raised by a fraction of `2187/2048` (approximately `113.685c`) by appending a sharp sign `#` to either side of the octave (spelled as a hash to remain within ASCII). Unicode `♯` is also supported.
```
A4 A4# A♯4
```
To raise the pitch by double the amount use a double sharp sign `x` (spelled as a lowercase 'ex' to remain within ASCII). Unicode `𝄪` is also supported.
```
A4 A4x A𝄪4
```
To lower the pitch by `2187/2048` append a flat sign `b` (spelled as a lowercase 'bee'). Unicode `♭` is also supported. The double-flat `𝄫` works too.
```
A4 A4b A♭4 A𝄫4
```
You can stack any number of `#`, `x` or `b` to modify the pitch further.
```
A4 A4bb
```

## Augmented and Diminished Intervals
If the base interval is perfect `P` or major `M` an augmented version is wider by a fraction of `2187/2048`.
```
P1 a1
```
If the base interval is perfect `P` or minor `m` a diminished version is narrower by a fraction of `2187/2048`. This can create paradoxical intervals that go down in pitch.
```
P1 d1
```
Augmented `a` and diminished `d` stack.
```
P1 dd1 aaa1
```

## Neutral Intervals
An assortment of intervals between minor and major are also supported. `N3` is exactly half the cents of `P5`.
```
N2 N3 N6 N7
```
Warning: Not all edos support dividing the fifth in half and this can result in half-edosteps.

## Half-diminished and Half-augmented Intervals
Stacking neutral intervals eventually produces half-diminished and half-augmented intervals.
```
ha1 hd4 ha4 hd5 ha5 hd8
```

## Quarter-tones
The accidentals `t` and `d` act as quarter-tone sharp and flat respectively. The associated semi-fraction is 27/32&middot;&radic;1½ the square root of a sharp.
```
C4 E4d G4 B4d  $ Neutral 7th arpeggio
```

## Ups and Downs
Equal temperament mode is activated by specifying the number of divisions of the octave with `ET:`. Using the arrows `^` and `v` before intervals or absolute pitches raises or lowers the pitch by one edo step.
```
ET:31
D4 vF4 G4 B4
C4 M3 P5 ^m7 P8
```
See [equal temperaments](#equal_temperament) for more information.

## Half-octave (Tritone)
When not in equal temperament mode the ups-and-downs arrows shift by half of an octave (&radic;2).
```
^1 vP8  $ Two spellings for the half octave
vhd5  $ Alternative meaning for "quartertone" as the half-diminished fifth reduced by a tritone
```

## Inflections
To spell intervals beyond the 3-limit HEWMP uses small adjustements defined by prime factors and their exponents. For example `5/4` is spelled `M3-` (a flat major third), `7/4` is spelled `m7<` (a flat minor seventh) and `11/8` is spelled `P4^` (a sharp perfect fourth). There's a pair of *arrows* corresponding to every prime up to 31 (ordered by size in cents bellow).

| lower | raise | prime | 2,3,5,7,11,13,17,19,23,29,31-monzo | ratio     | cents    |
|:-----:|:-----:|:-----:| ---------------------------------- |:---------:|:--------:|
| V     | A     | 19    | [-9 3 0 0 0 0 0 1 0 0 0>           | 513/512   | 3.37802  |
| %     | *     | 17    | [-12 5 0 0 0 0 1 0 0 0 0>          | 4131/4096 | 14.73041 |
| n     | u     | 23    | [5 -6 0 0 0 0 0 0 1 0 0>           | 736/729   | 16.54434 |
| -     | +     | 5     | [-4 4 -1 0 0 0 0 0 0 0 0>          | 81/80     | 21.50629 |
| !     | i     | 13    | [9 -8 0 0 0 1 0 0 0 0 0>           | 6656/6561 | 24.88765 |
| <     | >     | 7     | [6 -2 0 -1 0 0 0 0 0 0 0>          | 64/63     | 27.26409 |
| D     | U     | 29    | [-8 2 0 0 0 0 0 0 0 1 0>           | 261/256   | 33.48720 |
| v     | ^     | 11    | [-5 1 0 0 1 0 0 0 0 0 0>           | 33/32     | 53.27294 |
| W     | M     | 31    | [5 0 0 0 0 0 0 0 0 0 -1>           | 32/31     | 54.96443 |

Currently these inflections are fixed but an option to configure them will be added.

The vectors associated with the primes 5, 7 and 11 follow Joe Monzo's original proposition.
The monzo for `i` and `!` was particularly chosen so that the barbados third `13/10` is spelled `M3i+`. This in turn makes it possible to write the barbados terrad `10:13:15` as `=Mi+` using the chord system (pronounced "major island" see [Pronunciation](#pronunciation) for details).
The inflections are supposed to resemble arrows pointing in opposite directions while the U and D pair bring to mind the words *up* and *down*.

## Color Notation
Color intervals such as `y3` for `5/4` are supported. Absolute intervals are made using color commas.
```
A4 ryC5  $ Jump from wa A4 to ruyo C5
A4 C5&r1&y1  $ The same, but with explicit commas using transpositions.
```
For more details see [Color Notation](https://en.xen.wiki/w/Color_notation) in the Xenharmonic Wiki.
## Figuring Out Spellings
If you want to see how a certain fraction is spelled use the notation module.
```
$ python -m hewmp.notation 5/3
M6-
$ python -m hewmp.notation 5/3 --absolute
F5#-
$ python -m hewmp.notation 5/3 --color
y6
$ python -m hewmp.notation 11/7 --smitonic
L5>
```
For more details on the last command see the [Smitonic Extension](#smitonic).
## Chords
Text2Music has multiple ways of specifying groups of notes that sound together.
### Otonal Chords
Use `:` to spell out chords as extended ratios. The first number is always at the current pitch.
```
M2=10:12:15  $ ii
P5=4:3:5     $ V
P1=4:5:6:8   $ I
4:5:6        $ The '=' sign is optional if you don't want the pitch to change
```
### Utonal Chords
Where otonal chords are composed of members of the harmonic series, utonal chords by contrast are composed of subharmonics and spelled using `;`.
```
$ A minor chord written using utonal syntax
6;5;4
$ The same but using fractions and otonal syntax
1/6:1/5:1/4
```
### Chord Symbols
HEWMP comes with a chord system that applies inflections and ups-and-downs to chord tones
```
$ Major seventh chord with syntonic inflections on the major third and the major seventh
=M7-
$ Same as
8:10:12:15
```
Some chords like `=aug` only have one version and do not support inflections.
(Chord documentation coming soon.)
#### Added tones
Tones can be added to the chord symbols that support inflections.
```
$ Major seventh chord with an added perfect fourth
=M7-add4
```
#### Suspendend replacements
The third of a chord can be substituted for chords that support inflections.
```
$ Major seventh chord with the major third replaced by a major second
=M7-sus2
```
### Comma-separated Pitches
```
$ Minor seventh chord with syntonic inflections
P1,m3+,P5,m7+
$ Same as
=m7+
$ or
10:12:15:18
```
### Chord Inversions
Chords spelled in otonal, utonal or symbolic style can be inverted using `_`. A three note chord has three inversions `_0` root position, `_1` first inversion and `_2` second inversion. Chords with four notes have four inversions and so on.
```
D4=m7+     $ ii
G4=7-_2    $ V7 in second inversion
C4=M-add8  $ I with an octave on top
```
### Complex Voicings
More complex voicings are created by specifying the order of the chord tones `1` through `7` come in relation to the root `R`.
```
D4=m7+_5R573  $ ii with a fifth bellow the root, another fifth above the root, a seventh above that and a third on the next octave.
G4=dom-_57R3  $ V7 with a pythagorean m7 in second inversion
C4=M-_R351    $ I with an octave on top
```
### Chord duration
Duration can be attached to otonal, utonal and symbolic chords. Comma-separated pitches need to be wrapped in parenthesis.
```
6;5;4[1/2]
=sus4[1/2]
(P1,P5)[2]
```

## Time Rewind
The comma operator `,` is actually a time rewind operator that goes back to the start of the last note played so that multiple notes can be specified to play at the same time. Multiple `,` stack and move back by the same amount of time on each usage.

## Absolute Time
To rewind time to a specific beat use the `@` symbol followed by a number inside square brackets `[`, `]`.

## Tuplets
Parenthesis `(`, `)` are actually used to define tuplets. Anything placed inside parenthesis will have total duration of one.
```
$ Steady pedal tone
1         1    1  1    |  1  1      1 1 ||
$ Funky second voice
~3/2[@0] (. 1) 1 (. 1) | (1 1 1)[2] 1 1 ||
```

## Arpeggiate and Hold
A bare soft pedal `~` inside square brackets extends the durations of notes inside the tuplets so that they end at the same time.
```
(1 5/4 3/2 15/8)[~]     $ All notes of the tetrad hold until the end.
(1 5/4 3/2 15/8)[~ !3]  $ Notes arpeggiate within one beat of time and hold together for 3 additional beats.
```

## Timestamp
To specify a timestamp use `T`. To jump to the timestamp use `@T`. The default behaviour is to jump to the beginning of the song.
```
$ First section soprano voice
   (. C5) B4 (. A4) G4 |
$ First section alto voice
@T C4     D4 E4     E4 |

T  $ Mark the beginning of the second section
$$$$ Second section soprano voice
(. E5) (. C5) (. F4) C5 |
@T $ Jump to the beginning of the second section
$$$$ Second section alto voice
F4     C4     A4     !  |

$ Final section soprano
 T (. G4) (. B4) C5 ! ||
$ Final section alto
@T E4     !      C4 ! ||
```
## Tracks
You can have multiple tracks in your HEWMP score by separating them with `---` (three dashes). The first track is used to define the global config and it should be left without any music when using multiple tracks.
```
$ Global config
ET:19         $ Use 19ed2 as the global tuning
Q:1/4=200     $ Use 200bpm as the global tempo
---
$ Chords
MP:4          $ Reserve four MIDI channels
L:1/1         $ Play full bars
~-P8[0]       $ Play in the alto register
~M2=m7+ | ~P4=dom-_2 | ~-P5=M7- | =M- ||
---
$ Melody
MP:1          $ Reserve one MIDI channel
L:1/4         $ Play quarter notes
~M2 m7+ M6- P5 | ~P4 -M2 M3- -P4 | ~-P5 M7- M3- P4 | P5 M3- P1[2] ||
---
$ Drums
N:percussion  $ Use percussion notation and MIDI channel 10
MP:0          $ Don't reserve pitched channels
L:1/4         $ Play quarter notes
k h s k,h | k h s k,o | k,h h s k,h | k,c h s . ||
```
## Configuration
Configuration is usually placed near the top of the score and consists of various shorthands in capital letters followed by a colon.
### Base Frequency
Use the config `BF:` to define what frequency is used for `@P1` and `A4`. Everything else is calculated in reference to this base pitch. Default is 440Hz.
```
BF:432  $ Now we're vibing
```
### Base Note
Use the config `BN:` to change what absolute pitch has the same frequency as `@P1`. Default is `A4,J5`. (`J5` comes from the [Smitonic Extension](#smitonic))
```
BN:C4  $ Start from C=440Hz
```
### Tempo
Use `Q:` to define how many beats there are in a minute and what constitutes a beat of tempo. Default is `1/4=120`.
```
Q:1/4=220  $ Quarter notes at 220bpm
```
### Unit Length
Use `L:` to define the duration of one beat on the grid. This is compared to the duration of a beat of tempo to calculate the real duration of a beat. Default is `1/4`.
```
L:1/8  $ Duration of [1] corresponds to an eight note
```
### Groove Pattern
Use `G:` to define a non-uniform relative duration for beats on the grid. Default is `1/4=1 1` (straight).
```
G:1/4=2 1  $ Every span of a quarter note is played in triplet swing
```
### Track Volume
Use `V:` to define the volume of a track. Default is `1.0`.
```
V:0.5  $ Half as loud
```
### Notation
Use `N:` to change what notes mean. Used for writing percussion, but reserved for future alternatives that clash with base HEWMP notation. Default is `hewmp`.
```
N:percussion
```
Percussion notation uses shorthands for drums. Here are some basics.

| shorthand | name               | notes  |
|:---------:|:------------------:|:------:|
| k         | Acoustic Bass Drum | "kick" |
| s         | Acoustic Snare     |        |
| h         | Closed Hi-hat      |        |
| o         | Open Hi-hat        |        |
| r         | Ride Cymbal 1      |        |
| c         | Crash Cymbal 1     |        |
| t5        | High Tom           |        |
| t4        | Hi-Mid Tom         |        |
| t3        | Low-Mid Tom        |        |
| t2        | Low Tom            |        |
| t1        | High Floor Tom     |        |
| t0        | Low Floor Tom      |        |

See [percussion](doc/percussion.md) for the full list.
### Instrument
Use `I:` to select an instrument. If the name corresponds to General MIDI the matching program is selected as well.
```
I:Marimba
```
See [instruments](doc/instruments.md) for the full list.
### Maximum Track Polyphony
Text2Music uses per-channel pitch-bends to achieve microtones. Use `MP:` to reserve some of the available 15 channels for the current track.
```
MP:2
```
### Subgroup
To use Text2Music's tuning capabilities you need to tell it which mappings of primes should be affected. You can also use fractions like `2.3.13/5` or multiples of primes like `2.15.7`.
```
SG:2.3.5
```
### Comma List
The main reason HEWMP notation is based on relative intervals is to be able to write comma pumps of arbitrary length in just intonation with a finite number of symbols.
```
$ I-vi-ii-V chord progression that pumps the syntonic comma downwards.
$ (The product of the fractions is 80/81)
|: ~2/3=M- ~5/6=m+ ~4/3=m+ ~4/3=M-_2 :|x12
```
Using a comma-list `CL:` you can *temper out* a set of commas so that the pitch doesn't change when pumping said commas. Text2Music accomplishes this by slightly altering the pitch mapping of the primes in the subgroup given by `SG:`.
```
SG:2.3.5
CL:81/80,128/125
$ I-vi-ii-V chord progression that pumps the syntonic comma,
$ but the overall pitch doesn't change.
|: ~2/3=M- ~5/6=m+ ~4/3=m+   ~4/3=M-_2 :|x4
$ Chord progression that pumps the diesis without changing the overall pitch.
|: ~1/2=M- ~5/4=M- ~5/4=M-_2 ~5/4=7-_3 :|x4
```
### Temperament
Text2Music comes with a few named presets so that you don't have to type out specific subgroups and comma lists.
```
$ Same as SG:2.3.5 and CL:250/243
T:porcupine
$ Chord progression that pumps the porcupine comma
|: ~5/3=6:4:5 ~2/3=3:4:5 ~5/3=6:4:5 ~2/3=6:5:4 ~5/6=3:4:5 :|
```
(Documentation coming soon)
### Constraints
The tuning algorithm tries to do the least amount of damage to just intonation when tempering out commas, but sometimes you may wish to preserve certain intervals while allowing others to take more of the damage.
```
T:meantone
$ Specify quarter-comma meantone by constraining
$ octaves to be pure and major thirds to be just
C:P8,M3-
```
### <a name="equal_temperament"></a> Equal Temperament and Warts
While it is possible to produce an equal temperament without affecting every prime (e.g. `T:compton` is 12edo that only affects `2` and `3`) there's the option to round every prime to the closest number of steps of an equal temperement with `ET:`. You can use [Wart Notation](https://en.xen.wiki/w/Val#Shorthand_notation) to specify non-standard rounding. To specify another interval to divide besides the default `2` use `ED{N}` after the number of divisions and the warts.
```
ET:13b  $ 13edo with a flat fifth to make it compatible with Ups and Downs notation
```
```
ET:13ED3  $ Bohlen-Pierce scale
```
Some equal temperaments have special names. Wendy Carlos' `alpha`, `beta`, `gamma`, `delta` and Bohlen-Pierce (`BP`).
It can be fun to spell melodies and harmonies in just intonation even when using `ET:` as it allows you to untemper the music afterwards
Warning: Large errors in the ET mapping for the prime numbers tend to compound and produce big surprises in how the music sounds compared to its spelling.
### Flags
Various configs that don't take parameters go under flags `F:`.
```
T:porcupine
F:CR  $ Use comma-reduction to simplify output
```
### Comma Reduction Search Depth
Sometimes the algorithm fails to find the simplest representation. You can increase `CRD:` from the default `5` to give the search more resources.
```
CRD:6
```
## Dynamics
To change the velocity of notes played use dynamics `ppp`, `pp`, `p`, `mp`, `mf`, `f`, `ff` or `fff`.
## Articulation
To change the gate length of notes played use articulations `'` (staccato), `;` (normale) or `_` (tenuto).
## User Messages
You can add custom messages to the JSON output by using double quotes `"`.
```
P1 "gently" M2
```
The `$` character acts as as escape inside double quotes. To enter a double quote use `$"`. To enter a dollar sign use `$$`.
## Cents
If you want to specify intervals not affected by tuning use cents.
```
$ 12ed2 A major scale
0c 200c 400c 500c 700c 900c 1100c 1200c
```
Warning: Not even `ET:` will affect something specified in raw cents.
## Primes beyond 31
If a fraction contains primes larger than the supported `31` those will be converted to cents in the output.
```
1 37/31
```
Warning: This can cause some surprises when tempering.
## Hz Offset
Beating of similarly tuned notes is a musical phenomenon that is often perceived as a rhythm instead of a pitch difference. Use `Hz` to specify a frequency offset. See also [Phase Offset](#phase).
```
1,1 . 1,1Hz . 1,2Hz  $ Three unisons with different amounts of beating
```

## Transposing
To combine two intervals use the `&` symbol. This is mainly useful for specifying `Hz` offset alongside a pitch.
```
1/1 3/2&1Hz
```

## EDN Steps
The shorthand to enter cents equal to the current `ET:` step size is `1\`. To specify the number of divisions of `2` add a second number after `\`. To specify another interval to divide besides `2` append it after a second backslash.
```
0\ 2\ 7\ 12\  $ Steps 0, 2, 7 and 12 in the current ET

0\19 5\19 10\19 19\19  $ Steps 0, 5, 10 and 19 in 19ed2

0\10\3 5\10\3  $ Steps 0 and 5 in 10ed3
```

## Interval Roots
To specify fractional pitch monzos append a slash `/` and the desired root degree.
```
$ Arpeggiated neutral chord
P1 P5/2 P5  $ Same as P1 N3 P5
```
Warning: Interval roots may produce fractional steps if the relevant components of the `ET:` mapping are not divisible by the root degree.
### Interval Exponents
To further multiply the fractional pitch monzo append an asterisk `*` and the desired exponent.
```
$ Step through equal divisions of the pure fourth
P1 P4/3 P4/3*2 P4
```

## Rhythm Modeling
Text2Music offers many ways to turn notes and tuplets into more complex rhythmic patterns.

### Arpeggiate Chord
Use `a` to turn a simultaneous chord into a tuplet.
```
=m7+[a]  $ Minor seventh as a quadruplet arpeggio
```
### Reverse (Logical) Order
Use `r` to reverse the order of the notes.
```
=m7+[r a]  $ Minor seventh arpeggiated down
```
### Reverse Time
Use `R` to reverse the temporal information within a pattern
```
=m7+[a R]  $ Minor seventh arpeggiated down
```
### Concatenate Tuplets
You can build complex patterns for further modeling by concatenating them with `+` (adds durations) or `=` (preserves the duration of the first tuplet).
```
=M- + =m+[a]  $ Major followed by minor arpeggiated
=M- = =m+[a]  $ Major followed by minor arpeggiated, but twice as fast
```
### Rhythm Repeats
A pattern can be repeated using `x` followed by a number inside square brackets. By default this doesn't affect the duration of the tuplet. Use a capital `X` to stretch the duration accordingly.
```
=M-[a X4]  $ Major chord arpeggiated four times over four beats
P8[x5]     $ followed by the root note repeated five times over one beat an octave above.
```
### Stretch to Logical Duration
Patterns keep internal time separate from song time. You can equalize those using a `?`.
```
=dom-[a x3 ?]  $ Dominant arpeggio that takes up 12 beats because of internal reasons
```
### Rhythm Rotation
Arrows in different directions shuffle around the logic and rhythm in various ways.
```
(P1 !! P4 ! P5 P8) ... R[^] ... R[<] ... R[v] ... R[>]
```
TODO: Actually explain what these do.
## Advanced Rhythms
Text2Music has a few rhythm families that do different things based on how many notes there are in the manipulated pattern.
### Geometric
Some natural rhythms such as bouncing balls can be hard to notate using integer multiples and tuplets alone. This is where the Concatenated Geometric rhythm family comes in. As the name implies the durations are in a geometric progression and the notes are concatenated together in time. You could also call this the Exponential rhythm family due to the way it sounds, but `CG` is more precise in meaning.
```
P1[x22 CG0.9 ?]  $ Note played in a bouncing ball rhythm of 22 bounces such that
$ the first bounce takes one beat of time and each bounce is 90% of the duration of the last one.
```
### Arithmetic
An arithmetic progression starts with an initial duration and progressively adds a fixed duration to it. The initial duration is to the left of `CA` and the fixed duration is to the right. Concatenated arithmetic rhythms align with a grid while geometric rhythms generally do not.
```
=M-[x2 6CA-1 4]  $ Notes of a major chord with relative durations 6, 5, 4, 3, 2 and 1 such that the whole figure takes up 4 beats.
```
### Harmonic
Geometric rhythms can get pretty fast pretty quickly to the point that they produce a pitched squeal. Harmonic progressions (1/1, 1/2, 1/3, 1/4, etc.) of durations are more subdued while still producing a good accelerando. In `{initial}CH{delta}` the durations are calculated as `1/(initial + n*delta)` for the nth note in the pattern.
```
N:percussion
(k h s h)[x8 3CH2 6]  $ A drum pattern gettin progressively faster over 6 beats.
```
### Euclidean
The Euclidean rhythms are produced in a way analoguous to Euclid's algorithm for finding the greatest common divisor of two numbers and are common in traditional world music. For example two notes in `E5` produce a Persian rhythm called *Khafif-e-ramal* `x.x..` while three notes in `E8` creates the Cuban *tresillo* `x..x..x.`. You can rotate the pattern to the left using numbers on the left side of `E`. Three notes in `1E8` is `x..x.x..` and in `2E8` it is `x.x..x..`.
```
$ Rhythm section composed of claves, hand claps and wood blocks.
N:percussion
   cs[x5 E8 4 X4]
@T hc[x7 E16 4 X4]
@T (w1 w1 w0 w0 w1)[E16 4 X4]
```
See the first few patterns [here](/doc/euclidean_rhythms.md).
### Moment of Symmetry
TODO

## <a name="pronunciation"></a> Pronunciation
### Inflections
| arrow | pronunciation | prime*  | notes |
|:-----:|:-------------:|:------: | ----- |
| +     | plus          | 1/5     |       |
| +2    | plus two      | 1/25    | double the effect of a single `+` |
| -     | minus         | 5       |       |
| -3    | minus three   | 125     | triple the effect of a single `-` |
| >     | more          | 1/7     |       |
| <     | less          | 7       |       |
| ^     | up            | 11      |       |
| v     | down          | 1/11    |       |
| i     | aye           | 13      | `i+` is pronounced "island", motivated by the various island temperaments |
| !     | lei           | 1/13    | `!-` is pronounced "lake", opposite of an island |
| *     | star          | 17      |       |
| %     | holes         | 1/17    | think of stars and black holes |
| A     | high          | 19      | `A` looks like a big carret `^` with a line across |
| V     | low           | 1/19    |       |
| u     | hook          | 23      | think "up" |
| n     | sinker        | 1/23    | looks like an upside down `u`|
| U     | arc           | 29      | think "Up" |
| D     | bow           | 1/29    | think "Down" |
| M     | mighty        | 1/31    | `M` looks like two arrows pointing up |
| W     | weak          | 31      | `W` looks like two arrows pointing down |

Example `cM7-<3A2` "Compound major seventh minus less three high 2" or `987069284145/274877906944`.

### Chords
| symbol  | pronunciation         | notes                                                                                 |
|:-------:|:---------------------:| ------------------------------------------------------------------------------------- |
| =sus2   | sus two               | same as `P1,M2,P5` or `9;8;6` or `8:9:12` |
| =sus4   | sus four              | same as `P1,P4,P5` or `6:8:9` |
| =M      | major                 | same as `P1,M3,P5` or `81;64;54` or `64:81:96`                                                      |
| =M-     | major minus           | same as `P1,M3-,P5` or `4:5:6` |
| =m      | minor                 | same as `P1,m3,P5` or `54:64:81`                                                      |
| =m+     | minor plus            | same as `P1,m3+,P5` or `6;5;4` |
| =M7     | major-seventh         | the major third and the major seventh use the same inflection                         |
| =m7     | minor-seventh         | the minor third and the minor seventh use the same inflection                         |
| =7      | seventh               | spelled as a major chord but uses a minor seventh of the opposite inflection          |
| =dom    | dominant              | uses a Pythagorean minor seventh for a shorter harmonic distance in a V-I progression |
| =mM7    | minor-major-seventh   | spelled as a minor chord but uses a major seventh of the opposite inflection          |
| =M9     | major-ninth           | the major ninth is not inflected |
| =m9     | minor-ninth           | the major ninth is not inflected |
| =9      | ninth                 | the major ninth is not inflected |
| =dom9   | dominant-ninth        | only the third is inflected |
| =mb9    | minor-flat-ninth      | the minor ninth is inflected     |
| =M11    | major-eleventh        | the perfect eleventh is inflected |
| =m11    | minor-eleventh        | the perfect eleventh is inflected |
| =M#11   | major-sharp-eleventh  | the augmented eleventh is inflected |
| =11     | eleventh              | the perfect eleventh is not inflected |
| =domb12 | dominant-flat-twelfth | only the third is inflected |
| =M13    | major-thirteenth      | the major thirteenth is inflected |
| =dom13  | dominant-thirteenth   | only the third is inflected |
| =13     | thirteenth            | the major thirteenth is not inflected |
| =M#15   | major-sharp-fifteenth | the major thirteenth is inflected, the augmented fifteenth is not |

## <a name="phase"></a> Phase Offset
To control when the beats of two similarly tuned notes occur use a phase offset defined in degrees. You will most likely have to write your own synths to take advantage of this.
```
(1,1Hz&90deg)[5]
```
Warning: Phase offset is ignored in MIDI output.
## <a name="smitonic"></a> Smitonic Extension
Note: In the future the Smitonic Extension will be respelled, hidden under a separate `N:` config and renamed to `orgone` as it doesn't actually produce smithirds in all edos.
Because HEWMP is mainly focused on notating just intonation and temperaments thereof it can produce quite surprising results for edos. First an expression is parsed into a fraction and then the prime components of that fraction are used to decide what scale degree should represent that factor. If a prime component is mapped inaccurately the error will compound. This is especially damaging if the prime in question is 3 as it breaks the whole Pythagorean basis of the notation.

Consider 11ed2:
| Degree | Pythagorean interval | Smitonic interval |
|:------:|:--------------------:|:-----------------:|
| 0      | P1                   | p1                |
| 1      | M2                   | s2                |
| 2      | M3                   | L2                |
| 3      | m2                   | p3                |
| 4      | m3                   | s4                |
| 5      | P4                   | L4                |
| 6      | P5                   | s5                |
| 7      | M6                   | L5                |
| 8      | M7                   | p6                |
| 9      | m6                   | s7                |
| 10     | m7                   | L7                |
| 11     | P8                   | p8                |

The Pythagorean notation is poorly aligned and we end up with `m2` being larger in size than `M3`. Contrast this to the *smitonic* intervals that come in clean numerical order.

The smitonic extension to generated by `p3` the *perfect smithird* which is equal to &radic;(16/11) (or equally generated by `cp6` the *perfect compound smisixth* equal to &radic;11). This particular semi-ratio comes from the highly accurate Orgone temperament for the `2.7.11` subgroup where `p3` is equal to `77/64` and three of them equal `7/4`. By definition a stack of two smithirds is equal to `16/11` so the whole subgroup is covered in mere three steps. Contrast this with Meantone temperament which needs four steps of `P5` to cover `2.3.5`.

### Basic Pitches and Intervals
Because it is only an extension and we're running out of letters, the absolute pitches beneath the smitonic intervals are a ragtag collection.
```
$ A chain of smi3rds around the base note J5
K4 Q4 U4 J5 O5 S5 Y5
...
$ The same spelled using semi-fractions
@1331/4096/2   @11/16   @11/16/2   @1   @16/11/2   @16/11   @4096/1331/2
```
And these in turn define the smitonic intervals.
```
J4 p1 J4  $ Perfect unison
J4 L2 K4  $ Large smi2nd
J4 p3 O4  $ Perfect smi3rd
J4 L4 Q4  $ Large smi4th a.k.a. undecimal superfourth 11/8
J4 s5 S4  $ Small smi5th a.k.a. undecimal subfifth 16/11
J4 p6 U4  $ Perfect smi6th
J4 s7 Y4  $ Small smi7th
J4 p8 J5  $ Perfect octave

K4 s2 O4  $ Small smi2nd
K4 s4 S4  $ Small smi4th
K4 n6 U4  $ Narrow smi6th

U4 W3 K5  $ Wide smi3rd
Q4 L5 K5  $ Large smi5th
N4 L7 K5  $ Large smi7th
```
### Sharps, Flats, Wides and Narrows
A sharp sign `#` raises a smitonic pitch by `19487171/16777216/2` (approximately `129.613c`) the same amount a perfect or large smitonic interval differs from its wide counterpart.
```
J5  J5#
@p1 @W1
@1  @19487171/16777216/2
```
A flat sign `b` lowers a smitonic pitch by `19487171/16777216/2` the same amount a perfect or small smitonic interval differs from its narrow counterpart.
```
J5  J5b
@p1 @n1
@1  @16777216/19487171/2
```
### Inflections
| lower | raise | prime | 2,3,5,7,11,13,17,19,23,29,31-monzo | ratio     | cents    |
|:-----:|:-----:|:-----:| ---------------------------------- |:---------:|:--------:|
| <     | >     | 7     | [-8 0 0 -1 -1.5 0 0 1 0 0 0>       | 256/77/&radic;11 | 4.19718 |
| %     | *     | 17    | [-11 0 0 0 2 0 1 0 0 0 0>          | 2057/2048 | 7.59129 |
| n     | u     | 23    | [8 0 0 0 -1 0 0 0 -1 0 0>          | 256/253 | 20.40771 |
| V     | A     | 19    | [6 0 0 0 -0.5 0 0 -1 0 0 0>        | 64/19/&radic;11 | 26.82801 |
| !     | i     | 13    | [2 0 0 0 0.5 -1 0 0 0 0 0>         | &radic;11&middot;4/13 | 35.13131 |
| v     | ^     | 3     | [-5 1 0 0 1 0 0 0 0 0 0>           | 33/32             | 53.27294 |
| W     | M     | 31    | [5 0 0 0 0 0 0 0 0 0 -1>           | 32/31             | 54.96443 |
| D     | U     | 29    | [-10 0 0 0 1.5 0 0 0 0 1 0>        | &radic;11&middot;319/1024 | 56.55411 |
| -     | +     | 5     | [-4 0 1 0 0.5 0 0 0 0 0 0>         | &radic;11&middot;5/16     | 61.97269 |

### Chords
Currently there are two smitonic chords that support inflections `=O` and `=u` and and an extra augmented chord `=smaug`.
```
$ The otonal tetrad
=O<
$ Equal to
8:11:14
$ The utonal tetrad
=u<
$ Equal to
14;11;8
$ The smitonic augmented tetrad
=smaug
$ Equal to
64:88:121
```

### Notation for 18ed2
While not the most accurate edo for the Orgone temperament, 18ed2 does greatly benefit from smitonic notation.

| Degree | Pythagorean interval | Smitonic interval |
|:------:|:--------------------:|:-----------------:|
| 0      | P1                   | p1                |
| 1      | dd5                  | W1,n2             |
| 2      | d4                   | s2                |
| 3      | m3                   | L2                |
| 4      | M2                   | W2,n3             |
| 5      | a1,d6                | p3                |
| 6      | d5                   | W3,n4             |
| 7      | P4                   | s4                |
| 8      | M3                   | L4                |
| 9      | a2,d7                | W4,n5             |
| 10     | m6                   | s5                |
| 11     | P5                   | L5                |
| 12     | a4                   | W5,n6             |
| 13     | a3,d8                | p6                |
| 14     | m7                   | W6,n7             |
| 15     | M6                   | s7                |
| 16     | a5                   | L7                |
| 17     | aa4                  | W7,n8             |
| 18     | P8                   | p8                |

See more [edo notation](doc/edo_notation.md) in the docs.

## Table of ASCII glyphs
See [ASCII semantics](doc/ASCII_semantics.md) in the docs.
