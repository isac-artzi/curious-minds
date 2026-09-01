"""Atom-level zoom + conservation chips for the Chemistry Lab.

Pure HTML / SVG / CSS, no third-party deps. Parses Claude's
``balanced_equation`` (LaTeX-flavored), pulls out per-element counts on
each side, and renders an animated "molecule pill" scene with
conservation chips below.

Public:
- ``parse_formula(formula)``      element symbol → count for one formula
- ``parse_equation(equation)``    (reactant_terms, product_terms) lists
- ``atom_counts(equation)``       (reactant_counts, product_counts) dicts
- ``atom_zoom_svg(equation)``     full HTML block for the zoom view
- ``atom_zoom_height()``          recommended iframe height
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_TERM_RE = re.compile(r"^(\d*)\s*(.+)$")
_ATOM_RE = re.compile(r"([A-Z][a-z]?)(\d*)")


def _strip_latex(s: str) -> str:
    """Reduce a LaTeX-ish equation to plain ASCII suitable for parsing."""
    s = s.replace(r"\rightarrow", "→").replace(r"\to", "→")
    # Tolerate plain-text arrows the model sometimes emits instead of LaTeX.
    s = s.replace("-->", "→").replace("->", "→").replace("⟶", "→").replace("=", "→")
    s = s.replace(r"\;", " ").replace(r"\,", " ").replace("$", "")
    # H_2 or H_{2} → H2
    s = re.sub(r"_\{?(\d+)\}?", r"\1", s)
    # drop superscript charges like ^+, ^{2+}
    s = re.sub(r"\^\{?[^\s{}+\-]*[+\-]?\}?", "", s)
    return s.strip()


def _expand_groups(f: str) -> str:
    """Expand parenthesized groups: ``Ca(OH)2`` → ``CaOHOH``.

    Handles nesting by expanding innermost groups first.
    """
    group_re = re.compile(r"\(([^()]*)\)(\d*)")
    while "(" in f:
        new = group_re.sub(lambda m: m.group(1) * int(m.group(2) or 1), f)
        if new == f:  # unbalanced parens — give up gracefully
            return f.replace("(", "").replace(")", "")
        f = new
    return f


def parse_formula(formula: str) -> dict[str, int]:
    """Element symbol → atom count for a formula, including parenthesized
    groups like ``Ca(OH)2`` and ``Al2(SO4)3``.

    Handles SMILES-style ionic strings like ``[Na+].[Cl-]`` by stripping
    brackets and dots. Subscripts use the trailing-number convention
    (``H2O``, ``Fe2O3``).
    """
    if not formula:
        return {}
    f = re.sub(r"[\[\]+\-.\s]", "", formula)
    f = _expand_groups(f)
    out: dict[str, int] = {}
    for match in _ATOM_RE.finditer(f):
        sym, cnt = match.group(1), match.group(2)
        if not sym:
            continue
        n = int(cnt) if cnt else 1
        out[sym] = out.get(sym, 0) + n
    return out


def parse_equation(equation: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Split a balanced equation into (lhs, rhs) lists of (coefficient, formula)."""
    s = _strip_latex(equation or "")
    if "→" not in s:
        return [], []
    lhs_s, rhs_s = s.split("→", 1)

    def parse_side(side: str) -> list[tuple[int, str]]:
        terms: list[tuple[int, str]] = []
        for raw in side.split("+"):
            t = raw.strip()
            if not t:
                continue
            m = _TERM_RE.match(t)
            if not m:
                continue
            coef_s, formula = m.group(1), m.group(2).strip()
            try:
                coef = int(coef_s) if coef_s else 1
            except ValueError:
                coef = 1
            if formula:
                terms.append((coef, formula))
        return terms

    return parse_side(lhs_s), parse_side(rhs_s)


