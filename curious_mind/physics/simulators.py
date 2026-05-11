"""Pure deterministic compute layer for the Physics Lab.

Each function takes plain numbers and returns a plain dict — easy to test, easy
to feed into Claude as a payload.
"""

from __future__ import annotations

import math

import numpy as np

from . import data_loader as dl

_C = dl.constant("c")
_H = dl.constant("h")
_EV_TO_J = dl.constant("eV_to_J")


# ---------------------------------------------------------------------------
# 1. Projectile motion (no air resistance)
# ---------------------------------------------------------------------------
def projectile(v0: float, angle_deg: float, g: float, y0: float = 0.0,
               n_points: int = 120) -> dict:
    theta = math.radians(angle_deg)
    vx = v0 * math.cos(theta)
    vy = v0 * math.sin(theta)
    # Solve y(t) = y0 + vy*t - 0.5*g*t^2 = 0 for landing time.
    # Discriminant always non-negative when y0 >= 0.
    if g <= 0:
        return {
            "trajectory_x": [0.0], "trajectory_y": [y0],
            "range_m": 0.0, "max_height_m": y0, "t_flight_s": 0.0,
            "vx": vx, "vy": vy,
        }
    disc = vy * vy + 2 * g * y0
    t_flight = (vy + math.sqrt(disc)) / g if disc >= 0 else 0.0
    t = np.linspace(0.0, t_flight, max(n_points, 2))
    x = vx * t
    y = y0 + vy * t - 0.5 * g * t * t
    # Clip tiny negatives from float drift.
    y = np.maximum(y, 0.0)
    range_m = float(x[-1])
    # Max height analytic: y_max = y0 + vy^2 / (2g) (only if vy > 0).
    max_h = y0 + (vy * vy) / (2 * g) if vy > 0 else y0
    return {
        "trajectory_x": x.tolist(),
        "trajectory_y": y.tolist(),
        "range_m": range_m,
        "max_height_m": float(max_h),
        "t_flight_s": float(t_flight),
        "vx": vx,
        "vy": vy,
    }


# ---------------------------------------------------------------------------
# 2. Inclined plane + friction
# ---------------------------------------------------------------------------
def inclined_plane(mass: float, angle_deg: float, mu_s: float, mu_k: float,
                   f_applied: float = 0.0, g: float = 9.81) -> dict:
    """Block on an incline. Positive ``f_applied`` is up the slope.

    Returns the four constituent forces, the verdict (static / accelerating up
    or down), and the resulting acceleration along the slope (positive = up).
    """
    theta = math.radians(angle_deg)
    weight = mass * g
    f_grav_par = weight * math.sin(theta)   # along slope, pointing down
    f_normal = weight * math.cos(theta)
    max_static = mu_s * f_normal
    kinetic = mu_k * f_normal

    # Net non-friction force along slope (positive = up).
    f_drive = f_applied - f_grav_par

    if abs(f_drive) <= max_static:
        verdict = "static"
        accel = 0.0
        friction = -f_drive  # whatever it takes to balance
    else:
        verdict = "accelerating_up" if f_drive > 0 else "accelerating_down"
        # Kinetic friction opposes motion direction.
        sign_motion = 1.0 if f_drive > 0 else -1.0
        friction = -sign_motion * kinetic
        accel = (f_drive + friction) / mass

    return {
        "weight_N": weight,
        "f_grav_parallel_N": f_grav_par,
        "f_normal_N": f_normal,
        "max_static_friction_N": max_static,
        "kinetic_friction_N": kinetic,
        "f_applied_N": f_applied,
        "friction_N": friction,
        "verdict": verdict,
        "accel_m_s2": accel,
    }


