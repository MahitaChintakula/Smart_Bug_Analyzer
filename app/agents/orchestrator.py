import logging
from pathlib import Path

from app.models.bug import Bug


logger = logging.getLogger(__name__)


class BugOrchestrator:

    NEW_BUG_SIMILARITY_THRESHOLD = 0.75

    def __init__(
        self,
        parser,
        duplicate_agent,
        root_cause_agent,
        triage_agent,
        remediation_agent,
        historical_bugs,
        knowledge_base=None,
        rag_service=None,
        new_bug_similarity_threshold=NEW_BUG_SIMILARITY_THRESHOLD,
    ):
        self.parser = parser
        self.duplicate_agent = duplicate_agent
        self.root_cause_agent = root_cause_agent
        self.triage_agent = triage_agent
        self.remediation_agent = remediation_agent
        self.historical_bugs = historical_bugs
        self.knowledge_base = knowledge_base
        self.rag_service = rag_service
        self.new_bug_similarity_threshold = new_bug_similarity_threshold

    def analyze(self, bug_report):

        # ------------------------------------------------
        # STEP 1: Parse the log
        # ------------------------------------------------

        log_info = self.parser.parse(bug_report)

        # ------------------------------------------------
        # STEP 2: Find similar historical bugs
        # ------------------------------------------------

        similar_bugs = self.duplicate_agent.analyze(bug_report)

        # ------------------------------------------------
        # STEP 3: Get complete historical bug objects
        # ------------------------------------------------

        similar_ids = {bug.bug_id for bug in similar_bugs}

        historical_context = [
            bug for bug in self.historical_bugs if bug.bug_id in similar_ids
        ]

        # ------------------------------------------------
        # STEP 4: Root Cause Analysis
        # ------------------------------------------------

        root_cause_result = self.root_cause_agent.analyze(
            bug_report, historical_context
        )

        # ------------------------------------------------
        # STEP 5: Triage
        # ------------------------------------------------

        triage_result = self.triage_agent.analyze(
            bug_report, root_cause_result.root_cause
        )

        # ------------------------------------------------
        # STEP 6: Remediation
        # ------------------------------------------------

        remediation_result = self.remediation_agent.analyze(
            bug_report, root_cause_result.root_cause, historical_context
        )

        # Persist genuinely new bugs after the analysis fields are available.
        # The original top-three search results are returned unchanged.
        self._persist_new_bug(
            bug_report=bug_report,
            log_info=log_info,
            similar_bugs=similar_bugs,
            root_cause_result=root_cause_result,
            triage_result=triage_result,
            remediation_result=remediation_result,
        )

        # ------------------------------------------------
        # STEP 7: Return complete analysis
        # ------------------------------------------------

        return {
            "bug_report": bug_report,
            "log_info": log_info,
            "similar_bugs": similar_bugs,
            "root_cause": root_cause_result,
            "triage": triage_result,
            "remediation": remediation_result,
        }

    def _persist_new_bug(
        self,
        bug_report,
        log_info,
        similar_bugs,
        root_cause_result,
        triage_result,
        remediation_result,
    ):
        """Save and index the report when no historical match is strong enough."""
        if self.knowledge_base is None or self.rag_service is None:
            return

        highest_similarity = max(
            (float(getattr(match, "similarity_score", 0.0)) for match in similar_bugs),
            default=0.0,
        )

        if highest_similarity >= self.new_bug_similarity_threshold:
            logger.info(
                "[RAG] Existing historical bug matched (similarity %.2f); "
                "skipping knowledge-base insertion",
                highest_similarity,
            )
            return

        new_bug = self._build_bug_entry(
            bug_report=bug_report,
            log_info=log_info,
            root_cause_result=root_cause_result,
            triage_result=triage_result,
            remediation_result=remediation_result,
        )

        if not self.knowledge_base.append_bug(new_bug):
            logger.info(
                "[RAG] Knowledge-base entry %s already exists; skipping insertion",
                new_bug.bug_id,
            )
            return

        # Update the same in-memory FAISS service used by this request. This
        # makes the entry searchable immediately without restarting the app.
        self.rag_service.add_bug(new_bug)

        # RAGService normally owns this shared list. Keep the fallback safe for
        # compatible test doubles or alternative service implementations.
        if not any(bug.bug_id == new_bug.bug_id for bug in self.historical_bugs):
            self.historical_bugs.append(new_bug)

        logger.info(
            "[RAG] Added new historical bug %s and updated FAISS index",
            new_bug.bug_id,
        )

    def _build_bug_entry(
        self,
        bug_report,
        log_info,
        root_cause_result,
        triage_result,
        remediation_result,
    ) -> Bug:
        exception = self._value_or_unknown(getattr(log_info, "exception", None))
        source_file = self._value_or_unknown(getattr(log_info, "file", None))
        module = self._module_from_file(source_file)
        description = bug_report.strip()

        recommended_fix = self._value_or_unknown(
            getattr(remediation_result, "recommended_fix", None)
        )
        root_cause = self._value_or_unknown(
            getattr(root_cause_result, "root_cause", None)
        )

        return Bug(
            bug_id=self.knowledge_base.next_bug_id(),
            title=self._title(exception, source_file, description),
            description=description,
            severity=self._value_or_unknown(getattr(triage_result, "severity", None)),
            priority=self._value_or_unknown(getattr(triage_result, "priority", None)),
            module=module,
            exception=exception,
            stack_trace=description,
            root_cause=root_cause,
            resolution=recommended_fix,
            tags=self._tags(description, exception, module),
        )

    @staticmethod
    def _value_or_unknown(value):
        value = str(value or "").strip()
        return value if value else "Unknown"

    @staticmethod
    def _module_from_file(source_file):
        if source_file == "Unknown":
            return "Unknown"

        module = Path(source_file).stem.strip()
        return module or "Unknown"

    @staticmethod
    def _title(exception, source_file, description):
        if exception != "Unknown" and source_file != "Unknown":
            return f"{exception} in {source_file}"

        first_line = next(
            (line.strip() for line in description.splitlines() if line.strip()),
            "New bug report",
        )
        return first_line[:120]

    @staticmethod
    def _tags(description, exception, module):
        tags = []

        for value in (exception, module):
            if value != "Unknown" and value.lower() not in {
                tag.lower() for tag in tags
            }:
                tags.append(value)

        searchable_text = description.lower()
        keywords = (
            "authentication",
            "authorization",
            "cache",
            "database",
            "deployment",
            "memory",
            "network",
            "payment",
            "performance",
            "timeout",
            "validation",
        )

        for keyword in keywords:
            if keyword in searchable_text and keyword not in {
                tag.lower() for tag in tags
            }:
                tags.append(keyword)

        return tags or ["new bug"]
