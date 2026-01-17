# Enhanced Python Import Cycle Scanner & Visualizer

**A modern desktop tool to detect circular imports, visualize module dependencies, and understand your Python project's structure.**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=flat&logo=python&logoColor=white" alt="Python version">
  <img src="https://img.shields.io/badge/PyQt6-6.5+-green?style=flat" alt="PyQt6">
  <img src="https://img.shields.io/badge/pyvis-interactive%20graphs-orange?style=flat" alt="pyvis">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat" alt="License">
</p>

## ✨ Features

- Scans an entire Python project for **module-to-module imports**
- Detects **circular dependencies** (strongly connected components)
- Beautiful **interactive dependency graph** using pyvis + vis.js
  - Red nodes = part of a cycle
  - Zoom, pan, drag, hover for file paths
- Classic **tree/table view** showing modules, import counts and lists
- Highlights modules involved in cycles (bold + dark red background)
- **Rescan** project with one click (Ctrl+R)
- **Export** results as structured JSON
- Works both as **GUI application** and **CLI tool**
- Clean dark-themed graph with local vis.js resources (no internet needed)

## Screenshots

GUI with Tree View and Interactive Graph Tab  
*(Add your own screenshots here — recommended: one of the tree, one of the graph with a cycle visible)*

<!-- You can later add: -->
<!-- ![Tree View](screenshots/tree-view.png)   ![Graph View with cycle](screenshots/graph-cycle.png) -->

## Requirements

- Python **3.9** or newer
- PyQt6
- pyvis
- (optional but recommended: PySide6 as alternative Qt backend)


## Recommended - minimal dependencies
```bash
pip install PyQt6 pyvis
```
or with PySide6 compatibility layer:
```Bash
pip install PySide6 pyvis
```
---
## Installation
### Option 1: Run directly from source (recommended for development)
```Bash
git clone https://github.com/YOUR-USERNAME/python-import-cycle-scanner.git
cd python-import-cycle-scanner
```
## Install dependencies
```bash
pip install -r requirements.txt    # create this file — see below
```
Run GUI (current directory as project root)
```bash
python scanner_gui_v0.7.py
```
Or scan specific folder
```bash
python scanner_gui_v0.7.py /path/to/your/project
```
Option 2: One-file executable (PyInstaller)
```Bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ImportScanner" scanner_gui_v0.7.py
```
The executable appears in the dist/ folder.

## requirements.txt 
```text
textPyQt6 >= 6.5.0
pyvis >= 0.3.2
```
---
## Usage

GUI mode (most common)
```Bash
python scanner_gui_v0.7.py
# → scans current directory
```
or specify folder
```bash
python scanner_gui_v0.7.py ~/projects/my-large-app
```
## Keyboard shortcuts
```text
Ctrl+R — Rescan current project
Ctrl+E — Export JSON
Ctrl+Q — Quit
```
CLI mode (quick check)
```Bash
python scanner_gui_v0.7.py /path/to/project
```
Example output:
```text
Scanned 47 modules

Modules and Imports:
myapp.core.utils: -
myapp.core.models: myapp.core.utils
myapp.api.views: myapp.core.models, myapp.core.utils
...

Circular Dependencies:
Cycle 1: myapp.core.models → myapp.api.views → myapp.core.models
```
## How It Works
- Walks through all .py files in the project
- Parses AST to collect import and from ... import ... statements
- Resolves relative imports (from . import ..., from ..parent import ...)
- Builds directed graph: module → imported modules
- Uses Tarjan's algorithm variant to find strongly connected components (cycles)
- Generates interactive HTML graph with pyvis (nodes in red if cyclic)
- Displays results in sortable tree view + QtWebEngine-based graph tab

## Project Structure
```text.
├── scanner_gui_v0.7.py       # main file — GUI + CLI entry point
├── graph.html                # generated interactive graph (created on run)
├── lib/                      # local vis.js files (created by pyvis)
└── README.md
```
## Known Limitations
- Does not follow dynamic imports (__import__, importlib.import_module)
- Does not resolve imports from installed packages (only project-local modules)
- Very large projects (> 1000 modules) may make graph hard to read
- Graph is regenerated on every rescan (can be slow on huge codebases)

## Future Improvements (ideas welcome!)
- Filter graph (show only cycles / subgraph around selected module)
- Export graph as PNG / SVG
- Support for __init__.py namespace packages
- Dependency strength visualization (number of imports)
- Dark / light theme toggle for GUI
- Command-line-only mode with richer output (ASCII graph, JSON)

## Contributing

Contributions are very welcome!

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

## License
Distributed under the MIT License. See LICENSE for more information.
