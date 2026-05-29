"""Living Biome Theater — animated HTML/SVG/CSS hero for the Ecosystem Lab.

Renders the user's selected biome as a vivid scene with drifting emoji
creatures. The number of each creature scales with the log of its final
simulated population, so a wolf scenario gets one wolf and a wildebeest
migration gets many.

Pure presentation — no Streamlit calls in here so it can be unit-tested or
re-used in other contexts. The entry point is :func:`render_biome_theater`.
"""

from __future__ import annotations

import html as _html
import math
import random as _random


# ---------------------------------------------------------------------------
# Biome backdrop palettes — gradient stops + a sky/floor color split.
# Hand-tuned so each biome reads at a glance: snowy tundra is icy white,
# rainforest is deep green, desert is sand+coral, etc.
# ---------------------------------------------------------------------------
_BIOME_THEMES: dict[str, dict[str, str]] = {
    "temperate_forest": {
        "sky": "#a7d1c1", "floor": "#3a5a2e",
        "label": "Temperate forest", "accent": "#5d8f4a",
    },
    "boreal_forest": {
        "sky": "#cfe1e8", "floor": "#2c4a3a",
        "label": "Boreal forest (taiga)", "accent": "#456f5a",
    },
    "tundra": {
        "sky": "#e7f1f5", "floor": "#f8fafc",
        "label": "Arctic tundra", "accent": "#a4c6d4",
    },
    "savanna": {
        "sky": "#f7d56e", "floor": "#c69a4d",
        "label": "African savanna", "accent": "#a36a2e",
    },
    "tropical_rainforest": {
        "sky": "#86b97a", "floor": "#1d3a26",
        "label": "Tropical rainforest", "accent": "#3a7a3a",
    },
    "desert": {
        "sky": "#fde8c5", "floor": "#e2a35a",
        "label": "Hot desert", "accent": "#b5642a",
    },
    "grassland": {
        "sky": "#f4eab1", "floor": "#9bb24c",
        "label": "Temperate grassland", "accent": "#647b2c",
    },
    "kelp_forest": {
        "sky": "#3d7da6", "floor": "#0f3d52",
        "label": "Kelp forest", "accent": "#2f9f7a",
    },
    "coral_reef": {
        "sky": "#4fb9d6", "floor": "#0b6079",
        "label": "Coral reef", "accent": "#f08a7a",
    },
    "mangrove": {
        "sky": "#9fc4a8", "floor": "#3d5037",
        "label": "Mangrove forest", "accent": "#6f8a5b",
    },
    "freshwater_lake": {
        "sky": "#a9d7e8", "floor": "#1f4d6b",
        "label": "Freshwater lake", "accent": "#4c8aa8",
    },
    "yellowstone": {
        "sky": "#b8d4d6", "floor": "#3d5a3e",
        "label": "Yellowstone-style", "accent": "#5d7e4a",
    },
}

_DEFAULT_THEME = {
    "sky": "#d4e2e7", "floor": "#4a6c4a",
    "label": "Biome", "accent": "#3a7a3a",
}


# Decorative scenery glyphs per biome — drawn STATIC behind the moving fauna
# so the scene reads even when populations are tiny.
_SCENERY: dict[str, list[tuple[str, float]]] = {
    "temperate_forest": [("🌳", 0.4), ("🌲", 0.5), ("🍂", 0.85)],
    "boreal_forest": [("🌲", 0.4), ("🌲", 0.55), ("❄️", 0.2)],
    "tundra": [("❄️", 0.2), ("🏔️", 0.55), ("❄️", 0.35)],
    "savanna": [("🌳", 0.45), ("🌾", 0.78), ("☀️", 0.15)],
    "tropical_rainforest": [("🌴", 0.45), ("🌿", 0.8), ("🌺", 0.62)],
    "desert": [("🌵", 0.55), ("🪨", 0.85), ("☀️", 0.12)],
    "grassland": [("🌾", 0.78), ("🌾", 0.72), ("☁️", 0.2)],
    "kelp_forest": [("🌿", 0.45), ("🌿", 0.6), ("🫧", 0.3)],
    "coral_reef": [("🪸", 0.7), ("🪸", 0.78), ("🫧", 0.25)],
    "mangrove": [("🌳", 0.5), ("🌊", 0.82), ("🌿", 0.7)],
    "freshwater_lake": [("🌊", 0.78), ("🌿", 0.7), ("☁️", 0.18)],
    "yellowstone": [("🏔️", 0.5), ("🌲", 0.6), ("🌳", 0.7)],
}


def biome_theater_height() -> int:
    """Recommended iframe height for the theater hero."""
    return 360


