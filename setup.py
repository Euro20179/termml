from setuptools import setup

setup(
    name='tml',
    version="1.0.0",
    url='https://www.github.com/euro20179/tml',
    description='The interpreter for the terminal markup language',
    author='Euro',
    packages=['tml'],
    entry_points="""
        [console_scripts]
        tml=tml.tml:main
    """
)

