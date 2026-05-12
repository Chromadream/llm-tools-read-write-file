# llm-tools-read-write-file

[![Release](https://img.shields.io/github/v/release/Chromadream/llm-tools-read-write-file?label=release)](https://github.com/Chromadream/llm-tools-read-write-file/releases)
[![Changelog](https://img.shields.io/github/v/release/Chromadream/llm-tools-read-write-file?include_prereleases&label=changelog)](https://github.com/Chromadream/llm-tools-read-write-file/releases)
[![Tests](https://github.com/Chromadream/llm-tools-read-write-file/actions/workflows/test.yml/badge.svg)](https://github.com/Chromadream/llm-tools-read-write-file/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/Chromadream/llm-tools-read-write-file/blob/main/LICENSE)

A tool plugin for [LLM](https://llm.datasette.io/) that allows you to read and write files inside the current working directory.

The plugin ships an [`llm.Toolbox`](https://llm.datasette.io/en/stable/python-api.html#toolboxes) called `ReadWriteFile` that exposes two methods:

- `read_file(path)` — read a UTF-8 text file relative to the CWD.
- `write_file(path, content)` — write a UTF-8 text file relative to the CWD, creating parent directories as needed.

Both tools refuse to operate outside of the current working directory: absolute paths, `..` traversal, and symlinks pointing outside the CWD are rejected with an `Error:` message.

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/) directly from GitHub. Latest from `main`:
```bash
llm install git+https://github.com/Chromadream/llm-tools-read-write-file
```

Or pin to a specific release tag (recommended for reproducible setups — replace `v0.1.0` with the tag you want from the [releases page](https://github.com/Chromadream/llm-tools-read-write-file/releases)):
```bash
llm install git+https://github.com/Chromadream/llm-tools-read-write-file@v0.1.0
```

## Usage

To use this with the [LLM command-line tool](https://llm.datasette.io/en/stable/usage.html), pass the toolbox name once to expose both tools in a single invocation:

```bash
llm --tool ReadWriteFile "Read notes.txt and append a summary to summary.txt" --tools-debug
```

Individual tools are also registered, if you prefer to enable only one:

```bash
llm --tool read_file "Summarize notes.txt"
```

With the [LLM Python API](https://llm.datasette.io/en/stable/python-api.html):

```python
import llm
from llm_tools_read_write_file import ReadWriteFile

model = llm.get_model("gpt-4.1-mini")

result = model.chain(
    "Read notes.txt and append a summary to summary.txt",
    tools=[ReadWriteFile()],
).text()
```

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd llm-tools-read-write-file
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
llm install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
