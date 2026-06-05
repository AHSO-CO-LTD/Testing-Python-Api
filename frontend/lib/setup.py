from distutils.core import setup
from Cython.Build import cythonize

# Danh sách file cần build
modules_to_build = [
    "Display.py",
    "Main_Screen.py",
    "Camera_Program.py",
    "Global.py",
    "Login_Screen.py",
    "PLC.py",
    "Database.py",
    "Authentication.py",
    "StackUI.py"
]

# Lặp qua từng file
for module in modules_to_build:
    print(f"Building {module}...")
    setup(
        name=module.replace(".py", ""),
        ext_modules=cythonize(module, language_level="3")
    )

# import os

# for file in ["Display.c", "Main_Screen.c", "PLC.c", "Camera_Program.c", "Global.c",
#              "Login_Screen.c", "Databse.c"]:
#     if os.path.exists(file):
#         os.remove(file)

# command terminal: python setup.py build_ext --inplace
# command terminal: python setup.py build_ext --build-lib E:/DRB-OCR-AI/module


