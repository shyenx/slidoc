"""CLI smoke tests — ensure all subcommands are wired and --help works."""
import subprocess
import sys


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "slidoc.cli", *args],
        capture_output=True, text=True,
    )


def test_root_help():
    r = _run("--help")
    assert r.returncode == 0
    out = r.stdout
    for sub in ["inspect", "frames", "transcribe", "align", "check", "prompt", "run"]:
        assert sub in out, f"missing sub-command: {sub}"


def test_version():
    r = _run("--version")
    assert r.returncode == 0
    assert "slidoc" in r.stdout


def test_each_sub_help():
    for sub in ["inspect", "frames", "transcribe", "align", "check", "prompt", "run"]:
        r = _run(sub, "--help")
        assert r.returncode == 0, f"{sub} --help failed"
        assert sub in r.stdout or "usage:" in r.stdout
