# Reference First

README prose word count: 564 (whitespace-separated headings and prose; fenced code/setup blocks excluded).

An IIS Assignment 2 prototype: enter a health-information question, inspect fictional references and choose which passages may support a simulated summary.

## Project status

Implemented: question entry, topic routing, source inspection, Select / Exclude / Not sure decisions, compact selected rows, hidden exclusions, exclusion undo, additional-reference search, review gating, citations and reset. New or restored sources require decisions; changed evidence clears old output.

Simulated: retrieval, publications, eligibility judgements, disagreement detection and summaries. Three fictional collections cover sleep diaries, calmness and wearable sleep scores. Unsupported questions return no references. Selection permits input use, not medical approval.

Planned: live retrieval, a validated model and user evaluation. The runtime model/provider remains undecided. No clinical or usability improvement is claimed.

## Technology and setup

Python 3.10+ supplies the standard-library server, session state, JSON fixtures and unittest checks. HTML, CSS and vanilla JavaScript supply the browser interface. OpenAI Codex assisted development; it is not a runtime model. No third-party packages, accounts or API keys are needed.

Extract the ZIP before launching. On Windows, double-click **open_prototype.cmd** and keep its terminal open. The browser opens at http://127.0.0.1:8765. Press Ctrl+C in the terminal to stop. Alternatively:

```sh
python serve_prototype.py
```

Use python3 where appropriate. The launcher also checks for Python bundled with Codex. If the port is occupied:

```sh
python serve_prototype.py --port 8766
```

Question and review state remain in memory while the server runs. Inspect [engine.py](engine.py), [the local API](serve_prototype.py), [fixtures](fixtures.json), [browser source](web/) and [tests](tests/). The legacy [desktop interface](app.py) additionally requires Tkinter.

## Replay the interaction

1. Enter “Can a sleep diary help adults describe their sleep routine?” and choose **Find references**.
2. Read D1 and select it; exclude D2 and choose Not sure for D3. Selected rows reopen on click. Exclusions disappear. **Undo last exclusion** restores the newest exclusion as unreviewed while preserving other choices; review it before generating again.
3. Optionally add references, then review the additions. Generate the summary and open its citations. Change question begins another review.

Calmness questions retrieve another collection. Unrelated questions return no matches. Keyword routing does not validate every population or outcome.

## Development record and verification

[Development evidence E1-E6](docs/development_evidence.md) links each major change to its requester basis, reason, code, specific checks and limitations. It covers the simulation boundary, compact rows, exclusion recovery, incremental search, simplification and question-driven retrieval. These are grouped stages and project feedback, not participant research.

The [recorded test run](docs/verification_results.txt) contains the command, date and actual output: **62 tests passed**, including selected-input boundaries, citations, routing, undo, resets and session isolation. [Current screenshots](docs/screenshots/) supplement state tests with visible interaction evidence. No participant study is claimed.

```sh
python -m unittest discover -s tests -v
```

Repository URL provided for this project: [IIS Assignment](https://github.com/aksahaha/IIS_Assignment). README: [Project README](https://github.com/aksahaha/IIS_Assignment#readme). Local implementation and verification evidence are linked above.

## AI assistance

OpenAI Codex helped implement code, tests, documentation and figures. Suggestions were changed to restrict findings to selected fictional passages, invalidate stale summaries and reject unrelated schoolchildren/homework matches. Regression/API tests checked those changes. Requester feedback drove interface revisions; browser walkthroughs checked their behaviour. Report assistance included source checking, word counts and rendered-page inspection. No full prompt log is required or included.

## Additional files

The complete ZIP contains code, web/, tests/, tools/, docs/ and the [report PDF](output/pdf/Reference_First_A2_Report.pdf), with [editable Markdown](docs/report.md), [HTML](docs/report.html), figures and evidence. [tools/package_submission.py](tools/package_submission.py) rebuilds the complete package with launch instructions. Report regeneration separately requires ReportLab and Windows Calibri fonts. Course materials, Git history, caches and credentials are excluded.