# ---------------------------------------------------------------------------
# 3. Energy conservation along a 3-hill rollercoaster
# ---------------------------------------------------------------------------
def rollercoaster(h0: float, h1: float, h2: float, mu_k: float,
                  mass: float = 50.0, g: float = 9.81,
                  segment_length_m: float = 30.0) -> dict:
    """Cart starts at rest at h0; visits hill heights h1, h2 then ground.

    Friction loss per segment ≈ μ_k · m · g · L (assumes mostly horizontal
    travel between hilltops). Pedagogical only — real coasters have curves.
    """
    heights = [h0, h1, h2, 0.0]
    labels = ["Start (top)", "Hill 1", "Hill 2", "End (ground)"]
    pe = [mass * g * h for h in heights]
    # Cumulative friction loss across each travelled segment.
    n_segments = len(heights) - 1
    friction_loss = mu_k * mass * g * segment_length_m
    cum_loss = [0.0] + [friction_loss * (i + 1) for i in range(n_segments)]

    ke = []
    reachable = []
    for i, p in enumerate(pe):
        budget = pe[0] - p - cum_loss[i]
        if budget < 0:
            ke.append(0.0)
            reachable.append(False)
        else:
            ke.append(budget)
            reachable.append(True)

    return {
        "labels": labels,
        "heights_m": heights,
        "pe_J": pe,
        "ke_J": ke,
        "reachable": reachable,
        "friction_loss_per_segment_J": friction_loss,
        "cumulative_loss_J": cum_loss,
        "mass_kg": mass,
    }


# ---------------------------------------------------------------------------
# 4. 1D collision
# ---------------------------------------------------------------------------
def collision_1d(m1: float, m2: float, v1: float, v2: float, e: float = 1.0) -> dict:
    """Two masses on a frictionless line. ``e`` is the coefficient of restitution.

    e = 1 → elastic; e = 0 → perfectly inelastic (stick together).
    Closed-form solution from momentum conservation + restitution definition.
    """
    p_before = m1 * v1 + m2 * v2
    ke_before = 0.5 * m1 * v1 * v1 + 0.5 * m2 * v2 * v2
    total = m1 + m2
    v1p = (m1 * v1 + m2 * v2 + m2 * e * (v2 - v1)) / total
    v2p = (m1 * v1 + m2 * v2 + m1 * e * (v1 - v2)) / total
    p_after = m1 * v1p + m2 * v2p
    ke_after = 0.5 * m1 * v1p * v1p + 0.5 * m2 * v2p * v2p
    return {
        "v1_prime": v1p,
        "v2_prime": v2p,
        "p_before": p_before,
        "p_after": p_after,
        "ke_before": ke_before,
        "ke_after": ke_after,
        "ke_lost": ke_before - ke_after,
        "restitution": e,
    }


