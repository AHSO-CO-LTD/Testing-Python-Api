"""
Build script: compile all .py files in lib/ to .pyd using Cython,
output directly to module/. Generated .c files are kept in build_cython/.

Usage:
    python build_pyd.py
"""

import os
import glob
from setuptools import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

Options.docstrings = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(BASE_DIR, "lib")
OUTPUT_DIR = os.path.join(BASE_DIR, "module")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Collect all .py files in lib/ (skip __init__.py if present)
py_files = [
    f
    for f in glob.glob(os.path.join(LIB_DIR, "*.py"))
    if os.path.basename(f) != "__init__.py"
]

setup(
    name="lib_modules",
    ext_modules=cythonize(
        py_files,
        compiler_directives={"language_level": "3"},
        build_dir="build_cython",
    ),
    script_args=["build_ext", f"--build-lib={OUTPUT_DIR}"],
)

# built = glob.glob(os.path.join(OUTPUT_DIR, "*.pyd"))
# if built:
#     print(f"\n[OK] Built {len(built)} .pyd file(s) in '{OUTPUT_DIR}':")
#     for f in built:
#         print(f"     {os.path.basename(f)}")
# else:
#     print("\n[WARNING] No .pyd files found in output. Check build output above.")
