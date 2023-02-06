from setuptools import setup

setup(
    name="pomo",
    version="0.1.0",
    py_modules=["pomo"],
    install_requires=["rich"],
    entry_points={"console_scripts": ["pomo=pomo:main"]},
)
