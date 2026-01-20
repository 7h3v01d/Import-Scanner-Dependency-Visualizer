import sys
import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any

from PyQt6.QtGui import QAction, QFont, QKeySequence, QColor
from PyQt6 import QtWebEngineWidgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QMessageBox, QStatusBar, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from pyvis.network import Network


# ---------- Utility Functions ----------

def to_fqn(project_root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(project_root).with_suffix("")
    return ".".join(rel.parts)


def resolve_from_import(current_fqn: str, level: int, module: str | None) -> str:
    pkg_parts = current_fqn.split(".")[:-1]
    if level:
        pkg_parts = pkg_parts[: -level + 1] if level > 1 else pkg_parts
    if module:
        return ".".join([*pkg_parts, module])
    return ".".join(pkg_parts)


def strongly_connected_components(graph: Dict[str, set]) -> List[List[str]]:
    index = 0
    stack, onstack = [], set()
    indices, lowlink, sccs = {}, {}, []

    def dfs(v):
        nonlocal index
        indices[v] = lowlink[v] = index
        index += 1
        stack.append(v)
        onstack.add(v)
        for w in graph.get(v, ()):
            if w not in indices:
                dfs(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in onstack:
                lowlink[v] = min(lowlink[v], indices[w])
        if lowlink[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                onstack.remove(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(comp)

    for v in graph:
        if v not in indices:
            dfs(v)
    return sccs


# ---------- Scanner ----------

class ImportScanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.module_info: Dict[str, Dict[str, Any]] = {}

    def scan(self):
        self.module_info.clear()
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".py"):
                    path = Path(root) / file
                    fqn = to_fqn(self.project_root, path)
                    self.module_info[fqn] = {"path": str(path), "imports": []}
                    self._scan_file(path, fqn)

    def _scan_file(self, path: Path, fqn: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(path))
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.module_info[fqn]["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imported = resolve_from_import(fqn, node.level, node.module)
                self.module_info[fqn]["imports"].append(imported)

    def build_graph(self) -> Dict[str, set]:
        graph = {}
        for mod, data in self.module_info.items():
            graph[mod] = set(data["imports"])
        return graph

    def find_cycles(self) -> List[List[str]]:
        graph = self.build_graph()
        return strongly_connected_components(graph)


# ---------- Interactive Graph (pyvis) ----------

def build_interactive_graph(scanner: ImportScanner, out_html: str):
    graph = scanner.build_graph()
    cycles = {frozenset(c) for c in scanner.find_cycles()}

    # Initialize Network with local vis.js
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        bgcolor="#222222",
        font_color="white",
        cdn_resources="local"  # Ensure local vis.js resources
    )
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=120, spring_strength=0.05)

    # Add nodes
    for mod, data in scanner.module_info.items():
        color = "gray"
        for cycle in cycles:
            if mod in cycle:
                color = "red"
        net.add_node(mod, label=mod, title=data["path"], color=color)

    # Add edges
    for src, dests in graph.items():
        for dst in dests:
            if dst in scanner.module_info:
                net.add_edge(src, dst)

    # Save HTML with local resources
    try:
        net.write_html(out_html, notebook=False, local=True)
        # Verify lib directory and vis-network.min.js exist
        lib_dir = Path(out_html).parent / "lib"
        vis_js = lib_dir / "vis-network.min.js"
        if not vis_js.exists():
            print(f"Warning: {vis_js} not found, graph may not render")
    except Exception as e:
        print(f"Error generating graph.html: {e}")


# ---------- GUI ----------

class ImportTreeViewer(QMainWindow):
    def __init__(self, scanner: ImportScanner):
        super().__init__()
        self.scanner = scanner

        self.setWindowTitle("Enhanced Import Scanner (PyQt6)")
        self.setMinimumSize(1200, 800)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tree tab
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Module", "# Imports", "Imports List"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("QTreeWidget { font-size: 14px; }")
        self.tabs.addTab(self.tree, "Import Tree")

        # Graph tab
        self.webview = QtWebEngineWidgets.QWebEngineView()
        self.webview.page().javaScriptConsoleMessage = (
            lambda level, msg, line, source: print(f"JS Error: {msg} at {source}:{line}")
        )
        self.tabs.addTab(self.webview, "Interactive Graph")

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Menus + Toolbar
        self._create_actions()
        self._create_menus()
        self._create_toolbar()

        # Populate
        self.populate_tree()
        self.generate_graph()

    def _create_actions(self):
        self.rescan_act = QAction("Rescan", self)
        self.rescan_act.setShortcut(QKeySequence("Ctrl+R"))
        self.rescan_act.triggered.connect(self.rescan)

        self.export_json_act = QAction("Export JSON", self)
        self.export_json_act.setShortcut(QKeySequence("Ctrl+E"))
        self.export_json_act.triggered.connect(self.export_json)

        self.quit_act = QAction("Quit", self)
        self.quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_act.triggered.connect(self.close)

        self.about_act = QAction("About", self)
        self.about_act.triggered.connect(self.show_about)

    def _create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.rescan_act)
        file_menu.addAction(self.export_json_act)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_act)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.about_act)

    def _create_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.addAction(self.rescan_act)
        toolbar.addAction(self.export_json_act)
        toolbar.addAction(self.quit_act)

    def populate_tree(self):
        self.tree.clear()
        cycles = {frozenset(c) for c in self.scanner.find_cycles()}

        for module, data in sorted(self.scanner.module_info.items()):
            imports = data["imports"]
            imports_str = ", ".join(imports) if imports else "-"
            item = QTreeWidgetItem([module, str(len(imports)), imports_str])

            if any(module in cycle for cycle in cycles):
                font = QFont()
                font.setBold(True)
                for i in range(3):
                    item.setFont(i, font)
                    item.setBackground(i, QColor("#8b0000"))

            self.tree.addTopLevelItem(item)

        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)

        self.status.showMessage(
            f"Scanned {len(self.scanner.module_info)} modules | Cycles: {len(cycles)}"
        )

    def generate_graph(self):
        out_html = "graph.html"
        build_interactive_graph(self.scanner, out_html)
        out_path = Path(out_html).resolve()
        # Use file:// URL to ensure local resource loading
        self.webview.load(QUrl.fromLocalFile(str(out_path)))
        print(f"Loading graph from: file:///{str(out_path)}")

    def rescan(self):
        self.scanner.scan()
        self.populate_tree()
        self.generate_graph()

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON Files (*.json)")
        if not path:
            return
        data = {"modules": self.scanner.module_info, "cycles": self.scanner.find_cycles()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.status.showMessage(f"Exported JSON to {path}")

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Enhanced Import Scanner (PyQt6)\n\n"
            "• Import Tree + Interactive Dependency Graph\n"
            "• Pan, zoom, and click nodes\n"
            "• Highlights circular dependencies in red\n\n"
            "Clicking a node shows its file path in tooltip."
        )


# ---------- CLI Output ----------

def print_cli_output(scanner: ImportScanner):
    scanner.scan()
    cycles = scanner.find_cycles()
    graph = scanner.build_graph()

    print(f"Scanned {len(scanner.module_info)} modules")
    print("\nModules and Imports:")
    for module, data in sorted(scanner.module_info.items()):
        imports = data["imports"]
        print(f"{module}: {', '.join(imports) if imports else '-'}")

    print("\nCircular Dependencies:")
    if cycles:
        for i, cycle in enumerate(cycles, 1):
            print(f"Cycle {i}: {' -> '.join(cycle)}")
    else:
        print("No circular dependencies found")


# ---------- Main ----------

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        project_root = sys.argv[1]
        scanner = ImportScanner(project_root)
        print_cli_output(scanner)
    else:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        scanner = ImportScanner(os.getcwd())
        viewer = ImportTreeViewer(scanner)
        viewer.show()
        sys.exit(app.exec())