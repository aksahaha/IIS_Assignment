"""Pure state engine. All inference is deterministic simulation over labelled fixtures."""
import copy
import json
import re
from pathlib import Path

CHOICES = ("Select", "Exclude", "Uncertain")


def rank_sources(sources, query):
    """Stable token overlap over authored fixture text, never live retrieval."""
    tokens = set(re.findall(r"\w+", query.casefold()))

    def score(source):
        text = " ".join(source[field] for field in
                        ("title", "publisher", "population", "design", "relevance", "passage", "document"))
        return len(tokens.intersection(re.findall(r"\w+", text.casefold())))

    return sorted(sources, key=score, reverse=True)


def question_topic(question):
    """Recognise only the small fictional topics the prototype can demonstrate."""
    tokens = set(re.findall(r"\w+", question.casefold()))
    if tokens.intersection({"wearable", "wearables"}) or (
            "sleep" in tokens and tokens.intersection({"score", "scores"})):
        return "insufficient"
    if tokens.intersection({"diary", "diaries", "journal", "journals", "journaling", "journalling"}):
        return "diary"
    if tokens.intersection({"calm", "calmness", "relax", "relaxation", "relaxing", "winddown"}) or {"wind", "down"}.issubset(tokens):
        return "conflict"
    if "sleep" in tokens and tokens.intersection({"schoolchild", "schoolchildren"}):
        return "insufficient"
    return None


def load_cases(path=None):
    cases = json.loads(Path(path or Path(__file__).with_name("fixtures.json")).read_text(encoding="utf-8"))
    for case in cases.values():
        if not isinstance(case,dict) or not isinstance(case.get("sources"),list) or not isinstance(case.get("question"),str) or not isinstance(case.get("title"),str):
            raise ValueError("Malformed case")
        required = {"id", "title", "publisher", "date", "population", "design", "relevance", "kind", "direction", "passage", "finding", "limit", "document"}
        additional = case.get("additional_sources", [])
        if not isinstance(additional, list):
            raise ValueError("Additional sources must be a list")
        catalog = case["sources"] + additional
        for source in catalog:
            if not isinstance(source,dict) or not required.issubset(source) or any(not isinstance(source[k],str) for k in required):
                raise ValueError("Missing or invalid source fields")
            if source["direction"] not in ("positive", "negative", "none"):
                raise ValueError("Unknown fixture direction")
        ids = [s["id"] for s in catalog]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate source IDs")
        for source in catalog:
            if source["kind"] not in ("relevant", "irrelevant", "outdated"):
                raise ValueError("Unknown fixture category")
    return cases

