import re
from pathlib import Path
from setuptools import find_packages, setup

here = Path(__file__).parent

init_text = (here / "cryptoarithmetic" / "__init__.py").read_text(encoding="utf-8")
version = re.search(r'^__version__\s*=\s*"([^"]+)"', init_text, re.M).group(1) # read from cryptoarithmetic/__init__.py

setup(
    name="cryptoarithmetic",
    version=version,
    description=("Cryptography from scratch in pure Python, for study: finite fields, elliptic "
                 "curves, Schoof, SHA-2/3, HMAC/KMAC/CMAC, AES, DES, CBC/CTR/GCM, RSA, ECDSA"),
    long_description=(here / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Loris De Vos",
    license="MIT",
    license_files=["LICENSE"],
    keywords="cryptography education elliptic-curves schoof aes rsa sha2 sha3 ecdsa",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Education",
        "Topic :: Security :: Cryptography",
    ],
    packages=find_packages(include=["cryptoarithmetic", "cryptoarithmetic.*"]),
    python_requires=">=3.8",
    install_requires=[],                   # standard library only
)