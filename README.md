# hewmp
HEWMP is a machine-readable notation system for writing music in (tempered) just intonation.

The acronym stands for Helmholtz / Ellis / Wolf / Monzo / Pakkanen notation.

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

## <a name="pronunciation"></a> Pronunciation
### Inflections
| arrow | pronunciation | prime*  | notes |
|:-----:|:-------------:|:------: | ----- |
| -     | minus         | 5       | |
| -3    | minus three   | 125     | triple the effect of a single `-` |
| +     | plus          | 1/5     | |
| +2    | plus two      | 1/25    | double the effect of a single `+` |
| <     | less          | 7       | |
| >     | more          | 1/7     | |
| v     | down          | 1/11    | |
| ^     | up            | 11      | |
| !     | lei           | 1/13    | `!-` is pronounced "lake", opposite of an island |
| i     | aye           | 13      | `i+` is pronounced "island", motivated by the various island temperaments |
| %     | holes         | 1/17    | think of stars and black holes |
| *     | star          | 17      | |
| V     | low           | 1/19    | |
| A     | high          | 19      | `A` looks like a big carret `^` with a line across |
| d     | sinker        | 1/23    | think "down" |
| u     | hook          | 23      | think "up" |
| D     | bow           | 1/29    | think "Down" |
| U     | arc           | 29      | think "Up" |
| W     | little        | 31      | `W` looks like two arrows pointing down |
| M     | much          | 1/31    | `M` looks like two arrows pointing up |

### Chords
| symbol  | pronunciation         | notes                                                                                 |
|:-------:|:---------------------:| ------------------------------------------------------------------------------------- |
| =sus2   | sus two               | same as `P1,M2,P5` or `8:9:12` |
| =sus4   | sus four              | same as `P1,P4,P5` or `6:8:9` |
| =M      | major                 | same as `P1,M3,P5` or `64:81:96`                                                      |
| =M-     | major minus           | same as `P1,M3-,P5` or `4:5:6` |
| =m      | minor                 | same as `P1,m3,P5` or `96;81;64`                                                      |
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
