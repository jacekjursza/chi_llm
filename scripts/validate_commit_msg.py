import re
import sys
from pathlib import Path


HEADER_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)"
    r"(\([a-zA-Z0-9_\-]+\))?(\!)?: .{1,72}$"
)


def is_merge_or_revert(header: str) -> bool:
    return header.startswith("Merge ") or header.startswith("Revert ")


def validate_commit_message(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.strip().splitlines()
    if not lines:
        print("Empty commit message.")
        return 1

    header = lines[0]
    if not (HEADER_RE.match(header) or is_merge_or_revert(header)):
        print("Commit header must follow Conventional Commits and be <=72 chars.")
        print(
            "Examples: feat(cli): add modular subcommands | "
            "fix(core): handle None model"
        )
        return 1

    # Require Card-Id and Refs footers unless this is a merge or revert
    if not is_merge_or_revert(header):
        has_card = any(line.startswith("Card-Id:") for line in lines)
        has_refs = any(line.startswith("Refs:") for line in lines)
        if not (has_card and has_refs):
            print("Commit message must include Card-Id and Refs footers.")
            print(
                "Add lines, e.g.:\nCard-Id: 001\nRefs: "
                "docs/kanban/todo/001-cli-refactor-modularization.md"
            )
            return 1
    return 0


def main(argv) -> int:
    if not argv:
        print("Usage: validate_commit_msg.py <COMMIT_MSG_FILE>")
        return 1
    return validate_commit_message(Path(argv[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
