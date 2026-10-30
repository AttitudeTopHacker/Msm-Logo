from setuptools import setup, find_packages

setup(
    name="msmlogo",
    version="1.0.1",
    description="A lightweight and user-friendly GUI tool to create, customize and 1-Click apply Plymouth Boot Logos and GRUB backgrounds on Linux.",
    author="MsmLogo Team",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.5.0",
        "Pillow>=9.0.0"
    ],
    entry_points={
        "console_scripts": [
            "msmlogo=msmlogo.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
        "Topic :: System :: Boot",
    ],
    python_requires=">=3.8",
)
