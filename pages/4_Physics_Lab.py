"""Physics Lab — high-school mechanics + intro modern physics."""

from __future__ import annotations

import json as _json
import math

import streamlit as st

from curious_mind import llm, ui
from curious_mind.persistence import render_persistence_sidebar
from curious_mind.physics import data_loader, prompts, simulators, visuals
from curious_mind.physics.schemas import PhysicsResult


ui.page_setup("Physics Lab", "🔬")
ui.header("🔬 Physics Lab", crumb="Curious Minds · Physics")

# Hide Streamlit's per-chart fullscreen button — same fix as Ecosystem Lab,
# so animation Play/Restart don't break after a fullscreen round-trip.
st.markdown(
    "<style>button[title='View fullscreen']{display:none;}</style>",
    unsafe_allow_html=True,
)

if not llm.have_api_key():
    ui.offline_banner()


SCENARIOS = [
    ("projectile", "🎯 Projectile motion"),
    ("incline", "⛰️ Inclined plane + friction"),
    ("rollercoaster", "🎢 Energy conservation (rollercoaster)"),
    ("collision", "💥 2-D collision"),
    ("spring", "🌀 Spring SHM"),
    ("photoelectric", "💡 Photoelectric effect"),
    ("de_broglie", "🌊 Wave–particle duality"),
]
SCENARIO_LABELS = dict(SCENARIOS)


def _default_inputs() -> dict:
    return {
        "scenario": "projectile",
        # Projectile
        "v0": 25.0, "angle_deg": 45.0, "g": 9.81, "y0": 0.0,
        # Incline
        "incline_mass": 5.0, "incline_angle": 30.0,
        "incline_material": "wood_wood", "incline_f_applied": 0.0,
        # Rollercoaster
        "rc_h0": 30.0, "rc_h1": 18.0, "rc_h2": 25.0,
        "rc_mu_k": 0.05, "rc_mass": 100.0,
        # Collision (2D, up to 5 disks on a bounded square plane)
        "col_n": 2,
        "col_masses": [1.0, 1.0, 1.5, 1.0, 0.8],
        "col_vxs": [3.0, -2.0, 0.5, -0.3, -1.0],
        "col_vzs": [0.0, 0.5, -1.5, 1.5, -1.0],
        "col_type": "elastic",   # elastic | partial | plastic
        "col_e": 0.6,            # only used when type == "partial"
        "col_mu_k": 0.0,         # kinetic friction with the plane (0 = ideal)
        "col_plane_x": 10.0,     # half-width  of the rectangular plane (m)
        "col_plane_z": 6.0,      # half-depth  of the rectangular plane (m)
        # Spring
        "spring_m": 1.0, "spring_k": 20.0, "spring_x0": 0.1, "spring_v0": 0.0,
        # Photoelectric
        "pe_metal": "sodium", "pe_freq_hz": 7.0e14, "pe_intensity_rel": 1.0,
        # de Broglie / double-slit
        "db_particle": "electron", "db_v_mps": 2.0e6,
        "db_d_nm": 100.0,        # slit separation in nm
        "db_L_m": 1.0,           # slit-to-screen distance in m
    }


if "phy_inputs" not in st.session_state:
    st.session_state.phy_inputs = _default_inputs()
else:
    for k, v in _default_inputs().items():
        st.session_state.phy_inputs.setdefault(k, v)