# ---------------------------------------------------------------------------
# 4b. 2D collision (smooth-sphere model with restitution)
# ---------------------------------------------------------------------------
def collision_2d(m1: float, m2: float,
                 vx1: float, vy1: float,
                 vx2: float, vy2: float,
                 e: float = 1.0,
                 plastic: bool = False,
                 x1_0: float = -4.0, y1_0: float = 0.25,
                 x2_0: float = 4.0, y2_0: float = -0.25,
                 t_max: float = 4.0, n_frames: int = 200) -> dict:
    """Two disks on a frictionless 2D plane.

    Smooth-sphere model: at contact, the *normal* velocity components (along
    the line of centres) follow the 1D restitution rule with coefficient ``e``;
    *tangential* components are unchanged (no contact friction).

    If ``plastic`` is True the disks merge into a single body moving at the
    centre-of-mass velocity (true perfectly-inelastic 2D collision). Setting
    ``e = 0`` without ``plastic`` gives matching normal velocities but
    independent tangential motion.

    Returns trajectories for animation plus before/after kinematics for
    conservation-law plots.
    """
    # Visual radii — scale gently with mass so heavier disk looks larger.
    r1 = 0.85 + 0.45 * (max(m1, 0.01) ** (1 / 3))
    r2 = 0.85 + 0.45 * (max(m2, 0.01) ** (1 / 3))

    # Cache initial state for "before" panels.
    v1_in = (vx1, vy1)
    v2_in = (vx2, vy2)
    p_before = (m1 * vx1 + m2 * vx2, m1 * vy1 + m2 * vy2)
    ke_before = 0.5 * m1 * (vx1 * vx1 + vy1 * vy1) + 0.5 * m2 * (vx2 * vx2 + vy2 * vy2)

    # Working copies.
    cx1, cy1 = x1_0, y1_0
    cx2, cy2 = x2_0, y2_0
    cvx1, cvy1 = vx1, vy1
    cvx2, cvy2 = vx2, vy2

    xs1, ys1 = [cx1], [cy1]
    xs2, ys2 = [cx2], [cy2]
    collision_frame: int | None = None
    stuck = False
    total = m1 + m2

    dt = t_max / n_frames
    for i in range(n_frames):
        cx1 += cvx1 * dt
        cy1 += cvy1 * dt
        cx2 += cvx2 * dt
        cy2 += cvy2 * dt

        if collision_frame is None:
            dx = cx2 - cx1
            dy = cy2 - cy1
            dist = math.hypot(dx, dy)
            if dist <= (r1 + r2) and dist > 0.0:
                # Push the disks apart so they only just touch (split overlap
                # by mass — heavier disk moves less).
                overlap = (r1 + r2) - dist
                nx, ny = dx / dist, dy / dist
                cx1 -= nx * overlap * (m2 / total)
                cy1 -= ny * overlap * (m2 / total)
                cx2 += nx * overlap * (m1 / total)
                cy2 += ny * overlap * (m1 / total)

                # Decompose velocities into normal (line-of-centres) and tangent.
                tx, ty = -ny, nx
                v1n = cvx1 * nx + cvy1 * ny
                v1t = cvx1 * tx + cvy1 * ty
                v2n = cvx2 * nx + cvy2 * ny
                v2t = cvx2 * tx + cvy2 * ty

                # 1D restitution along the normal.
                v1n_new = (m1 * v1n + m2 * v2n + m2 * e * (v2n - v1n)) / total
                v2n_new = (m1 * v1n + m2 * v2n + m1 * e * (v1n - v2n)) / total

                if plastic:
                    # Both disks move with COM velocity; tangent components average too.
                    vcm_x = (m1 * cvx1 + m2 * cvx2) / total
                    vcm_y = (m1 * cvy1 + m2 * cvy2) / total
                    cvx1 = cvx2 = vcm_x
                    cvy1 = cvy2 = vcm_y
                    stuck = True
                else:
                    cvx1 = v1n_new * nx + v1t * tx
                    cvy1 = v1n_new * ny + v1t * ty
                    cvx2 = v2n_new * nx + v2t * tx
                    cvy2 = v2n_new * ny + v2t * ty

                collision_frame = i + 1

        xs1.append(cx1)
        ys1.append(cy1)
        xs2.append(cx2)
        ys2.append(cy2)

    p_after = (m1 * cvx1 + m2 * cvx2, m1 * cvy1 + m2 * cvy2)
    ke_after = 0.5 * m1 * (cvx1 * cvx1 + cvy1 * cvy1) + 0.5 * m2 * (cvx2 * cvx2 + cvy2 * cvy2)

    return {
        "xs1": xs1, "ys1": ys1, "xs2": xs2, "ys2": ys2,
        "r1": r1, "r2": r2,
        "v1_before": v1_in, "v2_before": v2_in,
        "v1_after": (cvx1, cvy1), "v2_after": (cvx2, cvy2),
        "p_before": p_before, "p_after": p_after,
        "ke_before": ke_before, "ke_after": ke_after,
        "ke_lost": ke_before - ke_after,
        "collision_frame": collision_frame,
        "stuck": stuck,
        "restitution": e,
        "m1": m1, "m2": m2,
        "n_frames": n_frames,
        "dt": dt,
    }


