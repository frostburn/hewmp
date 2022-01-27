# HEWMP
HEWMP is a machine-readable notation system for writing music in (tempered) just intonation.

The acronym stands for Helmholtz / Ellis / Wolf / Monzo / Pakkanen notation.

## Writing Music Using Ratios

You can use HEWMP with minimal knowledge of music theory by writing melodies using fractional numbers
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
Plain ratios use the last moved ratio as the base so use *absolute* ratios if you want to use the initial base frequency (denominators of one can be dropped).
```
@1 @5/4 @3/2 @2
```

## Installation
The project is still in alpha so you will have to clone this repository and install manually. The dependencies are not tracked yet, but it's basically just `scipy` and `mido`.

## MIDI Output
```
python -m hewmp.parser examples/giant_steps.hewmp /tmp/giant_steps.mid
```
## Translation for Inspection
The example is mostly written in relative intervals. If you wish to read it in absolute pitches use the `--absolute` command line argument.
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
To cause the pitch to fall use fractions smaller than one
```
1 ~3/4 ~4/5 ~5/6
```
or place a minus sign before the interval (this makes more sense if you think in terms of cents)
```
1 ~-4/3 ~-5/4 ~-6/5
```

## Note Duration
Note duration is specified using square brackets `[`, `]` after a note. The default duration is `[1]` (one beat).
```
1/1[2] 6/5 3/2 9/5 2/1[2]
```

## Rests
To advance time without playing a note use the rest symbol `z`. If you want to include the rest in the output use a capital letter `Z` (only applies if the output format supports explicit rests).
```
1 z 5/4 3/2
```

## Comments
Anything after a `$` sign is ignored until a newline is reached.
```
$ This is a comment
1 3/2 $ This another comment after two notes that play
```

## Barlines
Barlines `|` can be used to visually organize your music. They have no effect on the sound.
```
1[4] | 5/4[2] 3/2[2] | 15/8 2/1[3] ||
```

### Repeats
A section can be repeated by placing it between `|:` and `:|`. An optional `x` can be attached onto `:|` to specify the number of repeats other than the default two. This means that `x1` has no effect and `x0` effectively removes the section.
```
$ Repeats are literal so the following is an ascending sequence of seven notes
|: ~9/8 :|x7
```

### Previewing a Section
You can place a playhead symbol `|>` to skip all music written before it. Use a playstop symbol `>|` to ignore everything after it.
```
$ This is skipped but the effect of going up an octave is preserved
1 2
$ This section is played
|> 2/3 3/4 >|
$ This section is ignored
2 1
```

### Ties
To play a note across a barline use additive duration
```
1/1[2] 5/4[2]|[+4] | 3/2 2/1 1/1[2] ||
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
You can add an octave to an interval by prefixing it with `c`
```
1 3/2 c5/4
```

## Pythagorean basis
The base notation system of HEWMP is Pythagorean i.e. 3-limit just intonation i.e. fractions built from powers of 2 and 3.
While the main system is based on relative intervals there is an underlying set of absolute pitches forming a chain of fifths.
(Please note that the absolute pitch `a` is spelled in lowercase to differentiate it from the augmented interval `A`.) TODO: Switch these
```
$ A chain of fifths (3/2) around the base note a4
F2 C3 G3 D4 a4 E5 B5
z z z
$ The same spelled using fractions
@16/81 @8/27 @4/9 @2/3 @1 @3/2 @9/4
```
Adding one to the number after an absolute pitch raises it by an octave.
```
$ Two A notes an octave apart
a4 a5
$ The same
@1 @2
```
From the basic pitches we can derive the basic set of intervals `P1`, `m2`, `M2`, `m3`, `M3`, `P4`, `d5`, `A4`, `P5`, `m6`, `M6`, `m7` and `M7`.
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
C4 a4
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
a4 C5
a4 m3
$ Minor second
B4 C5
B4 m2
$ Augmented fourth
F4 B4
F4 A4
$ Diminished fifth
B3 F4
B3 d5
```
Remember that in just intonation the augmented fourth `729/512` is different from the diminished fifth `1024/729`.