# ---------------------------------------------------------------------------
# Sidebar — scenario picker + per-scenario sliders
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Scenario")
    scenario = st.selectbox(
        "Pick a scenario",
        options=[s[0] for s in SCENARIOS],
        index=[s[0] for s in SCENARIOS].index(st.session_state.phy_inputs["scenario"]),
        format_func=lambda s: SCENARIO_LABELS[s],
        help="One scenario at a time. Switch any time — your other settings are kept.",
    )
    st.session_state.phy_inputs["scenario"] = scenario

    inp = st.session_state.phy_inputs

    if scenario == "projectile":
        st.markdown("### Launch")
        inp["v0"] = st.slider("Initial speed v₀ (m/s)", 1.0, 100.0,
                              float(inp["v0"]), 1.0,
                              help="Speed at launch. 25 m/s ≈ a major-league fastball.")
        inp["angle_deg"] = st.slider("Launch angle θ (°)", 0.0, 90.0,
                                     float(inp["angle_deg"]), 1.0,
                                     help="Angle above horizontal. 45° gives max range "
                                          "from ground level.")
        inp["g"] = st.slider("Gravity g (m/s²)", 1.0, 30.0,
                             float(inp["g"]), 0.1,
                             help="Earth = 9.81 · Moon = 1.62 · Mars = 3.71 · Jupiter = 24.79.")
        inp["y0"] = st.slider("Launch height y₀ (m)", 0.0, 100.0,
                              float(inp["y0"]), 1.0,
                              help="Height of the launch point above ground.")

    elif scenario == "incline":
        st.markdown("### Block & slope")
        inp["incline_mass"] = st.slider("Mass m (kg)", 0.1, 100.0,
                                        float(inp["incline_mass"]), 0.1)
        inp["incline_angle"] = st.slider("Slope angle θ (°)", 0.0, 75.0,
                                         float(inp["incline_angle"]), 1.0)
        materials = data_loader.load_materials()
        mat_ids = [m["id"] for m in materials]
        cur_mat = inp["incline_material"] if inp["incline_material"] in mat_ids else mat_ids[0]
        inp["incline_material"] = st.selectbox(
            "Surface pair", options=mat_ids,
            index=mat_ids.index(cur_mat),
            format_func=lambda mid: data_loader.material_by_id(mid)["name"],
            help="Sets μₛ (static) and μₖ (kinetic) friction coefficients.",
        )
        mat = data_loader.material_by_id(inp["incline_material"])
        st.caption(f"μₛ = {mat['mu_s']:.2f} · μₖ = {mat['mu_k']:.2f}")
        inp["incline_f_applied"] = st.slider(
            "Applied force along slope (N, + = up)",
            -500.0, 500.0, float(inp["incline_f_applied"]), 5.0,
            help="External push parallel to the slope. Positive = up the slope.",
        )

    elif scenario == "rollercoaster":
        st.markdown("### Track heights")
        inp["rc_h0"] = st.slider("Start height h₀ (m)", 1.0, 100.0,
                                 float(inp["rc_h0"]), 1.0,
                                 help="The cart starts here at rest.")
        inp["rc_h1"] = st.slider("Hill 1 height (m)", 0.0, 100.0,
                                 float(inp["rc_h1"]), 1.0)
        inp["rc_h2"] = st.slider("Hill 2 height (m)", 0.0, 100.0,
                                 float(inp["rc_h2"]), 1.0)
        inp["rc_mu_k"] = st.slider("Track friction μₖ", 0.0, 0.5,
                                   float(inp["rc_mu_k"]), 0.01,
                                   help="0 = frictionless ideal track. 0.05 ≈ steel wheels on steel rail.")
        inp["rc_mass"] = st.slider("Cart mass (kg)", 10.0, 1000.0,
                                   float(inp["rc_mass"]), 10.0)

    elif scenario == "collision":
        st.markdown("### Disks on a bounded 2-D plane")
        inp["col_n"] = st.slider(
            "Number of disks", 2, 5, int(inp["col_n"]), 1,
            help="Add up to 5 disks. Initial positions are spaced evenly "
                 "around a circle inside the plane.",
        )
        cw, cd = st.columns(2)
        with cw:
            inp["col_plane_x"] = st.slider(
                "Plane half-width (m)", 4.0, 16.0,
                float(inp["col_plane_x"]), 0.5,
                help="Plane spans ±this in x (horizontal axis). Walls bounce "
                     "disks back elastically.",
            )
        with cd:
            inp["col_plane_z"] = st.slider(
                "Plane half-depth (m)", 3.0, 12.0,
                float(inp["col_plane_z"]), 0.5,
                help="Plane spans ±this in z (vertical axis on the top view).",
            )
        inp["col_mu_k"] = st.slider(
            "Friction with plane μₖ", 0.0, 0.5, float(inp["col_mu_k"]), 0.01,
            help="0 = ideal frictionless plane (motion never stops). "
                 "Higher = disks coast to rest faster.",
        )
        inp["col_type"] = st.radio(
            "Collision type",
            options=["elastic", "partial", "plastic"],
            index=["elastic", "partial", "plastic"].index(
                inp["col_type"] if inp["col_type"] in ("elastic", "partial", "plastic") else "elastic"
            ),
            format_func=lambda t: {
                "elastic": "Elastic (e = 1, perfect bounce)",
                "partial": "Partial bounce (set e below)",
                "plastic": "Plastic (sticking pairs)",
            }[t],
            help="Elastic conserves KE between disks. Plastic merges each "
                 "colliding pair into the same velocity.",
        )
        if inp["col_type"] == "partial":
            inp["col_e"] = st.slider("Restitution e", 0.05, 0.95,
                                     float(inp["col_e"]), 0.05,
                                     help="0 = perfectly inelastic, 1 = perfectly elastic.")
        st.markdown("**Per-disk mass and velocity**")
        # Make sure the lists are long enough (in case an older preset loaded).
        for key in ("col_masses", "col_vxs", "col_vzs"):
            while len(inp[key]) < 5:
                inp[key].append(1.0 if key == "col_masses" else 0.0)
        for i in range(int(inp["col_n"])):
            with st.expander(f"Disk {i+1}", expanded=(i < 2)):
                inp["col_masses"][i] = st.slider(
                    f"m{i+1} (kg)", 0.1, 10.0,
                    float(inp["col_masses"][i]), 0.1, key=f"col_m_{i}",
                )
                ca, cb = st.columns(2)
                with ca:
                    inp["col_vxs"][i] = st.slider(
                        f"v{i+1}ₓ (m/s)", -6.0, 6.0,
                        float(inp["col_vxs"][i]), 0.1, key=f"col_vx_{i}",
                        help="Positive = moving in +x.",
                    )
                with cb:
                    inp["col_vzs"][i] = st.slider(
                        f"v{i+1}_z (m/s)", -6.0, 6.0,
                        float(inp["col_vzs"][i]), 0.1, key=f"col_vz_{i}",
                        help="Positive = moving in +z. (Top view — z is in-plane.)",
                    )

    elif scenario == "spring":
        st.markdown("### Mass on a spring")
        inp["spring_m"] = st.slider("Mass m (kg)", 0.05, 10.0,
                                    float(inp["spring_m"]), 0.05)
        inp["spring_k"] = st.slider("Spring constant k (N/m)", 1.0, 200.0,
                                    float(inp["spring_k"]), 1.0,
                                    help="Stiffness. Higher = faster oscillation.")
        inp["spring_x0"] = st.slider("Initial displacement x₀ (m)", -0.5, 0.5,
                                     float(inp["spring_x0"]), 0.01,
                                     help="Stretch (+) or compression (−) at t = 0.")
        inp["spring_v0"] = st.slider("Initial velocity v₀ (m/s)", -2.0, 2.0,
                                     float(inp["spring_v0"]), 0.05)

    elif scenario == "photoelectric":
        st.markdown("### Light & metal")
        metals = data_loader.load_metals()
        mids = [m["id"] for m in metals]
        cur = inp["pe_metal"] if inp["pe_metal"] in mids else mids[0]
        inp["pe_metal"] = st.selectbox(
            "Metal target", options=mids,
            index=mids.index(cur),
            format_func=lambda mid: data_loader.metal_by_id(mid)["name"],
            help="Each metal has a different work function φ — the energy needed to free an electron.",
        )
        metal = data_loader.metal_by_id(inp["pe_metal"])
        st.caption(f"φ = {metal['work_function_eV']:.2f} eV")
        # Frequency in 10^14 Hz units to make the slider readable.
        f_units = st.slider(
            "Frequency f (×10¹⁴ Hz)",
            1.0, 25.0, float(inp["pe_freq_hz"]) / 1e14, 0.1,
            help="4.3 ≈ red light · 5.5 ≈ green · 7.5 ≈ violet · 10+ = UV.",
        )
        inp["pe_freq_hz"] = f_units * 1e14
        inp["pe_intensity_rel"] = st.slider(
            "Light intensity (relative)", 0.0, 5.0,
            float(inp["pe_intensity_rel"]), 0.1,
            help="More photons per second — affects current, not per-electron energy.",
        )

    elif scenario == "de_broglie":
        st.markdown("### Particle & speed")
        particles = data_loader.load_particles()
        pids = [p["id"] for p in particles]
        cur = inp["db_particle"] if inp["db_particle"] in pids else pids[0]
        inp["db_particle"] = st.selectbox(
            "Particle", options=pids,
            index=pids.index(cur),
            format_func=lambda pid: data_loader.particle_by_id(pid)["name"],
        )
        particle = data_loader.particle_by_id(inp["db_particle"])
        st.caption(f"Mass = {particle['mass_kg']:.3e} kg")
        # Log slider over many decades
        v_log = st.slider(
            "Speed v (log₁₀ m/s)", -2.0, 8.5,
            float(math.log10(max(inp["db_v_mps"], 1e-2))), 0.1,
            help="Very wide range: walking (~1 m/s) → near light speed (3·10⁸ m/s).",
        )
        inp["db_v_mps"] = 10.0 ** v_log

        st.markdown("### Double-slit setup")
        inp["db_d_nm"] = st.slider(
            "Slit separation d (nm)", 10.0, 10000.0,
            float(inp["db_d_nm"]), 10.0,
            help="Distance between the two slits. Smaller d → wider fringes.",
        )
        inp["db_L_m"] = st.slider(
            "Slit-to-screen distance L (m)", 0.1, 5.0,
            float(inp["db_L_m"]), 0.1,
            help="Distance from the slits to the detector. Larger L → wider fringes.",
        )

    st.divider()
    loaded = render_persistence_sidebar(
        "physics", inp, title_default=SCENARIO_LABELS[scenario],
    )
    if loaded:
        st.session_state.phy_inputs = {**_default_inputs(), **loaded}
        st.rerun()

    run_btn = st.button("⚡ Run scenario", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Main canvas
# ---------------------------------------------------------------------------
inp = st.session_state.phy_inputs
scenario = inp["scenario"]
C = 2.99792458e8


def _payload_and_render() -> tuple[dict, dict, str]:
    """Compute the deterministic result, render scenario visuals & metrics,
    return (computed_dict, payload_dict, narrative_subheader)."""

    if scenario == "projectile":
        sim = simulators.projectile(inp["v0"], inp["angle_deg"], inp["g"], inp["y0"])
        st.subheader(
            "🎯 Trajectory",
            help="Parabolic path under constant gravity. The orange dot marks the apex; "
                 "the red dot marks where it lands. Press ▶ Play to animate the projectile.",
        )
        st.plotly_chart(visuals.projectile_figure(sim, inp["v0"], inp["angle_deg"]),
                        use_container_width=True)
        cols = st.columns(4)
        cols[0].metric("Range", f"{sim['range_m']:.1f} m",
                       help="Horizontal distance travelled before landing.")
        cols[1].metric("Max height", f"{sim['max_height_m']:.1f} m",
                       help="Peak height above ground.")
        cols[2].metric("Time of flight", f"{sim['t_flight_s']:.2f} s",
                       help="Duration from launch to landing.")
        cols[3].metric("vₓ / v_y at launch",
                       f"{sim['vx']:.1f} / {sim['vy']:.1f} m/s",
                       help="Horizontal and vertical components of v₀.")
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "Standard 2-D kinematics, no air resistance:\n"
                "- vₓ = v₀·cos(θ), v_y = v₀·sin(θ)\n"
                "- y(t) = y₀ + v_y·t − ½·g·t²; landing time from quadratic\n"
                "- range = vₓ · t_flight, max height = y₀ + v_y² / (2g)"
            )
        if inp["v0"] > 1000.0:
            ui.warn_panel("⚠️ Above ~1000 m/s, air drag dominates — the no-drag model "
                          "overestimates range significantly.")
        return sim, {"computed": sim, "inputs": {
            "v0_mps": inp["v0"], "angle_deg": inp["angle_deg"],
            "g_m_s2": inp["g"], "y0_m": inp["y0"],
        }}, "Why this happens"

    elif scenario == "incline":
        mat = data_loader.material_by_id(inp["incline_material"])
        sim = simulators.inclined_plane(
            inp["incline_mass"], inp["incline_angle"],
            mat["mu_s"], mat["mu_k"], inp["incline_f_applied"],
        )
        st.subheader(
            "⛰️ Free-body diagram",
            help="The four forces on the block: gravity (down), normal (perpendicular "
                 "to slope), friction (along slope, direction set by motion), and any "
                 "applied force you set with the slider. Arrow lengths scale with magnitude.",
        )
        st.plotly_chart(visuals.incline_figure(sim, inp["incline_angle"]),
                        use_container_width=True)
        cols = st.columns(4)
        verdict_short = {
            "static": "🟰 Static",
            "accelerating_up": "↗ Slides up",
            "accelerating_down": "↘ Slides down",
        }.get(sim["verdict"], sim["verdict"])
        cols[0].metric("Verdict", verdict_short,
                       help="Static = won't slip · Slides up/down = kinetic motion.")
        cols[1].metric("Acceleration", f"{sim['accel_m_s2']:+.2f} m/s²",
                       help="Positive = up the slope, negative = down.")
        cols[2].metric("Normal force", f"{sim['f_normal_N']:.1f} N",
                       help="m·g·cos(θ).")
        cols[3].metric("Friction", f"{sim['friction_N']:+.1f} N",
                       help="Whatever's needed to prevent slipping (≤ μₛ·N), or "
                            "−sign(motion)·μₖ·N when sliding.")
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "Resolve gravity into slope-parallel and slope-perpendicular pieces, "
                "then check the static-friction limit:\n"
                "- Weight = m·g\n"
                "- f_grav_parallel = m·g·sin(θ), N = m·g·cos(θ)\n"
                "- Net non-friction along slope: f_drive = f_applied − m·g·sin(θ)\n"
                "- If |f_drive| ≤ μₛ·N → static; else slides with friction = μₖ·N opposing motion\n"
                "- a = (f_drive + friction) / m"
            )
        return sim, {"computed": sim, "inputs": {
            "mass_kg": inp["incline_mass"], "angle_deg": inp["incline_angle"],
            "mu_s": mat["mu_s"], "mu_k": mat["mu_k"],
            "f_applied_N": inp["incline_f_applied"],
            "material": mat["name"],
        }}, "Why this happens"

    elif scenario == "rollercoaster":
        sim = simulators.rollercoaster(
            inp["rc_h0"], inp["rc_h1"], inp["rc_h2"],
            inp["rc_mu_k"], inp["rc_mass"],
        )
        st.subheader(
            "🎢 Track + energy",
            help="Track height across waypoints with PE and KE bars. Green dots = "
                 "reachable, red dots = not enough energy after friction. PE shrinks "
                 "with height; KE picks up the slack until friction eats too much.",
        )
        st.plotly_chart(visuals.rollercoaster_figure(sim), use_container_width=True)
        # Metrics: speed at end + how much energy lost
        ke_end = sim["ke_J"][-1]
        v_end = (2 * ke_end / sim["mass_kg"]) ** 0.5 if ke_end > 0 else 0.0
        total_loss = sim["cumulative_loss_J"][-1]
        cols = st.columns(3)
        cols[0].metric("Speed at end", f"{v_end:.1f} m/s",
                       help="From ½·m·v² = KE remaining.")
        cols[1].metric("Energy lost to friction", f"{total_loss:.0f} J",
                       help="Cumulative across all segments.")
        cols[2].metric("Reaches end?",
                       "Yes" if all(sim["reachable"]) else "No",
                       help="Some hill might be higher than the budget allows.")
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "Conservation of energy with a friction sink:\n"
                "- Start with PE₀ = m·g·h₀ at rest (KE₀ = 0)\n"
                "- At each waypoint: KE = PE₀ − PE − cumulative friction loss\n"
                "- Friction loss per segment ≈ μₖ·m·g·L, with L = 30 m by default\n"
                "- If KE < 0, the cart can't reach that point"
            )
        if not all(sim["reachable"]):
            ui.warn_panel("⚠️ The cart runs out of energy before reaching every waypoint. "
                          "Try lowering μₖ or one of the hills.")
        return sim, {"computed": sim, "inputs": {
            "h0_m": inp["rc_h0"], "h1_m": inp["rc_h1"], "h2_m": inp["rc_h2"],
            "mu_k": inp["rc_mu_k"], "mass_kg": inp["rc_mass"],
        }}, "Why this happens"

    elif scenario == "collision":
        # Map the collision-type radio to (e, plastic) for the simulator.
        ctype = inp["col_type"]
        if ctype == "elastic":
            e_used, plastic_used = 1.0, False
        elif ctype == "plastic":
            e_used, plastic_used = 0.0, True
        else:  # partial
            e_used, plastic_used = float(inp["col_e"]), False

        # Initial layout: put 2 disks face-to-face on the x-axis so the
        # default vx signs aim them at each other; place 3+ disks evenly
        # on an ellipse fitted inside the plane rectangle.
        n_disks = int(inp["col_n"])
        Lx = float(inp["col_plane_x"])
        Lz = float(inp["col_plane_z"])
        rx = 0.62 * Lx
        rz = 0.62 * Lz
        if n_disks == 2:
            positions = [(-rx, 0.0), (+rx, 0.0)]
        else:
            positions = [
                (rx * math.cos(2 * math.pi * i / n_disks),
                 rz * math.sin(2 * math.pi * i / n_disks))
                for i in range(n_disks)
            ]
        disks = []
        for i in range(n_disks):
            disks.append({
                "m":  float(inp["col_masses"][i]),
                "x":  positions[i][0],
                "z":  positions[i][1],
                "vx": float(inp["col_vxs"][i]),
                "vz": float(inp["col_vzs"][i]),
            })

        sim = simulators.collision_multi(
            disks, e=e_used, plastic=plastic_used,
            mu_k=float(inp["col_mu_k"]),
            plane_half_x=Lx, plane_half_z=Lz,
        )

        st.subheader(
            "💥 2-D collisions on a bounded plane",
            help="Top view of up to five disks moving on a frictional or "
                 "frictionless square plane with reflective walls. Disks "
                 "never pass through each other; pairs that touch follow "
                 "the line-of-centres restitution rule.",
        )
        st.plotly_chart(visuals.collision_2d_figure(sim),
                        use_container_width=True)
        if sim["n_collisions"] == 0 and sim["n_wall_hits"] == 0:
            ui.warn_panel("ℹ️ Nothing collides with these velocities. Try "
                          "aiming the disks toward each other or reducing the "
                          "plane size.")

        st.subheader(
            "➡️ Conservation of momentum",
            help="Head-to-tail vector addition. With μₖ = 0 and no wall hits, "
                 "the navy total-momentum arrow is the SAME in both panels — "
                 "that is momentum conservation. Walls and friction can change "
                 "the total because they apply outside forces on the system.",
        )
        if sim["momentum_conserved"]:
            ui.info_panel(
                "<b>How to read this chart.</b> Each disk has a momentum vector "
                "<b>pᵢ = mᵢ·vᵢ</b>. They are drawn <b>head-to-tail</b> in the colour "
                "of their disk. The navy arrow from the origin to the chain's "
                "tip is the <b>total momentum p = Σ pᵢ</b>. With no friction and "
                "no wall hits the navy arrow is <b>identical</b> in both panels — "
                "the visual proof of momentum conservation."
            )
        else:
            note_bits = []
            if sim["n_wall_hits"] > 0:
                note_bits.append(f"the walls bounced disks {sim['n_wall_hits']} time(s)")
            if sim["mu_k"] > 0:
                note_bits.append(f"friction μₖ = {sim['mu_k']:.2f} bled energy off")
            ui.warn_panel(
                "ℹ️ <b>Momentum is no longer conserved here.</b> "
                + ", ".join(note_bits).capitalize() + ", and both walls and friction "
                "exert <b>outside forces</b> on the disks. Set μₖ = 0 and avoid wall "
                "hits to see the navy arrow stay identical between the two panels."
            )
        st.plotly_chart(visuals.collision_momentum_figure(sim),
                        use_container_width=True)

        st.subheader(
            "⚡ Energy budget",
            help="Each colour is one disk's KE share. The amber portion is "
                 "energy that left the kinetic account — to deformation, sound, "
                 "or friction with the plane.",
        )
        st.plotly_chart(visuals.collision_energy_figure(sim),
                        use_container_width=True)

        # Metrics row
        cols = st.columns(4)
        cols[0].metric("Disks", str(sim["n"]),
                       help="Number of bodies in the simulation.")
        cols[1].metric("Disk-disk hits", str(sim["n_collisions"]),
                       help="Total number of pair contacts that occurred.")
        cols[2].metric("Wall hits", str(sim["n_wall_hits"]),
                       help="Times any disk reflected off a plane border.")
        cols[3].metric("KE lost", f"{sim['ke_lost']:.2f} J",
                       help="Friction + inelastic deformation. Zero when "
                            "e = 1 and μₖ = 0.")

        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "Multi-body smooth-sphere model on a bounded plane:\n"
                "- Each frame: apply **kinetic friction** "
                "(deceleration a = μₖ·g) to every disk, then drift positions.\n"
                "- **Walls** at ±plane_half reflect each disk elastically "
                "(no energy loss at the wall, but momentum flips sign).\n"
                "- **Pair contacts**: when distance between centres ≤ r_i + r_j, "
                "split overlap by mass, decompose velocities into a "
                "**normal** (line-of-centres, n̂) and **tangent** (t̂) "
                "component.\n"
                "- Tangential components are unchanged (smooth contact).\n"
                "- Normal components follow the 1-D restitution rule:\n"
                "  v_iₙ' = (mᵢvᵢₙ + mⱼvⱼₙ + mⱼ·e·(vⱼₙ − vᵢₙ)) / (mᵢ + mⱼ)\n"
                "- For **plastic** collisions the colliding pair adopts the "
                "pair centre-of-mass velocity (v_CM = (mᵢvᵢ + mⱼvⱼ)/(mᵢ+mⱼ)).\n"
                "- Overlap correction nudges colliding disks apart along n̂ so "
                "they never visually pass through each other."
            )

        # LLM payload
        return sim, {"computed": {
            "n_disks": sim["n"],
            "masses_kg": sim["m"],
            "v_before": [list(v) for v in sim["v_before"]],
            "v_after":  [list(v) for v in sim["v_after"]],
            "p_before": list(sim["p_before"]),
            "p_after":  list(sim["p_after"]),
            "ke_before": sim["ke_before"], "ke_after": sim["ke_after"],
            "ke_lost": sim["ke_lost"],
            "n_collisions": sim["n_collisions"],
            "n_wall_hits": sim["n_wall_hits"],
            "momentum_conserved": sim["momentum_conserved"],
        }, "inputs": {
            "n_disks": n_disks,
            "masses_kg": [float(inp["col_masses"][i]) for i in range(n_disks)],
            "velocities_mps": [
                [float(inp["col_vxs"][i]), float(inp["col_vzs"][i])]
                for i in range(n_disks)
            ],
            "collision_type": ctype,
            "restitution_e": e_used,
            "mu_k": float(inp["col_mu_k"]),
            "plane_half_x_m": Lx,
            "plane_half_z_m": Lz,
        }}, "Why this happens"

    elif scenario == "spring":
        sim = simulators.spring_shm(
            inp["spring_m"], inp["spring_k"], inp["spring_x0"], inp["spring_v0"],
        )
        st.subheader(
            "🌀 Animated mass-on-spring",
            help="Left: the block slides on a frictionless surface, attached "
                 "to a wall by a spring. Right: x(t), v(t), a(t) curves with a "
                 "red time cursor synced to the block. Bottom: kinetic and "
                 "potential energy swap; total stays constant.",
        )
        st.plotly_chart(
            visuals.spring_figure(sim, inp["spring_m"], inp["spring_k"]),
            use_container_width=True,
        )
        cols = st.columns(4)
        cols[0].metric("Period T", f"{sim['period_s']:.3f} s",
                       help="T = 2π·√(m/k). Independent of amplitude.")
        cols[1].metric("Frequency", f"{1.0 / sim['period_s']:.2f} Hz" if sim['period_s'] > 0 else "—")
        cols[2].metric("Amplitude", f"{sim['amplitude_m']:.3f} m",
                       help="Max displacement from equilibrium.")
        cols[3].metric("Total energy",
                       f"{0.5 * inp['spring_k'] * sim['amplitude_m']**2:.3f} J",
                       help="½·k·A². Constant in undamped SHM.")
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "Analytic solution to the SHM equation of motion:\n"
                "- ω = √(k/m), T = 2π/ω\n"
                "- Amplitude from initial conditions: A = √(x₀² + (v₀/ω)²)\n"
                "- x(t) = A·cos(ω·t + φ), v(t) = −A·ω·sin(...), a(t) = −ω²·x\n"
                "- KE = ½·m·v², PE = ½·k·x²; total = ½·k·A²"
            )
        return sim, {"computed": sim, "inputs": {
            "m_kg": inp["spring_m"], "k_N_per_m": inp["spring_k"],
            "x0_m": inp["spring_x0"], "v0_mps": inp["spring_v0"],
        }}, "Why this happens"

    elif scenario == "photoelectric":
        metal = data_loader.metal_by_id(inp["pe_metal"])
        sim = simulators.photoelectric(
            inp["pe_freq_hz"], inp["pe_intensity_rel"], metal["work_function_eV"],
        )
        st.subheader(
            "💡 Animated photoelectric scene",
            help="Photons (colored by frequency) stream in from the left and "
                 "strike the metal target. If hf ≥ φ, an electron flies out "
                 "the other side with KE_max = hf − φ. Intensity controls how "
                 "many photons are in flight, NOT how fast each ejected "
                 "electron moves.",
        )
        st.plotly_chart(visuals.photoelectric_animation(
            sim, inp["pe_freq_hz"], metal["work_function_eV"],
            inp["pe_intensity_rel"],
        ), use_container_width=True)
        st.subheader(
            "📈 KE_max vs frequency",
            help="Einstein's photoelectric equation as a line plot. Below the "
                 "threshold frequency, no electrons are emitted no matter how "
                 "bright the light.",
        )
        st.plotly_chart(visuals.photoelectric_figure(
            sim, inp["pe_freq_hz"], metal["work_function_eV"]
        ), use_container_width=True)
        cols = st.columns(4)
        cols[0].metric("Photon energy", f"{sim['photon_eV']:.2f} eV",
                       help="E = h·f.")
        cols[1].metric("Threshold f₀",
                       f"{sim['threshold_freq_Hz']:.2e} Hz",
                       help="Minimum frequency: φ = h·f₀.")
        cols[2].metric("KE_max", f"{sim['ke_max_eV']:.2f} eV",
                       help="Per-electron energy. Zero below threshold.")
        cols[3].metric("Emits electrons?",
                       "Yes ✅" if sim["emits_electrons"] else "No ❌")
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "Einstein photoelectric equation:\n"
                "- Photon energy E = h·f\n"
                "- Work function φ is the energy to free a surface electron\n"
                "- KE_max = h·f − φ (clipped at 0)\n"
                "- Threshold frequency f₀ = φ / h\n"
                "- Brighter light = more photons = more electrons (current), "
                "but not faster ones"
            )
        if not sim["emits_electrons"]:
            ui.warn_panel("⚠️ Frequency is below threshold for this metal — no "
                          "electrons emitted regardless of intensity. Try violet or UV.")
        return sim, {"computed": sim, "inputs": {
            "frequency_Hz": inp["pe_freq_hz"],
            "intensity_rel": inp["pe_intensity_rel"],
            "metal": metal["name"], "phi_eV": metal["work_function_eV"],
        }}, "Why this happens"

    elif scenario == "de_broglie":
        particle = data_loader.particle_by_id(inp["db_particle"])
        sim = simulators.de_broglie(particle["mass_kg"], inp["db_v_mps"])
        st.subheader(
            "🌊 Animated matter wave",
            help="A travelling sinusoid representing the particle's de Broglie "
                 "wave. The cycles-per-screen are LOG-scaled to true λ so an "
                 "electron and a baseball can both fit on the same canvas — "
                 "the dense wave for a baseball means λ is far below atomic "
                 "scale; a sparse wave means λ ≫ atom.",
        )
        st.plotly_chart(visuals.de_broglie_animation(
            sim, particle["mass_kg"], inp["db_v_mps"], particle["name"]
        ), use_container_width=True)
        st.subheader(
            "📈 λ vs momentum (log-log)",
            help="Matter wavelength λ = h/p plotted across many decades. "
                 "Reference dotted lines mark atomic, light, and macroscopic "
                 "scales for comparison.",
        )
        st.plotly_chart(visuals.de_broglie_figure(
            sim, particle["mass_kg"], inp["db_v_mps"], particle["name"]
        ), use_container_width=True)

        # ---- Young's double-slit ----
        d_m = inp["db_d_nm"] * 1e-9
        L_m = inp["db_L_m"]
        lam = sim["wavelength_m"]
        st.subheader(
            "🪞 Double-slit experiment",
            help="Same particle, sent through a barrier with two narrow slits. "
                 "Each particle is detected at a single point — but after many "
                 "particles, the interference pattern emerges. Fringe spacing "
                 "Δy = λ·L/d is set by the de Broglie wavelength above.",
        )
        if not math.isfinite(lam) or lam <= 0:
            ui.warn_panel("⚠️ v = 0 → λ is infinite — no double-slit pattern "
                          "to compute.")
        else:
            ds = simulators.double_slit(lam, d_m, L_m)
            st.plotly_chart(visuals.double_slit_animation(ds, particle["name"]),
                            use_container_width=True)
            ds_cols = st.columns(3)
            ds_cols[0].metric("Fringe spacing Δy",
                              f"{ds['fringe_spacing_m']:.2e} m",
                              help="Δy = λ·L / d.")
            ds_cols[1].metric("Slit separation d",
                              f"{d_m:.2e} m",
                              help="Distance between the two slits.")
            ds_cols[2].metric("Screen distance L",
                              f"{L_m:.2f} m",
                              help="Distance from slits to detector.")
            with st.expander("ℹ️ How is this computed?"):
                st.markdown(
                    "Two-slit interference (Young, 1801; first done with "
                    "electrons by Davisson & Germer, 1927):\n"
                    "- Fringe spacing: **Δy = λ·L / d**\n"
                    "- Intensity: I(y) = cos²(π·d·y/(λL)) · sinc²(π·a·y/(λL))\n"
                    "  - First factor = two-slit interference\n"
                    "  - Second factor = single-slit diffraction envelope "
                    "(slit width a = d/4 here)\n"
                    "- Particles arrive one at a time at random positions "
                    "drawn from I(y); the pattern emerges only after many\n"
                    "- This is the canonical demonstration of "
                    "**wave–particle duality**: each particle is a discrete "
                    "hit, but the population shows a wave-interference pattern"
                )
        cols = st.columns(3)
        cols[0].metric("Momentum", f"{sim['momentum_kg_m_s']:.2e} kg·m/s")
        lam = sim["wavelength_m"]
        cols[1].metric("Wavelength λ",
                       f"{lam:.2e} m" if not math.isinf(lam) else "∞",
                       help="h / p.")
        v_frac = inp["db_v_mps"] / C
        cols[2].metric("v / c", f"{v_frac:.2e}",
                       help="Above ~0.1, classical p = m·v breaks down.")
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                "de Broglie hypothesis (1924):\n"
                "- Classical momentum p = m·v\n"
                "- Matter wavelength λ = h / p\n"
                "- For everyday objects, λ ≪ atomic spacing → no observable wave behaviour\n"
                "- For electrons at lab speeds, λ ~ 0.1 nm → diffraction is measurable"
            )
        if v_frac > 0.1:
            ui.warn_panel("⚠️ Above 10% of light speed — the classical p = m·v formula "
                          "breaks down. Use relativistic momentum p = γ·m·v for an honest answer.")
        return sim, {"computed": sim, "inputs": {
            "particle": particle["name"], "mass_kg": particle["mass_kg"],
            "v_mps": inp["db_v_mps"], "v_over_c": v_frac,
        }}, "Why this happens"

    return {}, {}, ""


