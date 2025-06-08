"""Build workflow."""

import logging
import os
import subprocess
import sys
from itertools import chain
from pathlib import Path
from typing import Final, Literal

import setuptools.command.build_ext
from setuptools import Extension, setup

logger = logging.getLogger(__name__)

platform_is_windows = sys.platform == "win32"

msvc_extra_compile_args_config: Final = [
    "/source-charset:utf-8",
    "/execution-charset:utf-8",
]


def _msvc_extra_compile_args(compile_args: list[str]) -> list[str]:
    cas = set(compile_args)
    xs = filter(lambda x: x not in cas, msvc_extra_compile_args_config)
    return list(chain(compile_args, xs))


msvc_define_macros_config: Final = [
    ("_CRT_NONSTDC_NO_WARNINGS", None),
    ("_CRT_SECURE_NO_WARNINGS", None),
]


def _msvc_define_macros(
    macros: list[tuple[str, str | None]],
) -> list[tuple[str, str | None]]:
    mns = set([i[0] for i in macros])  # noqa: C403, false-positive?
    xs = filter(lambda x: x[0] not in mns, msvc_define_macros_config)
    return list(chain(macros, xs))


class custom_build_ext(setuptools.command.build_ext.build_ext):  # noqa: N801
    """Custom `build_ext`."""

    def build_extensions(self) -> None:
        """build_extensions."""
        compiler_type_is_msvc = self.compiler.compiler_type == "msvc"
        for entry in self.extensions:
            if compiler_type_is_msvc:
                entry.extra_compile_args = _msvc_extra_compile_args(
                    entry.extra_compile_args
                    if hasattr(entry, "extra_compile_args")
                    else []
                )
                entry.define_macros = _msvc_define_macros(
                    entry.define_macros if hasattr(entry, "define_macros") else []
                )

        setuptools.command.build_ext.build_ext.build_extensions(self)


def _check_cmake_in_path() -> tuple[Literal[True], str] | tuple[Literal[False], None]:
    try:
        result = subprocess.run(
            ["cmake", "--version"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            # CMake is in the system path
            return True, result.stdout.strip()
    except FileNotFoundError:
        # CMake command not found
        return False, None
    else:
        # CMake is not in the system path
        return False, None


if os.name == "nt":  # Check if the OS is Windows
    # Check if CMake is in the system path
    cmake_found, cmake_version = _check_cmake_in_path()

    if cmake_found:
        msg = f"CMake is in the system path. Version: {cmake_version}"
        logger.info(msg)
    else:
        msg = "CMake is not found in the system path. Make sure CMake is installed and in the system path."
        raise SystemError(msg)

# open_jtalk sources
src_top = Path("lib") / "open_jtalk" / "src"

# generate config.h for mecab
# NOTE: need to run cmake to generate config.h
# we could do it on python side but it would be very tricky,
# so far let's use cmake tool
if not (src_top / "mecab" / "src" / "config.h").exists():
    cwd = Path.getcwd()
    build_dir = src_top / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(build_dir))

    r = subprocess.run(["cmake", ".."], check=False)
    r.check_returncode()
    os.chdir(cwd)

all_src: list[str] = []
include_dirs: list[str] = []
for s in [
    "jpcommon",
    "mecab/src",
    "mecab2njd",
    "njd",
    "njd2jpcommon",
    "njd_set_accent_phrase",
    "njd_set_accent_type",
    "njd_set_digit",
    "njd_set_long_vowel",
    "njd_set_pronunciation",
    "njd_set_unvoiced_vowel",
    "text2mecab",
]:
    all_src += list(map(str, (src_top / s).glob("*.c")))
    all_src += list(map(str, (src_top / s).glob("*.cpp")))
    include_dirs.append(str(Path.cwd() / src_top / s))

# Extension for OpenJTalk frontend
ext_modules = [
    Extension(
        name="pyopenjtalk.openjtalk",
        sources=[str(Path("pyopenjtalk") / "openjtalk.pyx"), *all_src],
        include_dirs=include_dirs,
        extra_compile_args=[],
        extra_link_args=[],
        language="c++",
        define_macros=[
            ("HAVE_CONFIG_H", None),
            ("DIC_VERSION", "102"),
            ("MECAB_DEFAULT_RC", '"dummy"'),
            ("PACKAGE", '"open_jtalk"'),
            ("VERSION", '"1.10"'),
            ("CHARSET_UTF_8", None),
        ],
    )
]

setup(ext_modules=ext_modules, cmdclass={"build_ext": custom_build_ext})