def _count_for_pop(pop: float) -> int:
    """Map a population to a creature count between 1 and 5.

    Uses log scaling so a wolf at 30 doesn't show 30 wolves but a small pack,
    while an elk herd at 800 fills the meadow."""
    if pop <= 0:
        return 0
    n = int(math.log1p(max(0.0, pop)) / math.log(6.0))
    return max(1, min(5, n))


def _scatter_positions(n: int, rng: _random.Random) -> list[tuple[float, float]]:
    """Return n (x%, y%) positions that are reasonably spread out.

    Uses jittered grid placement so creatures don't all stack on top of each
    other for high counts."""
    if n <= 0:
        return []
    cols = max(1, math.ceil(math.sqrt(n * 1.6)))
    rows = max(1, math.ceil(n / cols))
    out: list[tuple[float, float]] = []
    cell_w = 100.0 / cols
    cell_h = 100.0 / rows
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)
    for (c, r) in cells[:n]:
        x = (c + 0.5) * cell_w + rng.uniform(-cell_w * 0.25, cell_w * 0.25)
        y = (r + 0.5) * cell_h + rng.uniform(-cell_h * 0.18, cell_h * 0.18)
        out.append((max(2.0, min(98.0, x)), max(8.0, min(92.0, y))))
    return out


def _is_aquatic_biome(biome_id: str) -> bool:
    return biome_id in {"kelp_forest", "coral_reef", "freshwater_lake", "mangrove"}


def render_biome_theater(
    biome_id: str,
    species_records: list[dict],
    final_pops: dict[str, float],
    *,
    caption: str = "",
    dramatic: str = "",
    seed: int = 0,
) -> str:
    """Return a self-contained HTML string for the biome theater hero.

    Parameters
    ----------
    biome_id
        The biome id (must match an entry in :data:`_BIOME_THEMES`; falls
        back to a neutral palette otherwise).
    species_records
        Records from ``species.json`` for each species in the scene. Each
        needs an ``"id"``, ``"common_name"`` and ``"emoji"`` (defaults to
        ``"•"`` if missing).
    final_pops
        Map of species_id → final simulated population. Controls how many
        creatures of each species appear.
    caption
        Short overlay caption (≤ 12 words).
    dramatic
        One vivid sentence about the moment to notice.
    seed
        Deterministic placement seed so the same inputs produce the same scene.
    """
    theme = _BIOME_THEMES.get(biome_id, _DEFAULT_THEME)
    sky = theme["sky"]
    floor = theme["floor"]
    accent = theme["accent"]
    biome_label = theme["label"]

    rng = _random.Random(seed or hash(biome_id) & 0xFFFFFFFF)

    # ---- Static scenery (background) -------------------------------------
    scenery_html_parts: list[str] = []
    for i, (glyph, y_pct) in enumerate(_SCENERY.get(biome_id, _SCENERY["temperate_forest"])):
        # Spread scenery across the width.
        x_pct = (i + 0.5) * 100.0 / max(1, len(_SCENERY.get(biome_id, [glyph])))
        size = 38 + (i % 2) * 8
        scenery_html_parts.append(
            f"<div class='eco-scenery' style='left:{x_pct:.1f}%; top:{y_pct * 100:.1f}%;"
            f"font-size:{size}px;'>{glyph}</div>"
        )
    scenery_html = "".join(scenery_html_parts)

    # ---- Fauna (animated creatures) --------------------------------------
    fauna_html_parts: list[str] = []
    aquatic = _is_aquatic_biome(biome_id)
    for sp in species_records:
        sid = sp.get("id", "")
        glyph = sp.get("emoji") or "•"
        name = sp.get("common_name", sid)
        pop = float(final_pops.get(sid, 0.0))
        n = _count_for_pop(pop)
        if n == 0:
            # Extirpated → fading ghost glyph in the corner so it's visible
            # the species was here but vanished.
            fauna_html_parts.append(
                f"<div class='eco-faded' style='left:{rng.uniform(10, 90):.1f}%;"
                f"top:{rng.uniform(55, 80):.1f}%;' title='{_html.escape(name)} — extirpated'>"
                f"{glyph}</div>"
            )
            continue
        positions = _scatter_positions(n, rng)
        for (x_pct, y_pct) in positions:
            # Per-creature animation: 4-12 s bob/drift, randomized so the
            # crowd doesn't move in sync.
            dur = rng.uniform(4.0, 12.0)
            delay = rng.uniform(-dur, 0.0)
            drift_x = rng.uniform(-12.0, 12.0)
            drift_y = rng.uniform(-8.0, 8.0)
            anim = "eco-swim" if aquatic else "eco-bob"
            font_px = rng.randint(26, 38)
            fauna_html_parts.append(
                f"<div class='eco-fauna' "
                f"style='left:{x_pct:.1f}%; top:{y_pct:.1f}%; font-size:{font_px}px;"
                f"--dx:{drift_x:.1f}px; --dy:{drift_y:.1f}px;"
                f"animation:{anim} {dur:.1f}s ease-in-out {delay:.1f}s infinite;'"
                f" title='{_html.escape(name)} (pop ≈ {int(pop)})'>{glyph}</div>"
            )
    fauna_html = "".join(fauna_html_parts)

    # ---- Caption + dramatic-moment overlays ------------------------------
    caption_html = (
        f"<div class='eco-caption'>{_html.escape(caption)}</div>"
        if caption else ""
    )
    dramatic_html = (
        f"<div class='eco-moment'><span>🎬</span> {_html.escape(dramatic)}</div>"
        if dramatic else ""
    )

    return f"""<style>{_THEATER_CSS}</style>
<div class='eco-theater' style='--sky:{sky}; --floor:{floor}; --accent:{accent};'>
  <div class='eco-biome-badge'>{_html.escape(biome_label)}</div>
  <div class='eco-sky'></div>
  <div class='eco-floor'></div>
  {scenery_html}
  {fauna_html}
  {caption_html}
  {dramatic_html}
</div>
"""