computed, payload_inputs, narrative_subheader = _payload_and_render()


# ---------------------------------------------------------------------------
# LLM narrative
# ---------------------------------------------------------------------------
payload = {
    "scenario_id": scenario,
    "scenario_name": SCENARIO_LABELS[scenario],
    **payload_inputs,
    "user_question": st.session_state.get("phy_user_question"),
}
input_signature = _json.dumps(payload, sort_keys=True, default=str)
should_run = (
    run_btn
    or "phy_last_result" not in st.session_state
    or st.session_state.get("phy_last_signature") != input_signature
    or st.session_state.get("phy_last_scenario") != scenario
)
if should_run:
    with st.spinner("Reasoning over the physics…"):
        result, source = llm.call_structured(
            domain=f"physics_{scenario}",
            system_prompt=prompts.SYSTEM_PROMPT,
            user_payload=payload,
            schema=PhysicsResult,
            fallback=prompts.FALLBACK.get(scenario, prompts.FALLBACK["projectile"]),
            max_tokens=1800,
        )
    st.session_state.phy_last_result = result
    st.session_state.phy_last_source = source
    st.session_state.phy_last_signature = input_signature
    st.session_state.phy_last_scenario = scenario

result: PhysicsResult = st.session_state.phy_last_result
source: str = st.session_state.phy_last_source

