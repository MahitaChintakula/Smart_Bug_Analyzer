import re
from pathlib import PurePath

from app.models.log_info import LogInfo


class LogParser:
    """Extract the exception and source location from common log formats."""

    SOURCE_EXTENSIONS = (
        "java",
        "py",
        "js",
        "jsx",
        "ts",
        "tsx",
        "cpp",
        "cc",
        "cxx",
        "c",
        "h",
        "hpp",
        "go",
        "rs",
    )

    def _extract_exception(self, stack_trace: str) -> str:
        patterns = (
            r"(?m)^\s*((?:[A-Za-z_][\w.$]*?(?:Exception|Error)|Exception|Error))\b",
            r"\b(?:raise|throw(?:\s+new)?|caused by:)\s+([A-Za-z_][\w.$]*)",
            r"\b((?:std::)?[\w:]+_[Ee]rror)\b",
            r"\bpanic:\s*([^\n:]+)",
            r"\b(thread\s+['\"][^'\"]+['\"]\s+panicked)\b",
            r"\b(Segmentation fault|abort(?:ed)?|assertion failed)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, stack_trace, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Unknown"

    def _extract_source_location(self, stack_trace: str) -> tuple[str, int]:
        extension_pattern = "|".join(self.SOURCE_EXTENSIONS)
        patterns = (
            # Python traceback: File "/srv/app.py", line 42
            rf"File\s+[\"'](.+?\.({extension_pattern}))[\"']\s*,\s*line\s+(\d+)",
            # JavaScript/TypeScript and Java: at fn (src/file.ts:12:4)
            rf"(?:\bat\s+[^\n(]*\()?((?:[A-Za-z]:)?[^\s()]+\.({extension_pattern})):(\d+)",
            # C/C++, Go, and Rust compiler/runtime diagnostics: src/main.rs:12
            rf"(?m)(?:^|\s)((?:[A-Za-z]:)?[\w./\\-]+\.({extension_pattern})):(\d+)",
        )
        for pattern in patterns:
            match = re.search(pattern, stack_trace, flags=re.IGNORECASE)
            if match:
                file_name = match.group(1)
                line_group = match.groups()[-1]
                return self._file_name(file_name), int(line_group)
        return "Unknown", -1

    @staticmethod
    def _file_name(value: str) -> str:
        """Keep the UI compact while supporting Unix and Windows paths."""
        return PurePath(value.replace("\\", "/")).name or value

    def parse(self, stack_trace: str) -> LogInfo:
        exception = self._extract_exception(stack_trace)
        file_name, line_number = self._extract_source_location(stack_trace)

        return LogInfo(
            exception=exception,
            file=file_name,
            line=line_number,
        )
