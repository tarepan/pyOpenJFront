"""pyopenjfront tests."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyopenjtalk


def test_hello() -> None:
    njd_features = pyopenjtalk.run_frontend("こんにちは")
    for f in njd_features:
        _, _ = f["string"], f["pron"]


def test_njd_features() -> None:
    njd_features = pyopenjtalk.run_frontend("こんにちは")
    expected_feature = [
        {
            "string": "こんにちは",
            "pos": "感動詞",
            "pos_group1": "*",
            "pos_group2": "*",
            "pos_group3": "*",
            "ctype": "*",
            "cform": "*",
            "orig": "こんにちは",
            "read": "コンニチハ",
            "pron": "コンニチワ",
            "acc": 0,
            "mora_size": 5,
            "chain_rule": "-1",
            "chain_flag": -1,
        }
    ]
    assert njd_features == expected_feature


def test_jtalk() -> None:
    for text in [
        "今日も良い天気ですね",
        "こんにちは。",
        "どんまい！",
        "パソコンのとりあえず知っておきたい使い方",
    ]:
        njd_features = pyopenjtalk.run_frontend(text)
        for f in njd_features:
            _, _ = f["string"], f["pron"]

        surface = "".join([f["string"] for f in njd_features])
        assert surface == text


def test_g2p_kana() -> None:
    for text, pron in [
        ("今日もこんにちは", "キョーモコンニチワ"),
        ("いやあん", "イヤーン"),
        (
            "パソコンのとりあえず知っておきたい使い方",
            "パソコンノトリアエズシッテオキタイツカイカタ",
        ),
    ]:
        p = pyopenjtalk.g2p(text, kana=True)
        assert p == pron


def test_g2p_phone() -> None:
    for text, pron in [
        ("こんにちは", "k o N n i ch i w a"),
        ("ななみんです", "n a n a m i N d e s U"),
        ("ハローユーチューブ", "h a r o o y u u ch u u b u"),
    ]:
        p = pyopenjtalk.g2p(text, kana=False)
        assert p == pron


def test_userdic() -> None:
    for text, expected in [
        ("nnmn", "n a n a m i N"),
        ("GNU", "g u n u u"),
    ]:
        p = pyopenjtalk.g2p(text)
        assert p != expected

    user_csv = Path(__file__).parent / "test_data" / "user.csv"
    user_dic = str(Path(__file__).parent / "test_data" / "user.dic")

    with user_csv.open("w", encoding="utf-8") as f:
        f.write("ｎｎｍｎ,,,1,名詞,一般,*,*,*,*,ｎｎｍｎ,ナナミン,ナナミン,1/4,*\n")
        f.write("ＧＮＵ,,,1,名詞,一般,*,*,*,*,ＧＮＵ,グヌー,グヌー,2/3,*\n")

    pyopenjtalk.mecab_dict_index(f.name, user_dic)
    pyopenjtalk.update_global_jtalk_with_user_dict(user_dic)

    for text, expected in [
        ("nnmn", "n a n a m i N"),
        ("GNU", "g u n u u"),
    ]:
        p = pyopenjtalk.g2p(text)
        assert p == expected


def test_multithreading() -> None:
    ojt = pyopenjtalk.openjtalk.OpenJTalk(pyopenjtalk.OPEN_JTALK_DICT_DIR)
    texts = [
        "今日もいい天気ですね",
        "こんにちは",
        "マルチスレッドプログラミング",
        "テストです",
        "Pythonはプログラミング言語です",
        "日本語テキストを音声合成します",
    ] * 4

    # Test consistency between single and multi-threaded runs
    # make sure no corruptions happen in OJT internal
    results_s = [ojt.run_frontend(text) for text in texts]
    results_m = []
    with ThreadPoolExecutor() as e:
        results_m = list(e.map(ojt.run_frontend, texts))
    for s, m in zip(results_s, results_m, strict=True):
        assert len(s) == len(m)
        for s_, m_ in zip(s, m, strict=True):
            # full context must exactly match
            assert s_ == m_
