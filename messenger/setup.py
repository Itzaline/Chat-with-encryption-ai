from cx_Freeze import setup, Executable

build_options = {
    "packages": ["PyQt6", "cryptography", "transformers"],
    "excludes": ["tkinter"],
    "include_files": ["config.py", "shared/"]
}

setup(
    name="SecureChat",
    version="0.1",
    description="Secure E2EE Messenger",
    options={"build_exe": build_options},
    executables=[Executable("client/main.py", base="Win32GUI")]
)