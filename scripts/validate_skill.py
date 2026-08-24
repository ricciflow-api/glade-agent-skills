#!/usr/bin/env python3
"""Repository-level structural checks for the amazon-data skill."""

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "amazon-data"

skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
match = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
assert match, "SKILL.md must start with YAML frontmatter"
frontmatter = match.group(1)
assert re.search(r"^name:\s*amazon-data\s*$", frontmatter, re.MULTILINE)
assert re.search(r"^description:\s*\S.+$", frontmatter, re.MULTILINE)
assert "TODO" not in skill_text
assert "references/operations.md" in skill_text
assert "scripts/glade_api.py" in skill_text

openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
assert 'display_name: "Glade Amazon Data"' in openai_yaml
assert "$amazon-data" in openai_yaml
assert 'url: "https://gladeapi.com/api/mcp"' in openai_yaml

operations = (SKILL / "references" / "operations.md").read_text(encoding="utf-8")
script_source = (SKILL / "scripts" / "glade_api.py").read_text(encoding="utf-8")
tree = ast.parse(script_source, filename="glade_api.py")
paths = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "PATHS" for target in node.targets
    ):
        paths = ast.literal_eval(node.value)
        break
assert paths is not None and len(paths) == 17
for operation, path in paths.items():
    assert f"`{operation}`" in operations
    assert f"`{path}`" in operations

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
assert manifest["skills"] == [
    {
        "name": "amazon-data",
        "path": "skills/amazon-data",
        "description": "Research public Amazon products, search, offers, reviews, sellers, categories, deals, best sellers, identifiers, stock, and sales estimates through Glade API.",
    }
]

for path in ROOT.rglob("*"):
    if path.is_file() and ".git" not in path.parts:
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not re.search(r"glade_live_[A-Za-z0-9_-]{12,}", text), f"key-shaped literal in {path}"

print("Validated amazon-data skill structure and 17-operation catalog.")
