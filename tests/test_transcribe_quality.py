"""Tests for the SRT quality gate (no whisper required)."""
from slidoc.transcribe import quality_report


def _write_srt(path, blocks):
    """Compose an SRT file from (start, end, text) tuples."""
    content = []
    for i, (start, end, text) in enumerate(blocks, 1):
        content.append(f"{i}\n{start} --> {end}\n{text}\n")
    path.write_text("\n".join(content))


def test_quality_report_unique(tmp_path):
    srt = tmp_path / "good.srt"
    _write_srt(srt, [
        ("00:00:00,000", "00:00:02,000", "line one"),
        ("00:00:02,000", "00:00:04,000", "line two"),
        ("00:00:04,000", "00:00:06,000", "line three"),
        ("00:00:06,000", "00:00:08,000", "line four"),
    ])
    qr = quality_report(srt)
    assert qr["total"] == 4
    assert qr["unique"] == 4
    assert qr["ratio"] == 1.0


def test_quality_report_hallucination(tmp_path):
    srt = tmp_path / "bad.srt"
    blocks = [("00:00:00,000", "00:00:02,000", "good opener")]
    # 9 repeats of the same garbage line
    for i in range(9):
        blocks.append((f"00:00:{2+i*2:02d},000", f"00:00:{4+i*2:02d},000", "looped phrase"))
    _write_srt(srt, blocks)
    qr = quality_report(srt)
    assert qr["total"] == 10
    assert qr["unique"] == 2
    assert qr["ratio"] == 0.2
    # top should be the repeated phrase
    assert qr["top_repeated"][0][0] == "looped phrase"
    assert qr["top_repeated"][0][1] == 9


def test_quality_report_empty(tmp_path):
    srt = tmp_path / "empty.srt"
    srt.write_text("")
    qr = quality_report(srt)
    assert qr["total"] == 0
    assert qr["ratio"] == 0.0
