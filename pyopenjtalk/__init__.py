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
from typing import TypedDict
from urllib.request import urlopen

try:
    from .version import __version__  # noqa: F401, false-positive
except ImportError as e:
    msg = "BUG: version.py doesn't exist. Please file a bug report."
    raise ImportError(msg) from e

from .openjtalk import OpenJTalk
from .openjtalk import mecab_dict_index as _mecab_dict_index

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


def _global_instance_manager(
    instance: OpenJTalk | None,
) -> Callable[[], Generator[OpenJTalk, None, None]]:
    """Generate an instance manager, which enable singleton-like global instance."""
    _instance = instance
    mutex = Lock()

    @contextmanager
    def manager() -> Generator[OpenJTalk, None, None]:
        nonlocal _instance
        with mutex:
            if _instance is None:
                if not Path(str(OPEN_JTALK_DICT_DIR)).exists():
                    _extract_dic()
                _instance = OpenJTalk(dn_mecab=OPEN_JTALK_DICT_DIR)
            yield _instance

    return manager


# Global instance of OpenJTalk
_global_jtalk = _global_instance_manager(None)


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


def run_frontend(text: str) -> list[OjtNjdFeature]:
    """Process text into OpenJTalk NJD features."""
    with _global_jtalk() as jtalk:
        return jtalk.run_frontend(text)


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
            OpenJTalk(dn_mecab=OPEN_JTALK_DICT_DIR, userdic=path.encode("utf-8"))
        )