# ---------------------------------------------------------------------------
# 4c. Multi-disk 2D collision (top view, with friction + reflective walls)
# ---------------------------------------------------------------------------
def collision_multi(disks: list[dict],
                    e: float = 1.0,
                    plastic: bool = False,
                    mu_k: float = 0.0,
                    g: float = 9.81,
                    plane_half_x: float = 10.0,
                    plane_half_z: float = 6.0,
                    t_max: float = 20.0,
                    n_frames: int = 480) -> dict:
    """N ≥ 2 disks colliding on a (possibly rectangular) plane viewed from above.

    Each ``disks[i]`` is a dict with keys ``m, x, z, vx, vz``.
    ``mu_k`` adds kinetic friction between every disk and the plane (decay only,
    never reverses motion). Walls at ``±plane_half_x`` (sides) and
    ``±plane_half_z`` (top/bottom) reflect each disk elastically (perfect
    bounce — no energy loss at the wall). Disk-disk contacts use the smooth-
    sphere model with restitution ``e`` (or plastic merge of the colliding
    pair when ``plastic`` is True).

    Returned arrays are per-disk parallel lists indexed by frame.
    """
    n = len(disks)
    if n < 2:
        raise ValueError("collision_multi needs at least 2 disks")

    m  = [float(d["m"])  for d in disks]
    x  = [float(d["x"])  for d in disks]
    z  = [float(d["z"])  for d in disks]
    vx = [float(d["vx"]) for d in disks]
    vz = [float(d["vz"]) for d in disks]
    r  = [0.55 + 0.30 * (max(mi, 0.01) ** (1 / 3)) for mi in m]

    # Snapshot for "before" panels (initial state).
    v_before = [(vx[i], vz[i]) for i in range(n)]
    p_before = (sum(m[i] * vx[i] for i in range(n)),
                sum(m[i] * vz[i] for i in range(n)))
    ke_before = sum(0.5 * m[i] * (vx[i] ** 2 + vz[i] ** 2) for i in range(n))

    xs = [[x[i]] for i in range(n)]
    zs = [[z[i]] for i in range(n)]
    collision_events: list[tuple[int, int, int]] = []   # (frame, i, j)
    wall_events: list[tuple[int, int]] = []             # (frame, i)
    # Snapshot of all disk velocities right after the *first* disk-disk
    # collision — used as the "AFTER" state in the momentum / energy panels
    # so the BEFORE/AFTER comparison is the cleanest possible conservation
    # story (one well-defined collision, no wall reflections or repeat
    # contacts in between). Defaults to the initial state if no collision
    # occurs.
    v_after_first_coll: list[tuple[float, float]] = [(vx[i], vz[i]) for i in range(n)]
    walls_before_first_coll = 0
    first_coll_seen = False
    dt = t_max / n_frames
    a_fric = mu_k * g                                    # deceleration magnitude

    for fi in range(1, n_frames + 1):
        # Friction (kinetic): bleed speed off each disk uniformly.
        if a_fric > 0.0:
            for i in range(n):
                s = math.hypot(vx[i], vz[i])
                if s > 0.0:
                    new_s = max(0.0, s - a_fric * dt)
                    scale = new_s / s
                    vx[i] *= scale
                    vz[i] *= scale

        # Drift.
        for i in range(n):
            x[i] += vx[i] * dt
            z[i] += vz[i] * dt

        # Reflective walls (perfectly elastic).
        for i in range(n):
            ri = r[i]
            if x[i] - ri < -plane_half_x:
                x[i] = -plane_half_x + ri
                if vx[i] < 0: vx[i] = -vx[i]
                wall_events.append((fi, i))
            elif x[i] + ri > plane_half_x:
                x[i] = plane_half_x - ri
                if vx[i] > 0: vx[i] = -vx[i]
                wall_events.append((fi, i))
            if z[i] - ri < -plane_half_z:
                z[i] = -plane_half_z + ri
                if vz[i] < 0: vz[i] = -vz[i]
                wall_events.append((fi, i))
            elif z[i] + ri > plane_half_z:
                z[i] = plane_half_z - ri
                if vz[i] > 0: vz[i] = -vz[i]
                wall_events.append((fi, i))

        # Pairwise contacts.
        for i in range(n):
            for j in range(i + 1, n):
                dx, dz = x[j] - x[i], z[j] - z[i]
                dist = math.hypot(dx, dz)
                rsum = r[i] + r[j]
                if 0.0 < dist <= rsum:
                    # Overlap correction split by mass (heavier moves less).
                    overlap = rsum - dist
                    nx, nz = dx / dist, dz / dist
                    total = m[i] + m[j]
                    x[i] -= nx * overlap * (m[j] / total)
                    z[i] -= nz * overlap * (m[j] / total)
                    x[j] += nx * overlap * (m[i] / total)
                    z[j] += nz * overlap * (m[i] / total)

                    # Only resolve if disks are approaching (avoids re-trigger).
                    rel_vn = (vx[j] - vx[i]) * nx + (vz[j] - vz[i]) * nz
                    if rel_vn >= 0.0:
                        continue

                    tx, tz = -nz, nx
                    v1n = vx[i] * nx + vz[i] * nz
                    v1t = vx[i] * tx + vz[i] * tz
                    v2n = vx[j] * nx + vz[j] * nz
                    v2t = vx[j] * tx + vz[j] * tz

                    if plastic:
                        v_cm_n = (m[i] * v1n + m[j] * v2n) / total
                        v1n_new = v2n_new = v_cm_n
                        v_cm_t = (m[i] * v1t + m[j] * v2t) / total
                        v1t = v2t = v_cm_t
                    else:
                        v1n_new = (m[i] * v1n + m[j] * v2n
                                   + m[j] * e * (v2n - v1n)) / total
                        v2n_new = (m[i] * v1n + m[j] * v2n
                                   + m[i] * e * (v1n - v2n)) / total

                    vx[i] = v1n_new * nx + v1t * tx
                    vz[i] = v1n_new * nz + v1t * tz
                    vx[j] = v2n_new * nx + v2t * tx
                    vz[j] = v2n_new * nz + v2t * tz
                    collision_events.append((fi, i, j))
                    # Capture the "after" snapshot on the *first* collision
                    # only — that's the cleanest BEFORE/AFTER comparison.
                    if not first_coll_seen:
                        v_after_first_coll = [(vx[k], vz[k]) for k in range(n)]
                        walls_before_first_coll = len(wall_events)
                        first_coll_seen = True

        for i in range(n):
            xs[i].append(x[i])
            zs[i].append(z[i])

    # End-of-simulation state (used for diagnostics, not for the
    # conservation panels).
    v_final = [(vx[i], vz[i]) for i in range(n)]

    # "AFTER" snapshot for the conservation story: state right after the
    # *first* disk-disk collision. This isolates one clean disk-disk
    # interaction from any later wall reflections or repeat contacts.
    v_after = v_after_first_coll
    p_after = (sum(m[i] * v_after[i][0] for i in range(n)),
               sum(m[i] * v_after[i][1] for i in range(n)))
    ke_after = sum(0.5 * m[i] * (v_after[i][0] ** 2 + v_after[i][1] ** 2)
                   for i in range(n))

    # Momentum is conserved across that one disk-disk interaction iff no
    # wall reflected anything before it and there is no friction.
    momentum_conserved = (mu_k <= 1e-9) and (walls_before_first_coll == 0)

    return {
        "n": n,
        "m": m, "r": r,
        "xs": xs, "zs": zs,
        "v_before": v_before, "v_after": v_after,
        "p_before": p_before, "p_after": p_after,
        "ke_before": ke_before, "ke_after": ke_after,
        "ke_lost": max(0.0, ke_before - ke_after),
        "collision_events": collision_events,
        "wall_events": wall_events,
        "n_collisions": len(collision_events),
        "n_wall_hits": len(wall_events),
        "restitution": e,
        "plastic": plastic,
        "mu_k": mu_k,
        "plane_half_x": plane_half_x,
        "plane_half_z": plane_half_z,
        "n_frames": n_frames,
        "dt": dt,
        "momentum_conserved": momentum_conserved,
    }