ui.source_indicator(source)
if result.confidence == "speculative":
    ui.speculation_banner()

st.subheader(
    "📝 Scenario summary",
    help="Claude's plain-language read on what's happening, citing the computed numbers above.",
)
st.write(result.summary)

if result.intuition:
    st.subheader(
        narrative_subheader or "Intuition",
        help="Why the numbers come out the way they do — the physics in words, not equations.",
    )
    st.write(result.intuition)

# Confidence badge + key concepts row
meta_cols = st.columns([1, 3])
with meta_cols[0]:
    st.markdown("**Confidence**")
    st.markdown(ui.confidence_badge(result.confidence), unsafe_allow_html=True)
with meta_cols[1]:
    if result.key_concepts:
        st.markdown("**Key concepts**")
        st.markdown(" · ".join(f"`{c}`" for c in result.key_concepts))

if result.common_misconceptions:
    st.subheader(
        "🧠 Common misconceptions",
        help="Things that sound right but aren't — surfaced so they can be confronted directly.",
    )
    for m in result.common_misconceptions:
        st.markdown(f"- {m}")

if result.real_world_examples:
    st.subheader(
        "🌍 Real-world examples",
        help="Where this physics shows up outside the textbook.",
    )
    for ex in result.real_world_examples:
        st.markdown(f"- {ex}")

