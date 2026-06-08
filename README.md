# Hatchery
Theory engine plugin for Plover!

Hatchery generates all possible writeouts from a word list, according to customizable theory rules.

## Installation
This plugin is not included in the plugins registry. [Instructions are available on the Plover wiki](https://plover.wiki/index.php/Plugins#Find_the_plugin_on_PyPI_or_as_a_git_repo) on how to install this plugin from this Git repository.

## Motivation
> [!IMPORTANT]
> To be documented!

## Functionality
> [!IMPORTANT]
> To be documented!

### Definitions
A **sopheme** is a unit of a word that represents an atomic grapheme-phoneme correspondence. That is, it stores a sequence of letters that a reader would think of as making certain sounds. Ideally, the set of sophemes that make up a word is solely based on its reading and pronunciation and is independent of a theory.
* The letter `m` can make the `/m/` sound. The sopheme would be the pairing of that spelling and pronunciation together, which I denote with a dot: `m.m`.
* The letter `c` can make the `/k/` (`c.k`) or `/s/` (`c.s`) sounds.
* Multiple letters can make a single sound: `ph` makes the `/f/` sound (`ph.f`).
* A single letter can make multiple sounds: `x` makes the `/ks/` sounds (`x.ks`). 
* Multiple letters can make multiple sounds: `wh` makes the `/hw/` sounds in some accents (`wh.hw`).
* Letters can be silent: in `rate`, `e` makes no sound (`e.`).
* Pronounciations can arbitrarily diverge from their spellings but still be associated with clusters of letters: in `comfortable`, `orta` makes the `/tər/` sounds (`orta.tər`).
* *I called it that because "lexeme" and "morpheme" were already taken :)*