class Session:
    def __init__(self, cases=None, case_id="diary"):
        self.cases = copy.deepcopy(cases if cases is not None else load_cases())
        self.change_case(case_id)

    @property
    def case(self):
        return self._working_case

    @property
    def available_reference_count(self):
        return len(self._unused_references())

    def _unused_references(self):
        return [source for source in self.cases.get(self.case_id, {}).get("additional_sources", [])
                if source["id"] not in self.decisions]

    @property
    def reviewed(self):
        return sum(v is not None for v in self.decisions.values())

    @property
    def ready(self):
        return bool(self.decisions) and self.reviewed == len(self.decisions) and not self.stopped

    @property
    def last_excluded_source_id(self):
        return next((sid for sid in reversed(self.exclusion_history)
                     if self.decisions.get(sid) == "Exclude"), None)

    @property
    def can_undo_exclusion(self):
        return not self.stopped and self.last_excluded_source_id is not None

    def source(self, source_id):
        return next(s for s in self.case["sources"] if s["id"] == source_id)

    def change_case(self, case_id):
        if case_id not in self.cases:
            raise ValueError("Unknown case")
        self.case_id = case_id
        self._working_case = copy.deepcopy(self.cases[case_id])
        self._working_case.pop("additional_sources", None)
        self.decisions = {s["id"]: None for s in self.case["sources"]}
        self.exclusion_history = []
        self.search_query = ""
        self.question_submitted = False
        self.requested_question = ""
        self.retrieval_message = ""
        self.result = None
        self.stopped = False

    def ask_question(self, question):
        """Start a fresh review based on a typed question and a bounded topic catalogue."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Enter a question before finding references")
        if len(question) > 500:
            raise ValueError("Keep your question to 500 characters or fewer")
        clean_question = question.strip()
        topic = question_topic(clean_question)
        if topic not in self.cases:
            topic = None
        self.change_case(topic or "diary")
        self.question_submitted = True
        self.requested_question = clean_question
        if topic is None:
            self.case_id = "unmatched"
            self._working_case = {"title": "No matching fictional references", "question": clean_question, "sources": []}
            self.decisions = {}
            self.retrieval_message = (
                "No fictional references match this question. Try sleep diaries, Wind-Down calmness, "
                "or wearable sleep scores. This prototype does not search the web."
            )
        else:
            self.case["question"] = clean_question
            self.case["sources"] = rank_sources(self.case["sources"], clean_question)
            self.decisions = {source["id"]: None for source in self.case["sources"]}
            labels = {"diary": "sleep-diary", "conflict": "Wind-Down calmness", "insufficient": "wearable sleep-score"}
            self.retrieval_message = (
                f"Found {len(self.case['sources'])} related fictional {labels[topic]} references. "
                "Topic matching does not establish that they answer your question. Inspect their population, outcome and limitations."
            )

    def restart(self):
        """Submitted-question sessions return to input; legacy cases restart in place."""
        self.change_case("diary" if self.question_submitted else self.case_id)

    def add_references(self, query):
        """Add up to two unused fictional fixtures; this performs no live retrieval."""
        if self.stopped:
            raise ValueError("Restart the case before searching for more references")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Enter a few words to search the fictional reference collection")
        if len(query) > 200:
            raise ValueError("Keep the reference search to 200 characters or fewer")
        if self.question_submitted and self.case_id == "unmatched":
            raise ValueError("Ask a supported question before searching a fictional reference collection")
        available = self._unused_references()
        if not available:
            raise ValueError("All additional fictional references for this case are already in your review")
        clean_query = query.strip()
        # Sorting is stable: tied or unmatched sources retain their authored order.
        added = rank_sources(available, clean_query)[:2]
        self.case["sources"].extend(copy.deepcopy(added))
        self.decisions.update({source["id"]: None for source in added})
        self.search_query = clean_query
        self.result = None
        return [source["id"] for source in added]

    def decide(self, source_id, choice):
        if self.stopped:
            raise ValueError("Restart the case before reviewing")
        if source_id not in self.decisions or choice not in CHOICES:
            raise ValueError("Unknown source or choice")
        if self.decisions[source_id] != choice:
            self.exclusion_history = [sid for sid in self.exclusion_history if sid != source_id]
            if choice == "Exclude":
                self.exclusion_history.append(source_id)
            self.decisions[source_id] = choice
            self.result = None

    def undo_last_exclusion(self):
        """Restore the latest still-excluded source without resetting other decisions."""
        if self.stopped:
            raise ValueError("Restart the case before undoing an exclusion")
        source_id = self.last_excluded_source_id
        if source_id is None:
            raise ValueError("There are no excluded references to restore")
        self.exclusion_history = [sid for sid in self.exclusion_history if sid != source_id]
        self.decisions[source_id] = None
        self.result = None
        return source_id

    def selected(self):
        return [s for s in self.case["sources"] if self.decisions[s["id"]] == "Select"]

    def stop(self):
        self.result = None
        self.stopped = True

    def generate(self):
        if not self.ready:
            raise ValueError("Classify every source before generating")
        selected = self.selected()
        usable = [s for s in selected if s["kind"] == "relevant"]
        input_ids = [s["id"] for s in selected]
        if not usable:
            result = {"status": "insufficient", "heading": "Insufficient evidence - no answer", "message": "The selected fictional passages do not support this question. Review your references, undo an exclusion, or change your question.", "claims": []}
        else:
            conflict = len({s["direction"] for s in usable}) > 1
            result = {"status": "conflict" if conflict else "summary", "heading": "Conflicting evidence - no definitive conclusion" if conflict else "Limited fictional summary", "message": "The selected fictional pilots disagree. No overall effect is inferred." if conflict else "This summary describes only the selected fictional evidence. It establishes no clinical benefit.", "claims": [{"text":s["finding"], "source_id":s["id"], "quote":s["passage"], "limit":s["limit"]} for s in usable]}
        result["input_ids"] = input_ids
        result["input_passages"] = [{"source_id": s["id"], "passage": s["passage"]} for s in selected]
        result["omitted_selected_ids"] = [s["id"] for s in selected if s["kind"] != "relevant"]
        result["simulated"] = True
        self.result = result
        return copy.deepcopy(result)