if result.limitations_or_assumptions:
    st.subheader(
        "⚠️ Limitations & assumptions",
        help="What this model deliberately ignores. A good scientist names the simplifications.",
    )
    for lim in result.limitations_or_assumptions:
        st.markdown(f"- {lim}")

clicked = ui.follow_up_buttons(result.follow_ups, "phy")
if clicked:
    st.session_state.phy_user_question = clicked
    st.session_state.pop("phy_last_result", None)
    st.session_state.pop("phy_last_signature", None)
    st.toast(f"Exploring: {clicked}")
    st.rerun()


# ---------------------------------------------------------------------------
# Per-scenario glossary
# ---------------------------------------------------------------------------
GLOSSARY = {
    "projectile": (
        "- **Projectile** — anything launched and then moving only under gravity.\n"
        "- **Range** — horizontal distance from launch to landing.\n"
        "- **Trajectory** — the actual path through space (a parabola, no drag).\n"
        "- **Time of flight** — total airborne time.\n"
        "- **Apex** — highest point of the trajectory.\n"
        "- **Air resistance** — drag force we're ignoring; matters above ~50 m/s.\n"
    ),
    "incline": (
        "- **Normal force (N)** — surface push perpendicular to contact, m·g·cos(θ).\n"
        "- **Static friction (μₛ)** — resists initiation of motion, up to μₛ·N.\n"
        "- **Kinetic friction (μₖ)** — opposes ongoing motion, equals μₖ·N.\n"
        "- **Free-body diagram** — sketch showing every force on the object.\n"
        "- **Newton's 2nd law** — F_net = m·a along each axis.\n"
    ),
    "rollercoaster": (
        "- **Potential energy (PE)** — m·g·h, stored against gravity.\n"
        "- **Kinetic energy (KE)** — ½·m·v², the energy of motion.\n"
        "- **Work-energy theorem** — net work done = change in KE.\n"
        "- **Conservation of energy** — total mechanical energy constant if no friction.\n"
        "- **Friction loss** — work done by friction, removed from mechanical energy.\n"
    ),
    "collision": (
        "- **Momentum (p)** — m·v, a vector. In 2D top view: (pₓ, p_z). "
        "Conserved when no outside forces act — friction with the plane and "
        "wall reflections both count as outside forces.\n"
        "- **Line of centres (n̂)** — at contact, the unit vector from one "
        "disk's centre to the other. The collision impulse acts along this line.\n"
        "- **Tangent direction (t̂)** — perpendicular to n̂. With smooth (frictionless) "
        "contact, the tangential velocity component of each disk doesn't change.\n"
        "- **Coefficient of restitution (e)** — ratio of relative speed after to "
        "relative speed before, measured along n̂.\n"
        "- **Elastic** (e = 1) — KE conserved at the contact; perfect bounce.\n"
        "- **Partial** (0 < e < 1) — some KE lost to heat/sound/deformation.\n"
        "- **Plastic / perfectly inelastic pair** (e = 0, stick) — the colliding "
        "pair adopts the pair centre-of-mass velocity; maximum KE lost.\n"
        "- **Kinetic friction (μₖ)** — bleeds speed off every disk continuously "
        "(decay only, never reverses motion). With μₖ > 0 the disks coast to rest.\n"
        "- **Reflective walls** — perfectly elastic boundaries. They flip the "
        "perpendicular velocity component, so wall hits change a disk's "
        "momentum without changing its speed.\n"
    ),
    "spring": (
        "- **Hooke's law** — F = −k·x; restoring force ∝ displacement.\n"
        "- **Simple harmonic motion (SHM)** — sinusoidal oscillation about equilibrium.\n"
        "- **Period (T)** — 2π·√(m/k); time for one full oscillation.\n"
        "- **Angular frequency (ω)** — √(k/m); rad/s.\n"
        "- **Amplitude (A)** — max displacement; total energy = ½·k·A².\n"
    ),
    "photoelectric": (
        "- **Photon** — discrete packet of light energy E = h·f.\n"
        "- **Work function (φ)** — energy needed to free a surface electron.\n"
        "- **Threshold frequency (f₀)** — φ / h; below this, nothing happens.\n"
        "- **Planck's constant (h)** — 6.626 × 10⁻³⁴ J·s.\n"
        "- **Electronvolt (eV)** — energy unit; 1 eV ≈ 1.6 × 10⁻¹⁹ J.\n"
    ),
    "de_broglie": (
        "- **Matter wave** — every particle has an associated wavelength.\n"
        "- **de Broglie relation** — λ = h / p (Louis de Broglie, 1924).\n"
        "- **Wave–particle duality** — particles arrive as discrete hits but "
        "their statistics follow wave-interference math.\n"
        "- **Young's double-slit** — barrier with two narrow slits; fringe "
        "spacing **Δy = λ·L / d** (slit separation d, screen distance L).\n"
        "- **Davisson–Germer (1927)** — first experimental confirmation of "
        "matter waves, using electrons diffracting off a nickel crystal.\n"
        "- **Single-particle interference** — each individual particle is "
        "detected at ONE point, yet the pattern of many points reproduces the "
        "wave interference pattern (Tonomura, 1989, with electrons).\n"
        "- **Diffraction envelope** — sinc²(π·a·y/(λL)) modulates the fringes; "
        "set by the slit width a, not the slit separation d.\n"
        "- **Relativistic regime** — above ~0.1c, classical p = m·v breaks "
        "down; use p = γ·m·v for an honest answer.\n"
    ),
}

with st.expander("📖 Concepts"):
    st.markdown(GLOSSARY.get(scenario, ""))
