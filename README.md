# Reference First

README prose word count: 826 (whitespace-separated headings and prose; fenced code and setup commands excluded).

Package snapshot: rf-question-input-2026-11-24.

An IIS Assignment 2 prototype: enter a health-information question, inspect the references returned for it, and choose which passages may support a summary.

## Project status

Implemented: question input, topic-based reference retrieval, full-source inspection, Select / Exclude / Not sure decisions, compact selected rows, hidden exclusions, additional-reference searches, review progress, generation gating, cited summaries and reset. References appear only after a question is submitted. Changing the question clears the old review and output; changing evidence clears the summary.

Simulated: retrieval, documents, publishers, relevance labels and summary generation. The local fictional catalogue covers sleep diaries, relaxation/calmness and wearable sleep scores. Unsupported topics return no references. Selection permits use as input; it does not establish correctness or clinical benefit.

Unfinished: live search, a validated AI model, user evaluation, the updated assignment report and public GitHub publication. No real patient data or clinical evaluation is used. The runtime model/provider remains undecided.

## Technology stack

- Python 3.10 or newer: standard-library HTTP server, isolated browser sessions and review/summary engine.
- HTML, CSS and vanilla JavaScript: question form, reference cards, source inspector and summary interface.
- JSON: authored fictional documents and retrieval fixtures.
- unittest: engine and HTTP integration checks.
- OpenAI Codex: development and documentation assistance; it is not a runtime model in this prototype.

No third-party packages, accounts or API keys are needed. No keys or credentials are included.

## Running or inspecting the work

Extract the entire ZIP before launching. On Windows, double-click **open_prototype.cmd** and keep its terminal open. The browser opens at http://127.0.0.1:8765. Press Ctrl+C in that terminal to stop. The launcher can also use Python bundled with Codex if ordinary Python is unavailable.

Alternatively, open a terminal in the extracted project folder:

```sh
python serve_prototype.py
```

Use python3 on systems where that is the Python command. A modern browser and Python 3.10 or newer are required. If the default port is occupied:

```sh
python serve_prototype.py --port 8766
```

Question and review state remain in memory while the server runs. Inspect engine.py for decision and synthesis rules, serve_prototype.py for the local API, fixtures.json for fictional sources, web/ for the interface and tests/ for checks.

## Replay the interaction

1. Enter “Can a sleep diary help adults describe their sleep routine?” and choose **Find references**.
2. Read source D1 and select it. Exclude D2 and choose Not sure for D3. Selected sources collapse into rows; click to reopen them. Excluded sources disappear and never supply summary input.
3. Optionally choose **Add more references**, search and review the new sources. Existing choices remain saved; every new source requires a decision.
4. Choose **Generate summary**, then open its citations to inspect the exact original passages.
5. **Change question** begins another search. **Start again** clears the question and review; resubmitting retrieves the original sources again.

A calmness question retrieves a different collection. An unrelated question returns no matches rather than unrelated evidence.

## Development record and verification

- Began with the Assignment 1 reference-first proposal. Replaced live retrieval and model calls with fictional fixtures so the interaction could be replayed without keys or invented claims about real studies.
- Separated review decisions from the interface. Checks verify that only selected passages supply findings, citations match their sources and changed evidence invalidates output.
- Added compact selected rows and removed excluded cards following interface feedback. Browser walkthroughs checked reopening, exclusion, preserved selections and extra-reference searches.
- Removed scenario tabs and extra panels after feedback that the interface was too complicated. Added question entry so retrieval follows the user's input. Tightened topic matching so an unrelated schoolchildren/homework question does not return wearable sources.
- Verification: **52 automated tests passed**, covering question validation, routing, no matches, review gating, selected-input boundaries, citations, reset, search exhaustion and session isolation. Browser walkthroughs checked the full question-to-summary flow, different questions, refresh, no-match recovery and phone layout. No participant study is claimed.

```sh
python -m unittest discover -s tests -v
```

The initial local project build is commit 5cc3989. Current browser changes are uncommitted and are not identified by that earlier commit. This download is identified by VERSION.txt and MANIFEST.sha256. Public repository/README URLs and the final submitted commit or release must be recorded when publication is completed.

## AI assistance

OpenAI Codex helped implement the Python engine, browser interface, tests and documentation. Suggestions were changed to restrict findings to selected fictional passages, clear stale summaries and reject unrelated topic matches. Those changes were checked through regression/API tests. Interface and README drafts were revised following the user's feedback, then checked against the assignment requirements and browser behaviour. A full prompt/chat log is not included.

## Additional files

START_HERE.txt contains quick launch instructions. VERSION.txt identifies this package snapshot; MANIFEST.sha256 records each included file's checksum. The ZIP includes source, fixtures, tests and tools/package_prototype.py for rebuilding it.

The assignment report, earlier report drafts, course materials, Git history, caches and credentials are outside this package. This ZIP is a portable prototype copy; the assignment report and public repository links are separate deliverables.
