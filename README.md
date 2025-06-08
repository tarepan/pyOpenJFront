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

### About `run_marine` option

The `run_marine` option enable Japanese accent estimation with the DNN-based method (see [marine](https://github.com/6gsn/marine)).  

If you want to use the feature, please install pyopenjtalk as below;

```shell
pip install pyopenjtalk[marine]
```

And then, you can use the option as the following examples;

```python
In [1]: import pyopenjtalk

In [2]: label = pyopenjtalk.run_frontend("こんにちは", run_marine=True) # for text processing frontend only
```

## APIs
- `pyopenjtalk.g2p(text: str, kana: bool = False, join: bool = True) -> str | list[str]`: Grapheme-to-phoeneme conversion.
  - `kana`: If True, returns the pronunciation in katakana, otherwise in phone.
  - `join`: If True, concatenate phones or katakana's into a single string.
- `pyopenjtalk.estimate_accent(njd_features: list[OjtNjdFeature]) -> list[OjtNjdFeature]`
- `pyopenjtalk.run_frontend(text: str, run_marine: bool = False) -> list[OjtNjdFeature]`: Run OpenJTalk's text processing frontend.
  - `run_marine`: Whether to estimate accent using marine.
- `pyopenjtalk.mecab_dict_index(path: str, out_path: str, dn_mecab: str | None = None) -> None`: Create user dictionary.
- `pyopenjtalk.update_global_jtalk_with_user_dict(path: str) -> None`: Update global openjtalk instance with the user dictionary.

## Supported platforms

- Linux
- Mac OSX
- Windows (MSVC) (see [this PR](https://github.com/r9y9/pyopenjtalk/pull/13))

## LICENSE

- pyopenjtalk: MIT license ([LICENSE.md](LICENSE.md))
- Open JTalk: Modified BSD license ([COPYING](https://github.com/r9y9/open_jtalk/blob/1.10/src/COPYING))
- marine: Apache 2.0 license ([LICENSE](https://github.com/6gsn/marine/blob/main/LICENSE))

## Acknowledgements

HTS Working Group for their dedicated efforts to develop and maintain Open JTalk.

## Development

## Requirements
Following tools are needed for build:

- C/C++ compilers
- cmake
- cython

To build the package locally, you will need to make sure to clone open_jtalk.

```
git submodule update --recursive --init
```

### Check
```bash
## 一括でチェックと可能な範囲の自動修正をおこなう
ruff check --fix && ruff format && pytest
```

### Test
```bash
pytest
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
- Notebooks

New featues are listed below:

- Full type hints
- MARINE option in `run_frontend()` (could be removed)

If you needs more-rich-feature pyopenjtalk, [`pyopenjtalk-plus`](https://github.com/tsukumijima/pyopenjtalk-plus) will help you 😉