# Advanced Media File Searcher (Archived)

An experimental Python desktop application for scanning, classifying, and searching large media libraries (movies and TV shows).

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

This project is **archived** and kept as a reference implementation. It represents an ambitious prototype exploring media-aware search, batch processing, and GUI-driven workflows.

## What this project is
This is **not** a simple filename search tool.

The goal of this project was to explore:

- structured media parsing (movies vs TV shows)
- metadata-aware classification
- batch media processing
- a multi-tab desktop GUI for media operations

## Core features (prototype-level)

- **Media file scanning**
  - Walks directories and inspects media files
- **Media classification**
  - Distinguishes movies vs TV shows
  - Uses naming and structural heuristics
- **Dedicated parsers**
  - Separate parsing logic for movies and TV shows
- **Search service**
  - Centralized logic for querying parsed media
- **Batch processing**
  - Batch-oriented workflows for large libraries
- **Multi-tab GUI**
  - Search tab
  - Batch processing tab
  - Settings tab
- **Theming support**
  - Centralized theme definitions for UI consistency

## Project structure
```text
AdvancedMediaSearcher/
├── gui_app.py
├── gui_utilities.py
├── themes.py
├── search_service.py
├── media_classifier.py
├── movie_parser.py
├── tv_show_parser.py
├── batch_processor.py
├── filetracker.py
├── search_tab.py
├── batch_tab.py
├── settings_tab.py
├── base_parser.py
└── Documents/
├── Advanced Media File Searcher.docx
└── Program Capabilities and Analysis Report.docx
```

## Architectural notes

- Parsing, classification, searching, batch processing, and UI are intentionally separated.
- GUI tabs are implemented as discrete modules rather than a monolithic window.
- Media logic is domain-aware (movies vs TV shows), not generic file handling.
- The project evolved iteratively; some components overlap slightly as ideas matured.

This repo intentionally preserves that evolution.

## Requirements

- Python 3.9+
- Standard Python GUI stack (as used in the codebase)
- No external services required

> Note: This project does not currently include a persistence layer or index database. All processing is runtime-based.

## Status
**Archived / Prototype**

This project is not actively maintained. It exists as:

- a design reference
- an architectural experiment
- a snapshot of an evolving idea

## Known limitations

- No automated tests
- No persistent media index
- No plugin system for parsers
- Limited error handling
- Performance not optimized for very large libraries

These are known trade-offs for an exploratory prototype.

## Ideas for future revival

If revisited, potential extensions include:

- Persistent media index (SQLite or similar)
- Plugin-based parser architecture
- Background worker threads for scanning
- Caching and incremental rescans
- Unit tests for parsers and classifiers
- Exportable search results (JSON / CSV)

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