## Sharps and Flats
An absolute pitch can be raised by a fraction of `2187/2048` (approximately `113.685c`) by appending a sharp sign `#` to it (spelled as a hash to remain within ASCII). Unicode `♯` is also supported.
```
a4 a4#
```
To raise the pitch by double the amount use a double sharp sign `x` (spelled as a lowercase 'ex' to remain within ASCII). Unicode `𝄪` is also supported.
```
a4 a4x
```
To lower the pitch by `2187/2048` append a flat sign `b` (spelled as a lowercase 'bee'). Unicode `♭` and `𝄫` also supported.
```
a4 a4b
```
You can stack any number of `#`, `x` or `b` (in that order) to modify the pitch further.
```
a4 a4bb
```

## Augmented and Diminished Intervals
If the base interval is perfect `P` or major `M` an augmented version is wider by a fraction of `2187/2048`.
```
P1 A1
```
If the base interval is perfect `P` or minor `m` a diminished version is narrower by a fraction of `2187/2048`. This can create paradoxical intervals that go down in pitch.
```
P1 d1
```
Augmented `A` and diminished `d` stack.
```
P1 dd1 AAA1
```

## Neutral Intervals
An assortment of intervals between minor and major are also supported. `N3` is exactly half the cents of `P5`.
```
N2 N3 N6 N7
```
Warning: Not all edos support dividing the fifth in half and this can result in half-edosteps.

## Non-standard Intervals
The perfect intervals have quarter-tone minor and major versions.
```
M1 m4 M4 m5 M5 m8
```

## Quarter-tones
The accidentals `s` and `f` act as quarter-tone sharp and flat respectively.
```
C4 E4f G4 B4f  $ Neutral 7th arpeggio
```

## Inflections
To spell intervals beyond the 3-limit HEWMP uses small adjustements defined by prime factors and their exponents. For example `5/4` is spelled `M3-` (a flat major third), `7/4` is spelled `m7<` (a flat minor seventh) and `11/8` is spelled `P4^` (a sharp perfect fourth). There's a pair of *arrows* corresponding to every prime up to 31 (ordered by size in cents bellow).

