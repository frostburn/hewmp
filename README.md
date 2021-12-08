# hewmp
HEWMP is a machine-readable notation system for writing music in (tempered) just intonation.

The acronym stands for Helmholtz / Ellis / Wolf / Monzo / Pakkanen notation.

## Writing Music Using Ratios

You can use HEWMP with minimal knowledge of music theory by writing melodies using fractional numbers
```
1/1 5/4 6/5 4/3
```
Note frequency is initialized to 440Hz and each ratio multiplies it. Here's the same melody spelled using frequencies.
```
BF:0
@440Hz @550Hz @660Hz @880Hz
```
Or as *absolute* ratios that don't multiply together and are always calculated from the base frequency.
```
@1/1 @5/4 @3/2 @2/1
```
Denominators of one can be dropped.
```
@1 @5/4 @3/2 @2
```

## Descending Intervals
To cause the pitch to fall use fractions smaller than one
```
1 3/4 4/5 5/6
```
or place a minus sign before the interval
```
1 -4/3 -5/4 -6/5
```

## Note Duration
Note duration is specified using square brackets `[`, `]` after a note
```
1/1[2] 6/5 5/4 6/5 10/9[2]
```

## Rests
To advance time without playing a note use the rest symbol `z`. If you want to include the rest in the output use a capital letter `Z`.
```
1 z 5/4 6/5
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
1[4] | 5/4[2] 6/5[2] | 5/4 16/15[3] ||
```

### Repeats
A section can be repeated by placing it between `|:` and `:|`. An optional `x` can be attached onto `:|` to specify the number of repeats other than the default two. This means that `x1` has no effect and `x0` effectively removes the section.
```
$ Repeats are literal so the following is an ascending sequence of seven notes
|: M2 :|x7
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
1/1[2] 5/4[2]|[+4] | 5/6 4/3 1/2[2] ||
```

## Absolute Pitches
Use `@`.

## Floaty Pitches
To play a note relative to the previous one, but ignore it going forward use `~`. This can be used to play local scales, only using non-floaty pitches to move the root note.

## Hz Offset
Beating of similarly tuned notes is a musical phenomenon that is percieved as a rhythm instead of a pitch. Use `Hz` to specify a frequency offset. See also [phase offset](#phase).

## Transposing
To combine two notes use the `&` symbol. This is mainly useful for specifying `Hz` offset along with a pitch.
```
1/1 3/2&1Hz
```

## Inflections
The system is based on small adjustements to Pythagorean intervals defined by their prime-factors and their exponents.

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

Currently these inflections are fixed but an option to define your own will be added.

The vectors associated with the primes 5, 7 and 11 follow Joe Monzo's original proposition.
The monzo for `i` and `!` was particularly chosen so that the barbados third `13/10` can be spelled as `M3i+`. This in turn makes it possible to write the barbados terrad `10:13:15` as `=Mi+` using the chord system (pronounced "major island" see [pronunciation](#pronunciation) for details).
The inflections are supposed to resemble arrows pointing in opposite directions while the u and d pairs bring to mind the words up and down.

## Chords
HEWMP has multiple ways of specifying groups of notes that sound together.
### Otonal Chords
`4:5:6`
### Utonal Chords
`6;5;4`
### Chord Symbol
`=M7-`
### Comma-separated Pitches
`P1,M3-,P5,M7-`
### Chord Inversions
Chords spelled in otonal, utonal or symbolic style can be inverted using `_`. A three note chord has three inversions `_0` root position, `_1` first inversion and `_2` second inversion.
### Chord duration
Duration can be attached to otonal, utonal and symbolic chords. Comma-separated pitches need to be wrapped in parenthesis `(P1,P5)[2]`

## Time Rewind
The comma operator `,` is actually a time rewind operator that turns back time based on the duration of the last note played.

## Tuplets
Parenthesis `(`, `)` are actually used to define tuplets. Anything placed inside parenthesis will have total duration of one.

## Absolute Time
To rewind time a specific beat use the `@` symbol followed by a number inside square brackets `[`, `]`.
### Timestamp
To specify a timestamp use `T`. To jump to the timestamp us `@T` inside square brackets.

## <a name="pronunciation"></a> Pronunciation
### Inflections
| arrow | pronunciation | prime*  | notes |
|:-----:|:-------------:|:------: | ----- |
| +     | plus          | 1/5     | |
| +2    | plus two      | 1/25    | double the effect of a single `+` |
| -     | minus         | 5       | |
| -3    | minus three   | 125     | triple the effect of a single `-` |
| >     | more          | 1/7     | |
| <     | less          | 7       | |
| ^     | up            | 11      | |
| v     | down          | 1/11    | |
| i     | aye           | 13      | `i+` is pronounced "island", motivated by the various island temperaments |
| !     | lei           | 1/13    | `!-` is pronounced "lake", opposite of an island |
| *     | star          | 17      | |
| %     | holes         | 1/17    | think of stars and black holes |
| A     | high          | 19      | `A` looks like a big carret `^` with a line across |
| V     | low           | 1/19    | |
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
To control when the beats of two similarly tuned notes occur use a phase offset defined in degrees.
```
(1,1Hz&90deg)[5]
```
