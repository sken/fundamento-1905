# fundamento-1905

The *Fundamento de Esperanto* (L. L. Zamenhof, 1905) as plain text and machine-readable data.

The Fundamento is the binding core of Esperanto, declared unchangeable at the first World Esperanto Congress in Boulogne-sur-Mer (1905). It has four parts: a foreword, a grammar of 16 rules, a book of exercises and a root dictionary. Grammar and dictionary are given in five languages: French, English, German, Russian and Polish.

## Contents

```
teksto/                         the text, as Markdown
  1-antauparolo.md              Antaŭparolo (foreword, Esperanto)
  2-gramatiko-{fr,en,de,ru,pl}.md   Gramatiko in the five original languages
  3-ekzercaro.md                Ekzercaro (exercises, §1–§42)
data/
  reguloj.json                  the 16 grammar rules, one object per rule, in all five languages
  universala-vortaro.json       Universala Vortaro: 2,636 roots with translations and listed derivations
  universala-vortaro.csv        the same, flat: 2,933 rows (roots + derivations)
tools/
  build.py                      converts the source HTML into the files above
```

### `data/universala-vortaro.json`

```json
{
  "radiko": "aĉet'",
  "litero": "A",
  "fr": "acheter", "en": "buy", "de": "kaufen", "ru": "покупать", "pl": "kupować",
  "derivajhoj": [
    { "radiko": "sub'aĉet'", "fr": "corrompre", "en": "corrupt", "de": "bestechen", "ru": "подкупать", "pl": "przekupyvać" }
  ]
}
```

- `radiko` keeps Zamenhof's apostrophe notation, which marks the boundaries between word parts (`frat'in'o` = brother + female + noun). The CSV adds a column without apostrophes for searching.
- `litero` is the dictionary section, as printed (`"C, Ĉ"` etc.).
- The translations use the 1905 spelling, including pre-reform Russian orthography (`аббатъ`). This is deliberate: the Fundamento is reproduced as it was published, not modernized.

### `data/reguloj.json`

```json
{ "n": 10, "de": "Der Accent fällt immer auf die vorletzte Silbe.", "en": "…", "fr": "…", "ru": "…", "pl": "…" }
```

`n` is the rule's position. The 1905 English grammar prints rule 13 with the number 15. That misprint is part of the original and is recorded as `"presita_numero": {"en": 15}` instead of being corrected silently.

## Faithful to the original

The Fundamento is meant to stay unchanged, errors included, so this repository does not fix anything in the text. Old spellings such as *Hülfe*, *Thier* or *deklinirt*, misprints and inconsistencies stay as they are. Fixes belong in `tools/build.py` only when the conversion itself went wrong.

## Source

The text was extracted from the digital edition of the Akademio de Esperanto, <https://www.akademio-de-esperanto.org/fundamento/>, via the copy at <https://github.com/egrimley/fundamento> (commit `b08904b`, 2020-12-31). Only the text of the Fundamento was taken. The Akademio's page layout, navigation and links to its dictionary were removed.

To rebuild:

```sh
git clone https://github.com/egrimley/fundamento source
python3 -I tools/build.py source .
```

Python 3 standard library only.

## License

The Fundamento de Esperanto was published in 1905. Its author died in 1917. The text is in the **public domain**.

Everything else in this repository (data formats, Markdown conversion, the build script, this README) is dedicated to the public domain under **CC0 1.0**. See [LICENSE](LICENSE).