def atom_counts(equation: str) -> tuple[dict[str, int], dict[str, int]]:
    """Per-element atom tallies for the reactant and product sides."""
    lhs, rhs = parse_equation(equation)
    react: dict[str, int] = {}
    prod: dict[str, int] = {}
    for coef, f in lhs:
        for sym, n in parse_formula(f).items():
            react[sym] = react.get(sym, 0) + coef * n
    for coef, f in rhs:
        for sym, n in parse_formula(f).items():
            prod[sym] = prod.get(sym, 0) + coef * n
    return react, prod


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# Approximate CPK-style colors for common elements (fallback grey otherwise).
_ELEMENT_COLOR = {
    "H":  "#ffffff", "C":  "#222222", "N":  "#3050f8", "O":  "#ff0d0d",
    "F":  "#90e050", "Na": "#ab5cf2", "Mg": "#8aff00", "Al": "#bfa6a6",
    "Si": "#f0c8a0", "P":  "#ff8000", "S":  "#ffff30", "Cl": "#1ff01f",
    "K":  "#8f40d4", "Ca": "#3dff00", "Fe": "#e06633", "Cu": "#c88033",
    "Zn": "#7d80b0", "Br": "#a62929", "I":  "#940094",
}
_DARK_TEXT_ATOMS = {"H", "F", "Cl", "Br", "I", "S", "O", "Mg", "Al", "Si"}


def _color_for(sym: str) -> str:
    return _ELEMENT_COLOR.get(sym, "#b4b8c0")


def _text_for(sym: str) -> str:
    return "#000" if sym in _DARK_TEXT_ATOMS else "#fff"


def _molecule_pill_svg(coef: int, formula: str) -> str:
    """One molecule rendered as a row of atom circles inside a rounded pill."""
    atoms = parse_formula(formula)
    if not atoms:
        return ""
    # Flatten into one circle per atom instance (cap for readability)
    inst: list[str] = []
    for sym, n in atoms.items():
        inst.extend([sym] * n)
    overflow = max(0, len(inst) - 10)
    inst = inst[:10]

    spacing = 26
    pad = 22
    width = max(90, spacing * len(inst) + pad * 2)
    height = 60
    coef_label = str(coef) if coef > 1 else ""

    circles: list[str] = []
    bonds: list[str] = []
    for i, sym in enumerate(inst):
        cx = pad + i * spacing
        col = _color_for(sym)
        circles.append(
            f'<circle cx="{cx}" cy="28" r="11" fill="{col}" '
            f'stroke="#1f2937" stroke-width="1.2"/>'
            f'<text x="{cx}" y="32" text-anchor="middle" font-size="11" '
            f'font-weight="700" fill="{_text_for(sym)}">{sym}</text>'
        )
        if i > 0:
            x1 = pad + (i - 1) * spacing + 11
            x2 = cx - 11
            bonds.append(
                f'<line x1="{x1}" y1="28" x2="{x2}" y2="28" '
                f'stroke="#cbd5e1" stroke-width="2"/>'
            )

    coef_html = (
        f'<text x="6" y="32" font-size="14" font-weight="700" fill="#fde68a">{coef_label}</text>'
        if coef_label else ""
    )
    overflow_html = (
        f'<text x="{width - 18}" y="32" font-size="10" fill="#cbd5e1">+{overflow}</text>'
        if overflow else ""
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="2" y="8" width="{width-4}" height="40" rx="20" '
        f'fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.18)"/>'
        f'{coef_html}{"".join(bonds)}{"".join(circles)}{overflow_html}'
        f'<text x="{width/2}" y="56" text-anchor="middle" font-size="10" '
        f'fill="#94a3b8">{formula}</text></svg>'
    )


def atom_zoom_height() -> int:
    return 380