A **theory symbol** is a unit of a word that is treated uniquely by a steno theory. These are defined by the theory.
* In a lot of cases, these map one-to-one with specific phonemes, so e.g. any `/p/` sound is treated the same by a theory and thus can be represented with a single theory symbol, which might be called `P`. (The theory symbol names don't really matter; we just want a way to refer to them consistently.)
* Suppose you want your theory to treat the `/s/` sound differently depending on how it is spelled, like with a `c`. Then the sopheme `c.s` could be given one theory symbol probably named `C`, whereas any other occurrence of `/s/` would be given a theory symbol named `S`.

## Entrypoints
This plugin exposes the following tools and interfaces:

### Dictionaries

#### `.theory` :: Hatchery theory
> [!IMPORTANT]
> This is upcoming!

A collection of rules and settings to use when converting Hatchery entries to strokable outlines.

#### `.hatchery` :: Hatchery dictionary
A Hatchery entry list. Hatchery dictionary files inherit from the TOML file format.

We can define entries using multiple formats. Firstly, we can directly define a mapping between a steno outline and a translation, as with a typical Plover JSON dictionary:
```toml
[entries."hang:1"]
format = "steno"
translation = "hang"
steno = "HAPBG"
```

Often we won't be doing this for things other than briefs, since the number of valid steno outlines for a word can be prohibitively large. Within a given theory, we can instead define it in terms of the *theory symbols* which that theory defines, letting the theory do all the heavylifting of figuring out all possible valid outlines when you stroke:
```toml
[entries."hang:1"]
format = "theory_symbols"
translation = "hang"
theory_symbols = "H A NG"
```
Of course, theory symbols are theory-defined, so they are hard to transfer to another theory.

A lot of the entries defined in the default dictionary instead opt to use *sophemes* directly:
```toml
[entries."hang:1"]
format = "sophemes" 
translation = "hang"  # optional, overrides the translation that can be built from the sopheme sequence
sophemes = "h.[h] a.ae!1 ng./ŋ/"
```

As seen here, the sophemes themselves have three levels of specificity to use for sounds as needed:
1. `/.../` represents a **broad IPA** transcription. *(These are easier to author, but they provide the least information and are the least portable.)*
1. `[...]` represents a **narrow IPA** transcription.
1. Non-IPA sound symbols are **abstract**. These are meant to be accent-aware; various accent rules can be applied to convert abstract symbols into narrow IPA, which the theories can then operate on. *(These are harder to author because these aren't as standard as IPA and new ones will need custom accent rules written for them, but they are the most portable across different accents.)*

Phonetics have these options due to the huge variety of accents and pronunciations compared to, say, regional spellings.

These entry and sopheme sound symbol formats represent a spectrum of authoring ease versus portability tradeoffs:
1. **Steno** :: most convenient, least portable
1. **Theory symbols**
1. **Sophemes with broad IPA**
1. **Sophemes with narrow IPA**
1. **Sophemes with abstract sounds** :: least convenient, more portable

---

Upon loading a dictionary, Hatchery will apply your given theory rules and mappings to each entry, alongside rules such as vowel elision. The end result is that **any valid writeout** for an entry, with any combination of valid chords, elisions, and syllabic splits, will map to that entry (or some conflicting entry).

Sometimes, an outline will map to multiple possible translations, known as **<ins>conflicts</ins>**. Conflicts are ordered using a cost mechanism, determined by counting the number of abbreviation methods used in the outline, such as elisions (sorted into different types, such as stressed vowel vs unstressed vowel vs consonant) and clusters. The theory can specify these cost amounts as well as a variation cycler stroke that allows you to switch between the different conflicts in increasing order of cost.


##### Other sections
Apart from entry definitions, Hatchery dictionaries also may have the following sections:

```toml
[meta]
hatchery-format-version = "0.0.0"  # Hatchery dictionary file format version, for future migrations and backward compatibility

[macros.sophemes]  # Optional. An arbitrary list of macros that can replace sophemes
m = "m.m"  # Can be invoked as `{m}`
```

##### Generating a Hatchery dictionary from JSON
`./local-utils/json_to_hatchery.py` takes a standard JSON dictionary (such as `lapwing-base.json`) and the [Unisyn v1.3](https://www.cstr.ed.ac.uk/projects/unisyn/) Unilex lexicon as input and produces a Hatchery dictionary as an output by automatically matching letters with phonemes/keysymbols.

Command line usage:
```
json_to_hatchery.py [-h] -j IN_JSON_PATH -u IN_UNILEX_PATH -o OUT_PATH
```

## Methodology
*See the algorithms being ideated and developed in the [algorithm drafting whiteboard](https://www.figma.com/board/22f2V9ufYxLdvBtGWj6nXv/Hatchery?node-id=0-1&t=rvw11Srj6YIEvjmo-1)*

Hatchery attempts to store a huge number of outlines implicitly using custom data structures, instead of a direct outline-to-translation mapping like typical JSON dictionaries (so more like a Python dictionary).

### Intermediate entry representation
Hatchery dictionaries are (or will be) intended to be added to directly. However, for testing or as a base, a JSON dictionary along with the Unilex lexicon can be used to generate a large starter dictionary (using `./local-utils/json_to_hatchery.py`).

Letters, steno chords, and keysymbols are matched and aligned using a modified variant of the [Needleman–Wunsch string alignment algorithm](https://en.wikipedia.org/wiki/Needleman–Wunsch_algorithm). First, letters are matched with keysymbols, and then those "orthokeysymbols" are matched with steno chords.

A key modification is that the mapping is many-to-many, as in, multiple letters can match with multiple keysymbols and multiple orthokeysymbols can match with multiple steno keys, as opposed to stock Needleman–Wunsch which can only match single letters. If we are aligning the sequences $x, y$ and are currently computing the cost in cell $i, j$, then in stock Needleman–Wunsch we take the minimum among 3 costs: an indel of $x_i$, an indel of $y_j$, and a match/mismatch of $x_i, y_j$. Our modified alignment algorithm is supplied a dictionary of substrings of $x$ which map to substrings of $y$ that the aligner will consider a match. For each cell, our modified algorithm still considers the indel and mismatch cases, but for matches it will test every substring of $x$ that ends at position $i$ and look it up in the dictionary to see if it maps to some substring of $y$ that ends at position $j$. If $x, y$ have lengths $m, n$ respectively, then this incurs an additional cost of $O(m)$ for each cell, resulting in an overall time complexity of $O(m^2 n)$ amortized.

![String alignment diagram](https://github.com/user-attachments/assets/25295963-cd4f-431c-bbea-439c7e435d26)

Lapwing can be converted into a Hatchery dictionary in about 3 to 5 minutes.

### Lookup
The number of possible outlines for an entry depends on the number of combinations of possible elisions, syllabic splits, and chord choices, which scales roughly exponentially with the length of the entry. To store all these possible options while limiting redundant storage, we use a [nondeterministic finite automaton/state machine](https://en.wikipedia.org/wiki/Nondeterministic_finite_automaton) that functions as a [trie](https://en.wikipedia.org/wiki/Trie). Transitions are associated with one or more steno keys, with some special entries for linkers and stroke boundaries.

![Lookup trie diagram](https://github.com/user-attachments/assets/16bedccd-0ea7-4c10-b514-54b604c968d8)

While constructing paths in the trie, transitions are also associated with a (cost, translation) pair.
* The translation is used to ensure that the paths traversed during the lookup align with the translation that is found when there are no more keys in the outline to read. If a translation is found for an outline, but the path used to reach the node has some transition that is not associated with the translation, then the path is ignored.
* The cost is used to determine which translation to use in the case of conflicts, which occur when the set of nodes an outline ends at is associated with multiple valid translations. The cost is determined by e.g. whether the path is part of a cluster, inversion, elision, etc.

Constructing the trie for the entirety of Lapwing takes about 18 seconds.

### Performance
Assuming:
1. $O(1)$ dictionary/hashmap lookups
1. $O(1)$ operations on strings read from files
1. Word length $\propto$ writeout outline length for that word

|Method|Notes|# outlines encoded per entry (for entry of length $n$)|Entry preprocess time (for entry of length $n$)|Outline lookup time (for outline of length $n$)|
|-|-|-|-|-|
|JSON|Direct mapping between steno outlines and translations|$1$|$O(1)$|$O(n)$|
|[Runtime folding](https://github.com/wooningeire/plover-custom-folding)|Direct mapping except arbitrary combinations of chord folding conditions are checked for each mapped outline|$O(2^\text{\# folding rules})$|$O(1)$|$O(2^\text{\# folding rules})$|
|[Froj](https://github.com/StenoHarri/Froj)|Theory rules are applied against a [lexicon](https://www.cstr.ed.ac.uk/projects/unisyn/) to compile all possible outlines for each word in the lexicon to a JSON dictionary|?|$O(2^n)$|$O(1)$|
|Hatchery (no inversions)|Theory rules are applied against a dictionary to pregenerate a lookup trie which is used at runtime|?|$O(n)$|$O(1)$|
|Hatchery (with inversions)|Hatchery but all possible consonant conversions are added to the trie|?|$O(n^2\log(n))$|$O(n\log(n))$|

## Development
Like all Plover plugins, this is a Python project. We'll use [uv](https://docs.astral.sh/uv/) to manage dependencies.

This project also contains a Rust component for performance, so [cargo](https://rust-lang.org/tools/install/) must also be installed.

1. Create a virtual environment: `uv venv --python 3.13`
1. Enter the virtual environment: `./.venv/Scripts/activate`
1. Install dependencies: `uv pip install .`
1. Build the Rust component and add it to Plover: `uv run local-utils/maturin_dev.py --plover-path "C:/Program Files/Open Steno Project/Plover 5.1.0" --release`
    1. You may also want to add the Rust component to your virtual environment: `uv pip install ./plover_hatchery_lib_rs`
1. Add the plugin to Plover: `uv run local-utils/plover_install.py --plover-path "C:/Program Files/Open Steno Project/Plover 5.1.0"`

From here on, we can rebuild the plugin and relaunch Plover in a single script to test any new code changes:

1. `uv run local-utils/plover_debug.py --maturin-dev --reinstall --plover-path "C:/Program Files/Open Steno Project/Plover 5.1.0"`

### Testing
Python side: `uv run pytest`

Rust side: `cd plover_hatchery_lib_rs && cargo test`