# ---------------------------------------------------------------------------
# 5. Spring SHM (mass on a spring, no friction)
# ---------------------------------------------------------------------------
def spring_shm(m: float, k: float, x0: float, v0: float,
               n_periods: float = 3.0, n_points: int = 240) -> dict:
    if k <= 0 or m <= 0:
        return {
            "t": [0.0], "x": [x0], "v": [v0], "a": [0.0],
            "ke": [0.5 * m * v0 * v0], "pe": [0.5 * max(k, 0) * x0 * x0],
            "period_s": float("inf"), "amplitude_m": float("nan"),
            "omega": 0.0,
        }
    omega = math.sqrt(k / m)
    period = 2 * math.pi / omega
    amplitude = math.sqrt(x0 * x0 + (v0 / omega) ** 2)
    phi = math.atan2(-v0 / omega, x0)  # x(0)=x0, v(0)=v0
    t_max = period * n_periods
    t = np.linspace(0.0, t_max, n_points)
    x = amplitude * np.cos(omega * t + phi)
    v = -amplitude * omega * np.sin(omega * t + phi)
    a = -amplitude * omega * omega * np.cos(omega * t + phi)
    ke = 0.5 * m * v * v
    pe = 0.5 * k * x * x
    return {
        "t": t.tolist(),
        "x": x.tolist(),
        "v": v.tolist(),
        "a": a.tolist(),
        "ke": ke.tolist(),
        "pe": pe.tolist(),
        "period_s": period,
        "amplitude_m": amplitude,
        "omega": omega,
    }


