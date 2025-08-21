import sys
from pathlib import Path


MAX_LINES = (
    int(Path.cwd().joinpath(".max_file_lines").read_text().strip())
    if Path(".max_file_lines").exists()
    else 600
)


def load_ignores() -> set[str]:
    p = Path(".lengthcheckignore")
    if not p.exists():
        return set()
    patterns: set[str] = set()
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        patterns.add(s)
    return patterns


def is_ignored(path: Path, patterns: set[str]) -> bool:
    from fnmatch import fnmatch

    s = str(path)
    return any(fnmatch(s, pat) for pat in patterns)


def count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main(argv):
    if len(argv) == 0:
        return 0
    violations = []
    ignores = load_ignores()
    for name in argv:
        p = Path(name)
        # Only enforce for Python source files
        if p.suffix != ".py":
            continue
        if is_ignored(p, ignores):
            continue
        lines = count_lines(p)
        if lines > MAX_LINES:
            violations.append((str(p), lines))

    if violations:
        print("File length check failed (max {} lines):".format(MAX_LINES))
        for path, lines in violations:
            print(f" - {path}: {lines} lines")
        print("\nPlease split large modules into smaller ones (SRP).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
