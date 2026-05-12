# TODO

## Re-enable PyPI publishing

The "Publish to PyPI" step in `.github/workflows/publish.yml` is commented out because access to the PyPI account is currently being recovered.

Once access is restored:

1. Uncomment the `Publish to PyPI` step in `.github/workflows/publish.yml`.
2. Verify the Trusted Publisher entry on PyPI still points to workflow file `publish.yml` and environment `release`.
3. Restore the PyPI-based install instruction in `README.md` (`llm install llm-tools-read-write-file`) if desired.
4. Swap the GitHub Release version badge at the top of `README.md` back to the PyPI version badge:
   `[![PyPI](https://img.shields.io/pypi/v/llm-tools-read-write-file.svg)](https://pypi.org/project/llm-tools-read-write-file/)`
5. Remove this TODO entry.

Until then, `python-semantic-release` will still bump the version, tag, and create a GitHub Release with built artifacts attached — only the PyPI upload is skipped.
