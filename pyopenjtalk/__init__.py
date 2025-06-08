"""pyopenjtalk."""

import atexit
import logging
import os
import tarfile
import tempfile
from collections.abc import Callable, Generator
from contextlib import ExitStack, contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from threading import Lock
from typing import TypedDict, TypeVar
from urllib.request import urlopen

try:
    from .version import __version__  # noqa: F401, false-positive
except ImportError as e:
    msg = "BUG: version.py doesn't exist. Please file a bug report."
    raise ImportError(msg) from e

from .openjtalk import OpenJTalk
from .openjtalk import mecab_dict_index as _mecab_dict_index
from .utils import merge_njd_marine_features

logger = logging.getLogger(__name__)

_file_manager = ExitStack()
atexit.register(_file_manager.close)

_pyopenjtalk_ref = files(__name__)  # NOTE: package directory
_dic_dir_name = "open_jtalk_dic_utf_8-1.11"

# dictionary path. Env `OPEN_JTALK_DICT_DIR` or the package directory.
OPEN_JTALK_DICT_DIR = os.environ.get(
    "OPEN_JTALK_DICT_DIR",
    str(_file_manager.enter_context(as_file(_pyopenjtalk_ref / _dic_dir_name))),
).encode("utf-8")
_DICT_URL = "https://github.com/r9y9/open_jtalk/releases/download/v1.11.1/open_jtalk_dic_utf_8-1.11.tar.gz"


def _extract_dic() -> None:
    """Download and extract the dictionary under the package."""
    from tqdm.auto import tqdm

    global OPEN_JTALK_DICT_DIR  # noqa: PLW0603, demerit is accepted.
    pyopenjtalk_dir = _file_manager.enter_context(as_file(_pyopenjtalk_ref))

    # Download and extract the dictionary file
    with tempfile.TemporaryFile() as t:
        msg = f'Downloading: "{_DICT_URL}"'
        logger.info(msg)
        with urlopen(_DICT_URL) as response:  # noqa: S310,SIM117, trusted URL, false-positive
            with tqdm.wrapattr(
                t, "write", total=getattr(response, "length", None)
            ) as tar:
                for chunk in response:
                    tar.write(chunk)
        t.seek(0)
        logger.info("Extracting tar file")
        with tarfile.open(mode="r|gz", fileobj=t) as f:
            f.extractall(path=pyopenjtalk_dir)  # noqa: S202, trusted archive file

    # Update the dictionary path
    OPEN_JTALK_DICT_DIR = str(pyopenjtalk_dir / _dic_dir_name).encode("utf-8")


def _lazy_init() -> None:
    """Prepare the dictionary."""
    if not Path(str(OPEN_JTALK_DICT_DIR)).exists():
        _extract_dic()


_T = TypeVar("_T")


def _global_instance_manager(
    instance_factory: Callable[[], _T] | None = None, instance: _T | None = None
) -> Callable[[], Generator[_T, None, None]]:
    """Generate an instance manager, which enable singleton-like global instance."""
    if instance_factory is None and instance is None:
        msg = "Either instance_factory or instance should be not None."
        raise RuntimeError(msg)

    _instance = instance
    mutex = Lock()

    @contextmanager
    def manager() -> Generator[_T, None, None]:
        nonlocal _instance
        with mutex:
            if _instance is None:
                _instance = instance_factory()
            yield _instance

    return manager


def _jtalk_factory() -> OpenJTalk:
    """Generate new OpenJTalk instance with the dictionary."""
    _lazy_init()
    return OpenJTalk(dn_mecab=OPEN_JTALK_DICT_DIR)


def _marine_factory():  # noqa: ANN202, because of conditional import.
    """Generate new MARINE instance."""
    try:
        from marine.predict import Predictor
    except ImportError as e:
        msg = "Please install marine by `pip install pyopenjtalk[marine]`"
        raise ImportError(msg) from e
    return Predictor()


# Global instance of OpenJTalk
_global_jtalk = _global_instance_manager(_jtalk_factory)
# Global instance of Marine
_global_marine = _global_instance_manager(_marine_factory)


