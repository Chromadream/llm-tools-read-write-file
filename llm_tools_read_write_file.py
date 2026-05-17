from pathlib import Path

import llm


def _resolve_within_cwd(path: str) -> Path:
    """Resolve *path* and require the result to live inside the current working directory.

    Resolution follows symlinks and collapses ``..`` segments, so neither absolute
    paths, parent-directory traversal, nor symlinks pointing outside the CWD can
    escape the sandbox.
    """
    if not isinstance(path, str) or path == "":
        raise ValueError("path must be a non-empty string")

    cwd = Path.cwd().resolve()
    candidate = (cwd / path).resolve()

    if candidate != cwd and cwd not in candidate.parents:
        raise ValueError(
            f"refusing to access {path!r}: path escapes the current working directory"
        )
    return candidate


import json


class ReadWriteFile(llm.Toolbox):
    """File read/write tools sandboxed to the current working directory."""

    name: str = "Read/Write File"

    def read_file(self, path: str) -> str:
        """Read a UTF-8 text file located inside the current working directory.

        Args:
            path: Path to the file, interpreted relative to the current working
                directory. Absolute paths, ``..`` traversal, and symlinks that
                point outside the working directory are rejected.
        """
        try:
            target = _resolve_within_cwd(path)
        except ValueError as exc:
            return f"Error: {exc}"

        if not target.exists():
            return f"Error: {path!r} does not exist"
        if target.is_dir():
            return f"Error: {path!r} is a directory, not a file"

        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"Error: {path!r} is not a valid UTF-8 text file"
        except OSError as exc:
            return f"Error: could not read {path!r}: {exc}"

    def write_file(self, path: str, content: str) -> str:
        """Write *content* to a UTF-8 text file inside the current working directory.

        Creates parent directories as needed.

        Args:
            path: Path to the file, interpreted relative to the current working
                directory. Absolute paths, ``..`` traversal, and symlinks that
                point outside the working directory are rejected.
            content: Text to write to the file.
        """
        try:
            target = _resolve_within_cwd(path)
        except ValueError as exc:
            return f"Error: {exc}"

        if target.is_dir():
            return f"Error: {path!r} is an existing directory"

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            return f"Error: could not write {path!r}: {exc}"

        return f"Wrote {len(content)} characters to {path}"


class ListFiles(ReadWriteFile):
    """Directory listing + file read/write tools sandboxed to CWD."""

    name: str = "List Files"

    def list_files(self, path: str = ".") -> str:
        """List files and directories inside a directory in the CWD.

        Returns a JSON array of objects with ``name``, ``type``, and ``size``
        (files only).  Hidden / dot-files are excluded.

        Args:
            path: Path to the directory, interpreted relative to the CWD.
                Absolute paths, ``..`` traversal, and symlinks that point
                outside the CWD are rejected.
        """
        try:
            target = _resolve_within_cwd(path)
        except ValueError as exc:
            return f"Error: {exc}"

        if not target.exists():
            return f"Error: {path!r} does not exist"
        if not target.is_dir():
            return f"Error: {path!r} is not a directory"

        entries = []
        for child in sorted(target.iterdir()):
            if child.name.startswith("."):
                continue
            entry = {"name": child.name, "type": "directory" if child.is_dir() else "file"}
            if not child.is_dir():
                entry["size"] = child.stat().st_size
            entries.append(entry)
        return json.dumps(entries)


@llm.hookimpl
def register_tools(register):
    rw = ReadWriteFile()
    register(rw.read_file, "read_file")
    register(rw.write_file, "write_file")
    register(ReadWriteFile, "ReadWriteFile")

    lf = ListFiles()
    register(lf.list_files, "list_files")
    register(ListFiles, "ListFiles")