| lower | raise | prime | 2,3,5,7,11,13,17,19,23,29,31-monzo | ratio     | cents    |
|:-----:|:-----:|:-----:| ---------------------------------- |:---------:|:--------:|
| V     | A     | 19    | [-9 3 0 0 0 0 0 1 0 0 0>           | 513/512   | 3.37802  |
| %     | *     | 17    | [-12 5 0 0 0 0 1 0 0 0 0>          | 4131/4096 | 14.73041 |
| d     | u     | 23    | [5 -6 0 0 0 0 0 0 1 0 0>           | 736/729   | 16.54434 |
| -     | +     | 5     | [-4 4 -1 0 0 0 0 0 0 0 0>          | 81/80     | 21.50629 |
| !     | i     | 13    | [9 -8 0 0 0 1 0 0 0 0 0>           | 6656/6561 | 24.88765 |
| <     | >     | 7     | [6 -2 0 -1 0 0 0 0 0 0 0>          | 64/63     | 27.26409 |
| D     | U     | 29    | [-8 2 0 0 0 0 0 0 0 1 0>           | 261/256   | 33.48720 |
| v     | ^     | 11    | [-5 1 0 0 1 0 0 0 0 0 0>           | 33/32     | 53.27294 |
| W     | M     | 31    | [5 0 0 0 0 0 0 0 0 0 -1>           | 32/31     | 54.96443 |

Currently these inflections are fixed but an option to configure them will be added.

The vectors associated with the primes 5, 7 and 11 follow Joe Monzo's original proposition.
The monzo for `i` and `!` was particularly chosen so that the barbados third `13/10` is spelled `M3i+`. This in turn makes it possible to write the barbados terrad `10:13:15` as `=Mi+` using the chord system (pronounced "major island" see [Pronunciation](#pronunciation) for details).
The inflections are supposed to resemble arrows pointing in opposite directions while the u and d pairs bring to mind the words *up* and *down*.

## Color Notation
Color intervals such as `y3` for `5/4` are supported.

## Figuring Out Spellings
If you want to see how a certain fraction is spelled use the notation module.
```
$ python -m hewmp.notation 5/3
M6-
$ python -m hewmp.notation 5/3 --absolute
F5#-
$ python -m hewmp.notation 11/7 --smitonic
L5>
```
For more details on the last command see the [Smitonic Extension](#smitonic).
## Chords
HEWMP has multiple ways of specifying groups of notes that sound together.
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
HEWMP comes with a chord system that applies inflections to chord tones
```
$ Major seventh chord with syntonic inflections on the major third and the major seventh
=M7-
$ Same as
8:10:12:15
```
Some chords like `=aug` only have one version and do not support inflections. (TODO: Document all chords)
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
1        1    1  1     |  1  1      1 1 ||
$ Funky second voice
~3/2[@0] (z 1) 1 (z 1) | (1 1 1)[2] 1 1 ||
```
## Timestamp
To specify a timestamp use `T`. To jump to the timestamp use `@T` inside square brackets. TODO: Check if this still works
```
$ First section alto voice
C4         D4 E4     E4 |
$ First section soprano voice
(z C5)[@0] B4 (z a4) G4 |

T  $ Mark the begining of second section
$$$$ Second section alto voice
F4         C4     a4[2]     |
$$$$ Second section soprano voice
(z E5)[@T] (z C5) (z F4) C5 |

$ Final section alto
T E4[2]           C4[2] ||
$ Final section soprano
(z G4)[@T] (z B4) C5[2] ||
```
## Tracks
You can have multiple tracks in your HEWMP score by separating them with `---` (three dashes). The first track is used to define the global config and it should be left without any music when using multiple tracks.
```
$ Global config
ED:19         $ Use 19ed2 as the global tuning
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
k h s k,h | k h s k,o | k,h h s k,h | k,c h s z ||
```
## Configuration
Configuration is usually placed near the top of the score and consists of various shorthands in capital letters followed by a colon.
### Base Frequency
Use the config `BF:` to define what frequency is used for `@P1` and `a4`. Everything else is calculated in reference to this base pitch. Default is 440Hz.
```
BF:432  $ Now we're vibing
```
### Base Note
Us the config `BN:` to change what absolute pitch has the same frequency as `@P1`. Default is `a4,J5`. (`J5` comes from the [Smitonic Extension](#smitonic))
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
| c         | Crash Cymbal 1     |        |
| r         | Ride Cymbal 1      |        |
| t5        | High Tom           |        |
| t4        | Hi-Mid Tom         |        |
| t3        | Low-Mid Tom        |        |
| t2        | Low Tom            |        |
| t1        | High Floor Tom     |        |
| t0        | Low Floor Tom      |        |

TODO: Document all shorthands
### Instrument
Use `I:` to select an instrument. If the name corresponds to General MIDI the matching program is selected as well.
```
I:Marimba
```
TODO: Document all available instruments
### Maximum Track Polyphony
HEWMP uses per-channel pitch-bends to achieve microtones. Use `MP:` to reserve some of the available 15 channels for the current track.
```
MP:2
```
### Subgroup
To use HEWMP's tuning capabilities you need to tell it which mappings of primes should be affected. You can also use fractions like `2.3.13/5` or multiples of primes like `2.15.7`.
```
SG:2.3.5
```
### Comma List
The main reason HEWMP is based on relative intervals is to be able to write comma pumps of arbitrary length in just intonation with a finite number of symbols.
```
$ I-vi-ii-V chord progression that pumps the syntonic comma downwards.
$ (The product of the fractions is 80/81)
|: ~2/3=M- ~5/6=m+ ~4/3=m+ ~4/3=M-_2 :|x12
```
Using a comma-list `CL:` you can *temper out* a set of commas so that the pitch doesn't change when pumping the commas. HEWMP accomplishes this by slightly altering the pitch mapping of the primes in the subgroup given by `SG:`.
```
SG:2.3.5
CL:81/80,128/125
$ I-vi-ii-V chord progression that pumps the syntonic comma,
$ but the overall pitch doesn't change.
|: ~2/3=M- ~5/6=m+ ~4/3=m+   ~4/3=M-_2 :|x4
$ Chord progression that pumps the diesis without changing the overall pitch.
|: ~1/2=M- ~5/4=M- ~5/4=M-_2 ~5/4=7-_3 :|x4
```
### Temperament/Tuning
HEWMP comes with a few named presets so that you don't have to type out specific subgroups and comma lists.
```
$ Same as SG:2.3.5 and CL:250/243
T:porcupine
$ Chord progression that pumps the porcupine comma
|: ~5/3=6:4:5 ~2/3=3:4:5 ~5/3=6:4:5 ~2/3=6:5:4 ~5/6=3:4:5 :|
```
TODO: Document all available temperaments
### Constraints
The tuning algorithm tries to do the least amount of damage to just intonation when tempering out commas, but sometimes you may wish to preserve certain intervals while allowing others to take more of the damage.
```
T:meantone
$ Specify quarter-comma meantone by constraining
$ octaves to be pure and major thirds to be just
C:P8,M3-
```
### Equal Divisions of an Interval
While it is possible to produce an equal temperament without affecting every prime (e.g. `T:compton` is 12edo that only affects `2` and `3`) there's the option to round every prime to the closest number of steps of an equal temperement with `ED:`. You can use [Wart Notation](https://en.xen.wiki/w/Val#Shorthand_notation) to specify non-standard rounding. The default number of divisions is 12.
```
ED:20c
```
### Interval to Equally Divide
Use `EDN:` to change which interval is divided equally. The default interval to divide is `2`.
```
EDN:3
```
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
To change the gate length of notes played use articulations `.` (staccato), `;` (normale) or `_` (tenuto).
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
Warning: Not even `ED:` will affect something specified in raw cents.
## Primes beyond 31
If a fraction contains primes larger than the supported `31` those will be converted to cents in the output.
```
1 37/31
```
Warning: This can cause some surprises when tempering.
## Hz Offset
Beating of similarly tuned notes is a musical phenomenon that is often perceived as a rhythm instead of a pitch difference. Use `Hz` to specify a frequency offset. See also [Phase Offset](#phase).
```
1,1 z 1,1Hz z 1,2Hz
```

## Transposing
To combine two intervals use the `&` symbol. This is mainly useful for specifying `Hz` offset alongside a pitch.
```
1/1 3/2&1Hz
```

## EDN Steps
The shorthand to enter cents equal to the current `ED:` step size is `1\`. To specify the number of divisions of `2` add a second number after `\`. To specify another interval to divide besides `2` append it after a second backslash.
```
0\ 2\ 7\ 12\

0\19 5\19 10\19 19\19

0\10\3 5\10\3
```

## Interval Roots
To specify fractional pitch monzos append a slash `/` and the desired root degree.
```
$ Arpeggiated neutral chord
P1 P5/2 P5
```
Warning: Interval roots may produce fractional steps if the relevant components of the `ED:` mapping are not divisible by the root degree.
### Interval Exponents
To further multiply the fractional pitch monzo append an asterisk `*` and the desired exponent.
```
$ Step through equal divisions of the pure fourth
P1 P4/3 P4/3*2 P4
```

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
| d     | sinker        | 1/23    | think "down" |
| U     | arc           | 29      | think "Up" |
| D     | bow           | 1/29    | think "Down" |
| M     | mighty        | 1/31    | `M` looks like two arrows pointing up |
| W     | weak          | 31      | `W` looks like two arrows pointing down |

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
TODO: Fix pitch names

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
K4 O4 R4 J5 N5 Q5 S5
z z z
$ The same spelled using semi-fractions
@1331/4096/2   @11/16   @11/16/2   @1   @16/11/2   @16/11   @4096/1331/2
```
And these in turn define the smitonic intervals.
```
J4 p1 J4  $ Perfect unison
J4 L2 K4  $ Large smi2nd
J4 p3 N4  $ Perfect smi3rd
J4 L4 O4  $ Large smi4th a.k.a. undecimal superfourth 11/8
J4 s5 Q4  $ Small smi5th a.k.a. undecimal subfifth 16/11
J4 p6 R4  $ Perfect smi6th
J4 s7 S4  $ Small smi7th
J4 p8 J5  $ Perfect octave

K4 s2 N4  $ Small smi2nd
K4 s4 Q4  $ Small smi4th
K4 n6 S4  $ Narrow smi6th

S4 W3 K5  $ Wide smi3rd
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
| d     | u     | 23    | [8 0 0 0 -1 0 0 0 -1 0 0>          | 256/253 | 20.40771 |
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
| 5      | A1,d6                | p3                |
| 6      | d5                   | W3,n4             |
| 7      | P4                   | s4                |
| 8      | M3                   | L4                |
| 9      | A2,d7                | W4,n5             |
| 10     | m6                   | s5                |
| 11     | P5                   | L5                |
| 12     | A4                   | W5,n6             |
| 13     | A3,d8                | p6                |
| 14     | m7                   | W6,n7             |
| 15     | M6                   | s7                |
| 16     | A5                   | L7                |
| 17     | AA4                  | W7,n8             |
| 18     | P8                   | p8                |

See more [edo notation](doc/edo_notation.md) in the docs.