class OjtNjdFeature(TypedDict):
    """Open JTalk NJD feature."""

    string: str
    pos: str
    pos_group1: str
    pos_group2: str
    pos_group3: str
    ctype: str
    cform: str
    orig: str
    read: str
    pron: str
    acc: int
    mora_size: int
    chain_rule: str
    chain_flag: int


def g2p(text: str, *, kana: bool = False, join: bool = True) -> str | list[str]:
    """Grapheme-to-phoeneme (G2P) conversion.

    This is just a convenient wrapper around `run_frontend`.

    Parameters
    ----------
        text: Unicode Japanese text.
        kana: If True, returns the pronunciation in katakana, otherwise in phone.
        join: If True, concatenate phones or katakana's into a single string.

    Returns
    -------
        G2P results. Joined string or list of symbols.
    """
    with _global_jtalk() as jtalk:
        return jtalk.g2p(text, kana=kana, join=join)


class MarineFeature(TypedDict):
    """MARINE feature."""

    surface: str
    pos: str  # pos + pos_group1 + pos_group2 + pos_group3
    pron: str | None
    c_type: str
    c_form: str
    accent_type: int
    accent_con_type: str  # chain rule
    chain_flag: str


def estimate_accent(njd_features: list[OjtNjdFeature]) -> list[OjtNjdFeature]:
    """Accent estimation using marine.

    This function requires marine (https://github.com/6gsn/marine)

    Parameters
    ----------
        njd_result (list): features generated by OpenJTalk.

    Returns
    -------
        list: features for NJDNode with estimation results by marine.
    """
    with _global_marine() as marine:
        from marine.utils.openjtalk_util import convert_njd_feature_to_marine_feature

        marine_features: list[MarineFeature] = convert_njd_feature_to_marine_feature(
            njd_features
        )
        marine_results = marine.predict(
            [marine_features], require_open_jtalk_format=True
        )
    return merge_njd_marine_features(njd_features, marine_results)


def run_frontend(text: str, *, run_marine: bool = False) -> list[OjtNjdFeature]:
    """Run OpenJTalk's text processing frontend.

    Parameters
    ----------
        text: Unicode Japanese text.
        run_marine: Whether to estimate accent using marine.
          When use, need to install marine by `pip install pyopenjtalk[marine]`.

    Returns
    -------
        features for NJDNode.
    """
    with _global_jtalk() as jtalk:
        njd_features = jtalk.run_frontend(text)
    if run_marine:
        njd_features = estimate_accent(njd_features)
    return njd_features


def mecab_dict_index(path: str, out_path: str, dn_mecab: str | None = None) -> None:
    """Create user dictionary.

    Parameters
    ----------
        path: path to user csv
        out_path: path to output dictionary
        dn_mecab: path to mecab dictionary
    """
    if not Path(path).exists():
        msg = f"no such file or directory: {path}"
        raise FileNotFoundError(msg)

    if dn_mecab is None:
        # NOTE: Prepare the dictionary through `_lazy_init()` call
        with _global_jtalk():
            pass
        dn_mecab = OPEN_JTALK_DICT_DIR

    r = _mecab_dict_index(dn_mecab, path.encode("utf-8"), out_path.encode("utf-8"))
    # NOTE: mecab load returns 1 if success, but mecab_dict_index return the opposite
    if r != 0:
        msg = "Failed to create user dictionary"
        raise RuntimeError(msg)


def update_global_jtalk_with_user_dict(path: str) -> None:
    """Update global openjtalk instance with the user dictionary.

    Note that this will change the global state of the openjtalk module.

    Parameters
    ----------
        path: path to user dictionary
    """
    global _global_jtalk  # noqa: PLW0603, demerit is accepted.
    with _global_jtalk():
        if not Path(path).exists():
            msg = f"no such file or directory: {path}"
            raise FileNotFoundError(msg)
        _global_jtalk = _global_instance_manager(
            instance=OpenJTalk(
                dn_mecab=OPEN_JTALK_DICT_DIR, userdic=path.encode("utf-8")
            )
        )
