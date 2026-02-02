# 🎬 Advanced Media File Searcher (Archived)

A desktop tool for hunting down movies and TV shows inside chaotic media libraries using smart filename parsing, batch workflows, and a clean tabbed GUI.

This project is archived — but it represents a more mature, fully-wired iteration of an idea that grew beyond “just a file searcher.”

⚠️ **LICENSE & USAGE NOTICE — READ FIRST**

This repository is **source-available for private technical evaluation and testing only**.

- ❌ No commercial use  
- ❌ No production use  
- ❌ No academic, institutional, or government use  
- ❌ No research, benchmarking, or publication  
- ❌ No redistribution, sublicensing, or derivative works  
- ❌ No independent development based on this code  

All rights remain exclusively with the author.  
Use of this software constitutes acceptance of the terms defined in **LICENSE.txt**.

---

## 🚀 What makes this different?

This isn’t a dumb filename grep.

This tool was built to deal with real-world media mess:

- scene-style filenames
- inconsistent folder structures
- mixed movie + TV libraries
- large drives where “just search manually” stops being practical

It understands patterns, not just strings.

## 🧠 Core capabilities

 - 🔍 Smart media search

    - Searches folders using filename-aware parsing
    - Designed for movies, TV shows, and mixed libraries

- 🎞️ Media-aware parsing

    - Separate logic paths for movies vs TV shows
    - Handles common metadata embedded in filenames (year, season/episode, resolution, etc.)

-  📦 Batch mode

    - Run multiple search terms in one pass
    - Designed for large libraries and automation-style workflows

- 🖥️ Tabbed desktop GUI

    - Search — interactive exploration
    - Batch — large-scale processing
    - Settings — persistent configuration

- 🎨 Themes + settings

    - Dark mode support
    - Saved defaults (folders, file exclusions, UI preferences)
    - Debug visibility toggle

## 🧭 Why this exists

At some point, media libraries stop being “folders” and start becoming data problems.

This project was an experiment in:

- treating filenames as semi-structured data
- separating parsing logic from UI
- building a practical desktop tool instead of a throwaway script

It evolved far enough to need:

- persistent settings
- cleaner dependency wiring
- a real GUI layout

That’s where it paused — intentionally preserved in this repo.

## 🗂️ Project structure (high level)

You’ll find the code split into clear responsibilities:

- gui_app.py – main Tkinter app + tab container
- search_tab.py – interactive searching UI
- batch_tab.py – batch processing workflows
- settings_tab.py – saved configuration UI
- search_service.py – threaded search orchestration
- filetracker.py – filesystem scanning + filtering
- base_parser.py (+ specific parsers) – filename intelligence
- themes.py – UI look & feel
- settings.json – persisted user preferences

>Some default paths are Windows-specific (e.g. H:\...).</br>
>They’re just examples and can be changed directly in the Settings tab.

## ▶️ Running it

Requirements:

- Python 3.x

Tkinter (included with most Python installs)

Run the app:
```bash
python gui_app.py
```

(If your entry point differs after reconstructing the files, run the module with the __main__ block.)

## 🧪 How to use it

### 🔍 Search tab

- Pick a folder
- Enter a search term
- Choose smart vs exact matching
- Start / stop searches cleanly

### 📦 Batch tab

- Provide a list of search terms
- Run them in one pass
- Collect results for review or export

### ⚙️ Settings tab

- Default folders
- Filetype exclusions
- Dark mode toggle
- Debug output visibility

Settings persist between sessions.

---

## ⚠️ Known limitations (honest list)

- Archived project — no active maintenance

- No persistent media index/database
- No automated test suite
- Parsing rules reflect real-world heuristics, not formal specs
- Not packaged as an installer

All of that is intentional for a prototype snapshot.

---

## 💡 If this were ever revived…

Ideas that were clearly next on the roadmap:

- Persistent media index (SQLite)
- Plugin-based parser system
- Background worker pool for scanning
- Exportable results (CSV / JSON)
- Packaging (PyInstaller)
- Unit tests for parsing logic

## 📜 License

Currently unlicensed (personal archive).

If you plan to share or reuse it publicly, consider adding:

MIT for maximum freedom, or

Apache 2.0 for clearer redistribution terms.

## Contribution Policy

Feedback, bug reports, and suggestions are welcome.

You may submit:

- Issues
- Design feedback
- Pull requests for review

However:

- Contributions do not grant any license or ownership rights
- The author retains full discretion over acceptance and future use
- Contributors receive no rights to reuse, redistribute, or derive from this code

---

## License
This project is not open-source.

It is licensed under a private evaluation-only license.
See LICENSE.txt for full terms.
