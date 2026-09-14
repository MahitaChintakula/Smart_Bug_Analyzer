import json
import re
from pathlib import Path

from app.models.bug import Bug


class KnowledgeBase:
    """
    Handles loading and validating historical bug reports.
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load_bugs(self) -> list[Bug]:
        """
        Load bugs from the JSON knowledge base.

        Returns:
            list[Bug]: List of validated Bug objects.
        """

        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        bugs = [Bug(**bug) for bug in data]

        return bugs

    def next_bug_id(self) -> str:
        """Return the next available sequential BUG identifier."""
        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        highest_id = 0

        for bug in data:
            match = re.fullmatch(r"BUG-(\d+)", str(bug.get("bug_id", "")))
            if match:
                highest_id = max(highest_id, int(match.group(1)))

        return f"BUG-{highest_id + 1:03d}"

    def append_bug(self, bug: Bug) -> bool:
        """
        Persist a bug unless its BUG identifier is already present.

        Returns True when a new entry is written and False when the entry
        already exists.
        """
        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if any(item.get("bug_id") == bug.bug_id for item in data):
            return False

        if hasattr(bug, "model_dump"):
            serialized_bug = bug.model_dump()
        else:  # pragma: no cover - compatibility with Pydantic v1
            serialized_bug = bug.dict()

        data.append(serialized_bug)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Replace the file atomically so a request cannot leave invalid JSON
        # if the process is interrupted during the write.
        temporary_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.file_path)

        return True
