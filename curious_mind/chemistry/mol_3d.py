"""3D molecule rendering via PubChem (SDF) + 3Dmol.js (CDN, no Python deps).

Lookup strategy:
  1. If SMILES given, request 3D SDF from PubChem by SMILES.
  2. Else, resolve formula → first CID → 3D SDF.

PubChem occasionally has no 3D conformer (esp. ionic salts, exotic radicals).
We treat that gracefully and surface a placeholder in the UI.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import uuid

import streamlit as st

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"

# Reasonable diatomic / common-element SMILES for elemental reagents.
ELEMENT_SMILES = {
    "H": "[H][H]",
    "O": "O=O",
    "N": "N#N",
    "F": "FF",
    "Cl": "ClCl",
    "Br": "BrBr",
    "I": "II",
    "S": "S",          # rhombic sulfur is S8 but PubChem will resolve
    "C": "[C]",
    "He": "[He]",
    "Ne": "[Ne]",
    "Ar": "[Ar]",
    "Kr": "[Kr]",
    "Xe": "[Xe]",
}


def _http_get(url: str, timeout: int = 5) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status != 200:
                return None
            return r.read()
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_sdf_3d(smiles: str | None = None, formula: str | None = None) -> str | None:
    """Fetch a 3D SDF block from PubChem. Returns None on any failure."""
    # 1. Try SMILES path
    if smiles:
        smi_enc = urllib.parse.quote(smiles, safe="")
        url = f"{PUBCHEM_BASE}/smiles/{smi_enc}/SDF?record_type=3d"
        body = _http_get(url)
        if body:
            text = body.decode("utf-8", errors="ignore").strip()
            if text and "$$$$" in text:
                return text

    # 2. Fall back to formula → CID → SDF
    if formula:
        fml_enc = urllib.parse.quote(formula, safe="")
        cid_url = f"{PUBCHEM_BASE}/formula/{fml_enc}/cids/JSON"
        body = _http_get(cid_url)
        if body:
            try:
                data = json.loads(body.decode("utf-8", errors="ignore"))
                cids = data.get("IdentifierList", {}).get("CID", [])
            except (json.JSONDecodeError, AttributeError):
                cids = []
            if cids:
                cid = cids[0]
                url = f"{PUBCHEM_BASE}/cid/{cid}/SDF?record_type=3d"
                body = _http_get(url)
                if body:
                    text = body.decode("utf-8", errors="ignore").strip()
                    if text and "$$$$" in text:
                        return text

    return None


def mol_viewer_html(sdf: str, *, height: int = 320, style: str = "stick") -> str:
    """Return a self-contained HTML snippet that renders SDF in 3Dmol.js."""
    div_id = f"mol3d-{uuid.uuid4().hex[:10]}"
    # Embed SDF as JSON-encoded string to dodge quote/newline issues
    sdf_js = json.dumps(sdf)
    style_block = {
        "stick": '{stick: {radius: 0.16}}',
        "sphere": '{sphere: {scale: 0.3}}',
        "ball_stick": '{stick: {radius: 0.12}, sphere: {scale: 0.25}}',
    }.get(style, '{stick: {radius: 0.16}, sphere: {scale: 0.22}}')

    return f"""
<div id="{div_id}" style="
    position: relative;
    width: 100%; height: {height}px;
    background: #F8FAFC; border: 1px solid rgba(31,56,100,0.12);
    border-radius: 8px; overflow: hidden;
"></div>
<script src="https://3dmol.org/build/3Dmol-min.js"></script>
<script>
(function() {{
  var attempts = 0;
  function init() {{
    if (typeof $3Dmol === 'undefined') {{
      attempts += 1;
      if (attempts > 50) {{
        // CDN blocked (school firewall) — show a message instead of
        // polling forever over a blank box.
        var el = document.getElementById("{div_id}");
        if (el) el.innerHTML = '<div style="padding:1rem;color:#5B6478;' +
          'font-size:0.85rem;">3D viewer could not load (network blocked?).</div>';
        return;
      }}
      setTimeout(init, 80);
      return;
    }}
    var element = document.getElementById("{div_id}");
    if (!element) return;
    var viewer = $3Dmol.createViewer(element, {{
      backgroundColor: "#F8FAFC",
      antialias: true,
    }});
    var sdf = {sdf_js};
    viewer.addModel(sdf, "sdf");
    viewer.setStyle({{}}, {style_block});
    viewer.zoomTo();
    viewer.zoom(1.2);
    viewer.spin("y", 0.5);
    viewer.render();
  }}
  init();
}})();
</script>
"""


def smiles_for_reactant(kind: str, ident: str) -> tuple[str | None, str | None]:
    """Return (smiles, formula) for a selected reactant.

    `ident` is the element symbol or compound formula. Compound SMILES come
    from the local KB if present; element SMILES from ELEMENT_SMILES; otherwise
    we pass the symbol/formula and let PubChem resolve.
    """
    if kind == "element":
        smi = ELEMENT_SMILES.get(ident)
        return smi, ident
    # compound
    from .data_loader import compound_by_formula
    rec = compound_by_formula(ident) or {}
    smi = rec.get("smiles") or None
    return smi, ident
