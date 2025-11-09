from setuptools import find_packages, setup
from typing import List

def get_req(file) -> List[str]:
    with open(file) as f:
        lines = f.readlines()
    # remove comments, blank lines, and the '-e .' line to avoid recursion
    req = [r.strip() for r in lines if r.strip() and not r.startswith('#') and r.strip() != '-e .']
    return req

setup(
    name='netw0rk_security',
    version='0.0.1',
    author='suvankar payra',
    author_email='suvankarpayra12@gmail.com',
    packages=find_packages(),
    install_requires=get_req('req.txt')
)