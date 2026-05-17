import json
import os
from pathlib import Path

import llm
import pytest

from llm_tools_read_write_file import ListFiles, ReadWriteFile

_tools = ReadWriteFile()
read_file = _tools.read_file
write_file = _tools.write_file

_list_tools = ListFiles()
list_files = _list_tools.list_files


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Run each test from an isolated temp directory acting as CWD."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------


def test_write_file_creates_file(sandbox):
    result = write_file("hello.txt", "world")
    assert "Wrote" in result
    assert (sandbox / "hello.txt").read_text() == "world"


def test_write_file_creates_parent_dirs(sandbox):
    write_file("nested/dir/note.txt", "hi")
    assert (sandbox / "nested" / "dir" / "note.txt").read_text() == "hi"


def test_write_file_overwrites_existing(sandbox):
    (sandbox / "f.txt").write_text("old")
    write_file("f.txt", "new")
    assert (sandbox / "f.txt").read_text() == "new"


def test_write_file_rejects_parent_traversal(sandbox):
    result = write_file("../escape.txt", "nope")
    assert result.startswith("Error:")
    assert not (sandbox.parent / "escape.txt").exists()


def test_write_file_rejects_absolute_path(sandbox, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "x.txt"
    result = write_file(str(outside), "nope")
    assert result.startswith("Error:")
    assert not outside.exists()


def test_write_file_rejects_symlink_escape(sandbox, tmp_path_factory):
    outside_dir = tmp_path_factory.mktemp("outside")
    os.symlink(outside_dir, sandbox / "link")
    result = write_file("link/leak.txt", "nope")
    assert result.startswith("Error:")
    assert not (outside_dir / "leak.txt").exists()


def test_write_file_rejects_directory_target(sandbox):
    (sandbox / "adir").mkdir()
    result = write_file("adir", "nope")
    assert result.startswith("Error:")


def test_write_file_rejects_empty_path(sandbox):
    assert write_file("", "x").startswith("Error:")


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------


def test_read_file_returns_contents(sandbox):
    (sandbox / "a.txt").write_text("contents")
    assert read_file("a.txt") == "contents"


def test_read_file_nested(sandbox):
    p = sandbox / "sub" / "b.txt"
    p.parent.mkdir()
    p.write_text("nested")
    assert read_file("sub/b.txt") == "nested"


def test_read_file_missing(sandbox):
    assert read_file("nope.txt").startswith("Error:")


def test_read_file_rejects_parent_traversal(sandbox, tmp_path_factory):
    secret = sandbox.parent / "secret.txt"
    secret.write_text("top secret")
    try:
        assert read_file("../secret.txt").startswith("Error:")
    finally:
        secret.unlink()


def test_read_file_rejects_absolute_path(sandbox):
    assert read_file("/etc/passwd").startswith("Error:")


def test_read_file_rejects_symlink_escape(sandbox, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "secret.txt"
    outside.write_text("top secret")
    os.symlink(outside, sandbox / "leak")
    assert read_file("leak").startswith("Error:")


def test_read_file_rejects_directory(sandbox):
    (sandbox / "adir").mkdir()
    assert read_file("adir").startswith("Error:")


# ---------------------------------------------------------------------------
# list_files
# ---------------------------------------------------------------------------


def test_list_files_lists_sandbox(sandbox):
    (sandbox / "a.txt").write_text("hi")
    (sandbox / "b.txt").write_text("hey")
    (sandbox / "sub").mkdir()

    result = json.loads(list_files("."))
    names_by_type = {}
    for entry in result:
        names_by_type.setdefault(entry["type"], set()).add(entry["name"])
    assert names_by_type["file"] == {"a.txt", "b.txt"}
    assert names_by_type["directory"] == {"sub"}


def test_list_files_subdirectory(sandbox):
    sub = sandbox / "sub"
    sub.mkdir()
    (sub / "inner.txt").write_text("inside")

    result = json.loads(list_files("sub"))
    assert len(result) == 1
    assert result[0]["name"] == "inner.txt"
    assert result[0]["type"] == "file"


def test_list_files_excludes_dotfiles(sandbox):
    (sandbox / "visible.txt").write_text("yep")
    (sandbox / ".hidden").write_text("nope")

    result = json.loads(list_files("."))
    names = {e["name"] for e in result}
    assert "visible.txt" in names
    assert ".hidden" not in names


def test_list_files_includes_file_sizes(sandbox):
    (sandbox / "sized.txt").write_text("1234567890")

    result = json.loads(list_files("."))
    assert len(result) == 1
    assert result[0]["name"] == "sized.txt"
    assert result[0]["type"] == "file"
    assert result[0]["size"] == 10


def test_list_files_missing(sandbox):
    assert list_files("nope").startswith("Error:")


def test_list_files_rejects_parent_traversal(sandbox):
    assert list_files("../").startswith("Error:")


def test_list_files_rejects_absolute_path(sandbox):
    assert list_files("/etc").startswith("Error:")


def test_list_files_rejects_symlink_escape(sandbox, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    os.symlink(outside, sandbox / "leak")
    assert list_files("leak").startswith("Error:")


def test_list_files_rejects_file_not_directory(sandbox):
    (sandbox / "afile.txt").write_text("data")
    assert list_files("afile.txt").startswith("Error:")


def test_list_files_rejects_empty_path(sandbox):
    assert list_files("").startswith("Error:")


# ---------------------------------------------------------------------------
# LLM tool registration round-trip
# ---------------------------------------------------------------------------


def test_tools_via_echo_model_list(sandbox):
    """Pass ListFiles toolbox — verify list_files round-trip."""
    model = llm.get_model("echo")
    chain_response = model.chain(
        json.dumps(
            {
                "tool_calls": [
                    {
                        "name": "ListFiles_list_files",
                        "arguments": {"path": "."},
                    },
                ]
            }
        ),
        tools=[ListFiles()],
    )
    responses = list(chain_response.responses())
    tool_results = json.loads(responses[-1].text())["tool_results"]
    result = json.loads(tool_results[0]["output"])
    assert isinstance(result, list)


def test_tools_via_echo_model_toolbox(sandbox):
    """Pass the toolbox class so a single tools=[ReadWriteFile()] picks up both."""
    model = llm.get_model("echo")
    chain_response = model.chain(
        json.dumps(
            {
                "tool_calls": [
                    {
                        "name": "ReadWriteFile_write_file",
                        "arguments": {"path": "greeting.txt", "content": "hi"},
                    },
                    {
                        "name": "ReadWriteFile_read_file",
                        "arguments": {"path": "greeting.txt"},
                    },
                ]
            }
        ),
        tools=[ReadWriteFile()],
    )
    responses = list(chain_response.responses())
    tool_results = json.loads(responses[-1].text())["tool_results"]
    by_name = {r["name"]: r["output"] for r in tool_results}
    assert "Wrote" in by_name["ReadWriteFile_write_file"]
    assert by_name["ReadWriteFile_read_file"] == "hi"