def atom_zoom_svg(equation: str) -> str:
    """Return a complete HTML/SVG/CSS block for the atom-zoom scene."""
    lhs, rhs = parse_equation(equation)
    react_counts, prod_counts = atom_counts(equation)

    if not lhs and not rhs:
        return (
            '<div style="padding:30px;color:#cbd5e1;text-align:center;'
            'background:radial-gradient(ellipse at center,#1b2434,#0b1020);'
            'border-radius:14px;font-family:-apple-system,sans-serif;">'
            '<em>No balanced equation to zoom into.</em></div>'
        )

    react_pills = "".join(
        f'<div class="pill">{_molecule_pill_svg(c, f)}</div>' for c, f in lhs
    ) or '<div class="pill"><em>—</em></div>'
    prod_pills = "".join(
        f'<div class="pill">{_molecule_pill_svg(c, f)}</div>' for c, f in rhs
    ) or '<div class="pill"><em>—</em></div>'

    # Per-element conservation chips
    all_elements = sorted(set(react_counts) | set(prod_counts))
    chip_html: list[str] = []
    for sym in all_elements:
        r = react_counts.get(sym, 0)
        p = prod_counts.get(sym, 0)
        ok = (r == p)
        mark = "✓" if ok else "⚠"
        color = "#22c55e" if ok else "#f59e0b"
        chip_html.append(
            f'<span class="chip" style="border-color:{color};">'
            f'<span class="chip-sym" style="background:{_color_for(sym)};'
            f'color:{_text_for(sym)};">{sym}</span>'
            f'{r} → {p} <span style="color:{color};font-weight:700;">{mark}</span>'
            f'</span>'
        )

    balanced = all(react_counts.get(s, 0) == prod_counts.get(s, 0) for s in all_elements)
    banner = (
        '<div class="banner ok">⚛️ Atoms balance on both sides — '
        'matter is conserved.</div>' if balanced else
        '<div class="banner warn">⚠️ Atom counts don\'t match yet — '
        'either the equation isn\'t balanced or the parser missed something.</div>'
    )

    return _ATOM_CSS + f"""
<div class="atom-zoom">
  <div class="row reactants">{react_pills}</div>
  <div class="arrow-row">
    <svg viewBox="0 0 240 44" width="240" height="44" xmlns="http://www.w3.org/2000/svg">
      <defs><marker id="azh" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 z" fill="#fcd34d"/></marker></defs>
      <line x1="6" y1="22" x2="230" y2="22" stroke="#fcd34d"
            stroke-width="3" marker-end="url(#azh)"/>
      <g class="atomwave">
        <circle cx="40"  cy="14" r="3.5" fill="#ffffff"/>
        <circle cx="100" cy="30" r="3.5" fill="#ff0d0d"/>
        <circle cx="160" cy="14" r="3.5" fill="#3050f8"/>
      </g>
    </svg>
    <div class="rearranging">bonds breaking · atoms regrouping · bonds re-forming</div>
  </div>
  <div class="row products">{prod_pills}</div>
  <div class="chips">{"".join(chip_html) or '<em style="color:#94a3b8;">no atom data parsed</em>'}</div>
  {banner}
</div>
"""


_ATOM_CSS = """
<style>
.atom-zoom {
  background: radial-gradient(ellipse at center, #1b2434 0%, #0b1020 100%);
  border-radius: 14px;
  padding: 14px 16px 16px;
  color: #e5e7eb;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  display: flex; flex-direction: column; gap: 10px;
}
.atom-zoom .row {
  display: flex; flex-wrap: wrap; gap: 12px; justify-content: center;
  align-items: center;
}
.atom-zoom .pill {
  animation: pillPulse 3s ease-in-out infinite alternate;
}
@keyframes pillPulse {
  from { transform: translateY(0); }
  to   { transform: translateY(-3px); }
}
.atom-zoom .arrow-row {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.atom-zoom .atomwave circle {
  animation: drift 2.2s ease-in-out infinite;
  transform-box: fill-box;
  transform-origin: center;
}
.atom-zoom .atomwave circle:nth-child(2) { animation-delay: 0.4s; }
.atom-zoom .atomwave circle:nth-child(3) { animation-delay: 0.8s; }
@keyframes drift {
  0%   { transform: translateX(-30px); opacity: 0; }
  20%  { opacity: 1; }
  80%  { opacity: 1; }
  100% { transform: translateX(30px); opacity: 0; }
}
.atom-zoom .rearranging {
  font-size: 0.8rem; color: #fde68a; font-style: italic;
}
.atom-zoom .chips {
  display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;
  margin-top: 4px;
}
.atom-zoom .chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,0.06);
  border: 1px solid #475569;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.88rem;
}
.atom-zoom .chip-sym {
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 50%;
  font-size: 0.72rem; font-weight: 700;
  border: 1px solid #1f2937;
}
.atom-zoom .banner {
  text-align: center; padding: 8px; border-radius: 8px;
  font-size: 0.88rem;
}
.atom-zoom .banner.ok   { background: rgba(34,197,94,0.12);  color: #86efac; border: 1px solid rgba(34,197,94,0.35); }
.atom-zoom .banner.warn { background: rgba(245,158,11,0.12); color: #fde68a; border: 1px solid rgba(245,158,11,0.35); }
</style>
"""
