import re
import sys
from pathlib import Path


# Relaxed Conventional Commit header:
# <type>(<optional-scope>)<!>: <desc>
# - allow any non-empty description (length warning printed, not fatal)
# - allow any characters inside scope except closing paren
HEADER_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)"
    r"(\([^\)]+\))?(\!)?:\s+.+$"
)


def is_merge_or_revert(header: str) -> bool:
    return header.startswith("Merge ") or header.startswith("Revert ")


def validate_commit_message(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    raw_lines = text.splitlines()
    # Drop commented lines (git template) for validation purposes
    lines = [ln.rstrip() for ln in raw_lines if not ln.lstrip().startswith("#")]
    # Find first non-empty line as header
    header = next((ln for ln in lines if ln.strip() != ""), "")
    if not header:
        print("Empty commit message.")
        return 1
    if not (HEADER_RE.match(header) or is_merge_or_revert(header)):
        print("Commit header must follow Conventional Commits and be <=72 chars.")
        print(
            "Examples: feat(cli): add modular subcommands | "
            "fix(core): handle None model"
        )
        return 1

    # Warn (not fail) if header appears too long (> 72 chars)
    if len(header) > 72 and not is_merge_or_revert(header):
        print("Warning: commit header exceeds 72 characters.")

    # Require Card-Id and Refs footers unless this is a merge or revert
    if not is_merge_or_revert(header):
        # tolerate indentation and varied placement; ignore commented lines
        text_no_comments = "\n".join(lines)
        has_card = "Card-Id:" in text_no_comments
        has_refs = "Refs:" in text_no_comments
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