# ---------------------------------------------------------------------------
# 6. Photoelectric effect
# ---------------------------------------------------------------------------
def photoelectric(freq_hz: float, intensity_rel: float, phi_eV: float) -> dict:
    """Einstein photoelectric equation: KE_max = h·f − φ.

    Intensity changes the *number* of ejected electrons (current), not the
    per-electron energy.
    """
    photon_J = _H * freq_hz
    photon_eV = photon_J / _EV_TO_J
    threshold_freq = (phi_eV * _EV_TO_J) / _H
    ke_max_eV = max(0.0, photon_eV - phi_eV)
    emits = photon_eV >= phi_eV
    # Toy "current" — proportional to intensity if frequency clears threshold.
    current_rel = intensity_rel if emits else 0.0
    return {
        "photon_eV": photon_eV,
        "photon_J": photon_J,
        "threshold_freq_Hz": threshold_freq,
        "ke_max_eV": ke_max_eV,
        "emits_electrons": emits,
        "current_rel": current_rel,
        "phi_eV": phi_eV,
    }


# ---------------------------------------------------------------------------
# 7. de Broglie wavelength
# ---------------------------------------------------------------------------
def de_broglie(mass_kg: float, v_mps: float) -> dict:
    """λ = h / p, classical p = m·v. Flags relativistic regime if v > 0.1c."""
    p = mass_kg * v_mps
    wavelength = _H / p if p != 0 else float("inf")
    relativistic = v_mps > 0.1 * _C
    return {
        "momentum_kg_m_s": p,
        "wavelength_m": wavelength,
        "relativistic_regime": relativistic,
    }