_THEATER_CSS = r"""
.eco-theater {
  position: relative;
  width: 100%;
  height: 340px;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 14px rgba(0,0,0,0.18);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.eco-sky {
  position: absolute; inset: 0 0 30% 0;
  background: linear-gradient(180deg, var(--sky) 0%, color-mix(in srgb, var(--sky) 60%, white) 100%);
}
.eco-floor {
  position: absolute; left: 0; right: 0; bottom: 0; height: 35%;
  background: linear-gradient(180deg, color-mix(in srgb, var(--floor) 80%, var(--sky)) 0%, var(--floor) 100%);
  box-shadow: 0 -3px 10px rgba(0,0,0,0.18) inset;
}
.eco-biome-badge {
  position: absolute; top: 10px; left: 12px;
  background: rgba(255,255,255,0.78); color: #1a1a1a;
  padding: 4px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600; letter-spacing: 0.02em;
  z-index: 5;
}
.eco-scenery {
  position: absolute; transform: translate(-50%, -50%);
  opacity: 0.85;
  z-index: 1;
  user-select: none;
  pointer-events: none;
}
.eco-fauna {
  position: absolute; transform: translate(-50%, -50%);
  z-index: 3;
  user-select: none;
  cursor: help;
  text-shadow: 0 2px 3px rgba(0,0,0,0.25);
}
.eco-faded {
  position: absolute; transform: translate(-50%, -50%);
  z-index: 2;
  font-size: 26px;
  opacity: 0.18;
  filter: grayscale(1);
}
@keyframes eco-bob {
  0%   { transform: translate(calc(-50% + 0px),       calc(-50% + 0px))       rotate(0deg); }
  50%  { transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy))) rotate(-3deg); }
  100% { transform: translate(calc(-50% + 0px),       calc(-50% + 0px))       rotate(0deg); }
}
@keyframes eco-swim {
  0%   { transform: translate(calc(-50% + 0px),                 calc(-50% + 0px)) scaleX(1); }
  25%  { transform: translate(calc(-50% + var(--dx)),           calc(-50% + var(--dy) * -0.5)) scaleX(1); }
  50%  { transform: translate(calc(-50% + var(--dx) * 1.4),     calc(-50% + var(--dy))) scaleX(-1); }
  75%  { transform: translate(calc(-50% + var(--dx) * 0.6),     calc(-50% + var(--dy) * 0.5)) scaleX(-1); }
  100% { transform: translate(calc(-50% + 0px),                 calc(-50% + 0px)) scaleX(1); }
}
.eco-caption {
  position: absolute; bottom: 12px; left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 224, 130, 0.95); color: #3a2a00;
  padding: 6px 14px; border-radius: 999px;
  font-size: 13px; font-weight: 600;
  max-width: 90%; text-align: center;
  z-index: 6;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.eco-moment {
  position: absolute; top: 10px; right: 12px;
  background: rgba(16, 185, 129, 0.92); color: white;
  padding: 6px 12px; border-radius: 10px;
  font-size: 12px; font-weight: 500;
  max-width: 60%;
  z-index: 6;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  display: flex; gap: 6px; align-items: center;
}
.eco-moment span { font-size: 14px; }
"""
