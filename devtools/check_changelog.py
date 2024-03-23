"""
Certify the developer has input all requirements for PR.

Situations tested:

* additions are reported in CHANGELOG.rst
"""
from pathlib import Path


changelog = Path('docs', 'CHANGELOG.rst')

with open(changelog, 'r') as fin:
    for line in fin:
        if line.startswith('v'):
            print(
                'Please add a summary of your additions to docs/CHANGELOG.rst. '
                'As described in: https://grafanarmadillo.readthedocs.io'
                '/en/latest/contributing.html#update-changelog.'
            )
            exit(1)
        elif line.startswith('*'):
            exit(0)
