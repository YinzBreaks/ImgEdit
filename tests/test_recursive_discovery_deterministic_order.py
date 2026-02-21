from pathlib import Path

from src.cli import _discover_inputs


def test_recursive_discovery_deterministic_order(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    (input_dir / "subB").mkdir(parents=True, exist_ok=True)
    (input_dir / "subA").mkdir(parents=True, exist_ok=True)

    (input_dir / "subB" / "IMG_0001.jpg").write_bytes(b"x")
    (input_dir / "subA" / "z.png").write_bytes(b"x")
    (input_dir / "subA" / "a.png").write_bytes(b"x")
    (input_dir / "root.png").write_bytes(b"x")
    (input_dir / "skip.txt").write_text("skip", encoding="utf-8")

    discovered = _discover_inputs(
        input_dir=input_dir,
        glob_pattern="*.png",
        recursive=True,
        include_ext_csv="png,jpg,jpeg",
        max_files=None,
    )

    relpaths = [p.relative_to(input_dir).as_posix() for p in discovered]
    assert relpaths == [
        "root.png",
        "subA/a.png",
        "subA/z.png",
        "subB/IMG_0001.jpg",
    ]
