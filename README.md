<div align="center">

# 📃 pyOpenJFront 🔡 <!-- omit in toc -->

[![License](http://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](LICENSE.md)

Simple-and-Modern Text-processing Frontend of [Open JTalk](http://open-jtalk.sp.nitech.ac.jp/), wrapped by Python.  
シンプルかつモダンな Open JTalk テキスト分析フロントエンドの Python ラッパー
</div>

## How to Use
### Installation

```
pip install pyopenjtalk
```

### Grapheme-to-Tree (G2Tree)
WIP

### Grapheme-to-phoeneme (G2P)

```py
In [1]: import pyopenjtalk

In [2]: pyopenjtalk.g2p("こんにちは")
Out[2]: 'k o N n i ch i w a'

In [3]: pyopenjtalk.g2p("こんにちは", kana=True)
Out[3]: 'コンニチワ'
```

### Create/Apply user dictionary

1. Create a CSV file (e.g. `user.csv`) and write custom words like below:

```csv
ＧＮＵ,,,1,名詞,一般,*,*,*,*,ＧＮＵ,グヌー,グヌー,2/3,*
```

2. Call `mecab_dict_index` to compile the CSV file.

```python
In [1]: import pyopenjtalk

In [2]: pyopenjtalk.mecab_dict_index("user.csv", "user.dic")
reading user.csv ... 1
emitting double-array: 100% |###########################################|

done!
```

3. Call `update_global_jtalk_with_user_dict` to apply the user dictionary.

```python
In [3]: pyopenjtalk.g2p("GNU")
Out[3]: 'j i i e n u y u u'

In [4]: pyopenjtalk.update_global_jtalk_with_user_dict("user.dic")

In [5]: pyopenjtalk.g2p("GNU")
Out[5]: 'g u n u u'
```

## APIs
- `pyopenjtalk.g2p(text: str, kana: bool = False, join: bool = True) -> str | list[str]`: Grapheme-to-phoeneme conversion.
  - `kana`: If True, returns the pronunciation in katakana, otherwise in phone.
  - `join`: If True, concatenate phones or katakana's into a single string.
- `pyopenjtalk.run_frontend(text: str) -> list[OjtNjdFeature]`: Run OpenJTalk's text processing frontend.
- `pyopenjtalk.mecab_dict_index(path: str, out_path: str, dn_mecab: str | None = None) -> None`: Create user dictionary.
- `pyopenjtalk.update_global_jtalk_with_user_dict(path: str) -> None`: Update global openjtalk instance with the user dictionary.

## Supported platforms

- Linux
- Mac OSX
- Windows (MSVC) (see [this PR](https://github.com/r9y9/pyopenjtalk/pull/13))

## LICENSE

- pyopenjtalk: MIT license ([LICENSE.md](LICENSE.md))
- Open JTalk: Modified BSD license ([COPYING](https://github.com/r9y9/open_jtalk/blob/1.10/src/COPYING))

## Acknowledgements

HTS Working Group for their dedicated efforts to develop and maintain Open JTalk.

## Development

### Requirements
Following tools are needed for build:

- C/C++ compilers
- cmake
- cython

To build the package locally, you will need to make sure to clone open_jtalk.

```
git submodule update --recursive --init
```

### Installation
```bash
# Install dependencies
pip install .[dev]

# Install git hooks
pre-commit install -t pre-push
```

### Check
```bash
## Check at once
mypy . && ruff check && ruff format --check && typos && pytest

## Check and fix at once
mypy . && ruff check --fix && ruff format && typos && pytest
```

### Build
```bash
pip install -e .
```

## Differences from pyopenjtalk
pyOpenJFront is simplified and modernized version of `pyopenjtalk`.  

Removed features are listed below:  

- `pyopenjtalk.tts()`
- `pyopenjtalk.synthesize()`
- `pyopenjtalk.extract_fullcontext()`
- `pyopenjtalk.make_label()`
- `pyopenjtalk.estimate_accent()`
- Notebooks
- Docs

If you want to use [MARINE](https://github.com/6gsn/marine) for accent refinement, you can use it with `.run_frontend()` and custom parser (check [pyopenjtalk codes](https://github.com/r9y9/pyopenjtalk/blob/0f0fc44e782a8134cd9a51d80b57b48a7c95bb80/pyopenjtalk/__init__.py#L140-L159)).  

New features are listed below:

- Full type hints
- Cython 3.x
- Modern checkers (mypy + Ruff + typos + pytest)

If you needs more-rich-feature pyopenjtalk, [`pyopenjtalk-plus`](https://github.com/tsukumijima/pyopenjtalk-plus) will help you 😉


## Motivation
(private memo)  

There are 3 main motivations of pyOpenJFront

- Open JTalk is so strong
- Open JTalk / pyopenjtalk has heavy technical debt
- fullcontextlabel is not enough

As a results, "keeping only OJT core functionality with modern stacks" came to my mind.  

### Open JTalk is so strong
Open JTalk released at 2009 (v1.00) / 2018 (v1.11), but its accent performance is still near-SoTA.  
ML-based methods do not yet outperform rule-based OJT, especially in the sense of accent stability. Accent stability is critical for Japanese TTS naturalness.  
In my impression, this situation will continue several years, especially in editable TTS.  
Open JTalk is so strong.  

### Open JTalk pyopenjtalk has heavy technical debt
Open JTalk released at 2009 (v1.00) / 2018 (v1.11), and pyopenjtalk released at 2018.  
In IT engineering, 10 years is so long. The ecosystem change totally.  
If you hope to keep backward compatibility, you needs daily refactoring and OJT-specific heavy customs.  
Open JTalk / pyopenjtalk has heavy technical debt.  

### fullcontextlabel is not enough
full-context label is too specialized to HTS.  
In ML-era, more information is needed.  
fullcontextlabel is not enough.