def double_slit(lambda_m: float, d_m: float, L_m: float,
                slit_width_m: float | None = None,
                n_particles: int = 180,
                n_grid: int = 400,
                seed: int = 42) -> dict:
    """Young's double-slit interference pattern for a particle with de Broglie
    wavelength λ. Two narrow slits of separation d, screen at distance L.

    Intensity (high-school form, no calculus):
        I(y) = cos²(π·d·y / (λ·L))            ← interference factor
              · sinc²(π·a·y / (λ·L))           ← single-slit envelope, a = slit width

    Fringe spacing: Δy = λ·L / d.

    Returns the intensity profile, the fringe spacing, and a sample of
    n_particles arrival positions on the screen drawn from the intensity
    distribution via rejection sampling.
    """
    if slit_width_m is None:
        slit_width_m = d_m / 4.0

    if lambda_m <= 0 or d_m <= 0 or L_m <= 0:
        return {
            "fringe_spacing_m": float("nan"),
            "screen_half_m": 1.0,
            "slit_separation_m": d_m,
            "slit_to_screen_m": L_m,
            "slit_width_m": slit_width_m,
            "wavelength_m": lambda_m,
            "y_grid_m": [],
            "intensity_norm": [],
            "arrival_positions_m": [],
            "regime": "invalid",
        }

    fringe_spacing = lambda_m * L_m / d_m

    if fringe_spacing < 1e-9:
        regime = "fringes_atomic_or_smaller"
    elif fringe_spacing < 1e-4:
        regime = "fringes_microscopic"
    elif fringe_spacing < 1e-1:
        regime = "fringes_visible"
    else:
        regime = "fringes_macroscopic"

    rng = np.random.default_rng(seed)

    if regime == "fringes_atomic_or_smaller":
        # Classical regime: fringes are sub-atomic and unobservable. Particles
        # behave like ballistic projectiles — they pile up in two narrow clumps
        # directly behind each slit. No interference.
        screen_half = 2.5 * d_m
        y_grid = np.linspace(-screen_half, screen_half, n_grid)
        sigma = 0.25 * slit_width_m
        clump1 = np.exp(-0.5 * ((y_grid - d_m / 2.0) / sigma) ** 2)
        clump2 = np.exp(-0.5 * ((y_grid + d_m / 2.0) / sigma) ** 2)
        intensity = clump1 + clump2
        peak = float(intensity.max()) if intensity.size else 1.0
        intensity_norm = intensity / peak if peak > 0 else intensity

        # Sample arrivals as two Gaussian clumps (no interference fringes).
        half = n_particles // 2
        s1 = rng.normal(loc=d_m / 2.0, scale=sigma, size=half)
        s2 = rng.normal(loc=-d_m / 2.0, scale=sigma, size=n_particles - half)
        arrivals_arr = np.concatenate([s1, s2])
        arrivals_arr = np.clip(arrivals_arr, -screen_half, screen_half)
        arrivals = arrivals_arr.tolist()
    else:
        screen_half = 5.0 * fringe_spacing  # show ~10 fringes
        y_grid = np.linspace(-screen_half, screen_half, n_grid)
        arg_int = math.pi * d_m * y_grid / (lambda_m * L_m)
        arg_env = math.pi * slit_width_m * y_grid / (lambda_m * L_m)
        interference = np.cos(arg_int) ** 2
        envelope = np.where(np.abs(arg_env) < 1e-12,
                            1.0,
                            (np.sin(arg_env) / np.where(arg_env == 0, 1.0, arg_env)) ** 2)
        intensity = interference * envelope
        peak = float(intensity.max()) if intensity.size else 1.0
        intensity_norm = intensity / peak if peak > 0 else intensity

        # Rejection sampling for arrival positions
        arrivals = []
        safety = 0
        while len(arrivals) < n_particles and safety < 50:
            n_needed = n_particles - len(arrivals)
            ys = rng.uniform(-screen_half, screen_half, n_needed * 5)
            ps = np.interp(ys, y_grid, intensity_norm)
            accept = rng.uniform(0.0, 1.0, len(ys)) < ps
            arrivals.extend(ys[accept].tolist()[:n_needed])
            safety += 1

    return {
        "fringe_spacing_m": float(fringe_spacing),
        "screen_half_m": float(screen_half),
        "slit_separation_m": float(d_m),
        "slit_to_screen_m": float(L_m),
        "slit_width_m": float(slit_width_m),
        "wavelength_m": float(lambda_m),
        "y_grid_m": y_grid.tolist(),
        "intensity_norm": intensity_norm.tolist(),
        "arrival_positions_m": arrivals[:n_particles],
        "regime": regime,
    }
