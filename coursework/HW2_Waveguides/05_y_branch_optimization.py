import os
import numpy as np
import matplotlib.pyplot as plt
import tidy3d as td
import tidy3d.web as web

# ==============================================================================
# 0. AUTENTICACIÓN
# ==============================================================================
os.environ["TIDY3D_API_KEY"] = "API_KEY_PROPIA" #Aqui se empleo la API Key propia
web.configure(os.environ["TIDY3D_API_KEY"])

# ==============================================================================
# 1. PARÁMETROS GLOBALES
# ==============================================================================
wl_center = 1.55
wl_band = np.linspace(1.50, 1.60, 21)
freqs = td.C_0 / wl_band
freq0 = td.C_0 / wl_center

mat_si = td.material_library["cSi"]["Li1993_293K"]
mat_sio2 = td.material_library["SiO2"]["Horiba"]

platforms = {
    "Plat_220": {"H": 0.22, "W": 0.41},
    "Plat_300": {"H": 0.30, "W": 0.37}
}

designs = ["Short", "Optimized"]
y_pitch = 3.0

# ==============================================================================
# 2. CONSTRUCTORES GEOMÉTRICOS
# ==============================================================================
def make_taper(x0, x1, y_center, w0, w1, H):
    v = [(x0, y_center + w0/2), (x0, y_center - w0/2), (x1, y_center - w1/2), (x1, y_center + w1/2)]
    return td.Structure(geometry=td.PolySlab(vertices=v, axis=2, slab_bounds=(-H/2, H/2)), medium=mat_si)

def make_straight(x0, x1, y, W, H):
    return td.Structure(geometry=td.Box(center=((x0+x1)/2, y, 0), size=(x1-x0, W, H)), medium=mat_si)

def make_sine_bend(x0, y0, x1, y1, W, H):
    x = np.linspace(x0, x1, 100)
    L = x1 - x0
    dy = y1 - y0
    x_frac = (x - x0) / L
    y = y0 + dy * x_frac - dy * np.sin(2 * np.pi * x_frac) / (2 * np.pi)
    dx_grad, dy_grad = np.gradient(x), np.gradient(y)
    norm = np.sqrt(dx_grad**2 + dy_grad**2)
    nx, ny = -dy_grad / norm, dx_grad / norm
    xtop, ytop = x + W/2 * nx, y + W/2 * ny
    xbot, ybot = x - W/2 * nx, y - W/2 * ny
    v = np.vstack((np.concatenate((xtop, xbot[::-1])), np.concatenate((ytop, ybot[::-1])))).T
    return td.Structure(geometry=td.PolySlab(vertices=[tuple(pt) for pt in v], axis=2, slab_bounds=(-H/2, H/2)), medium=mat_si)

def make_optimized_junction(x_start, H):
    widths = np.array([0.5, 0.5, 0.6, 0.7, 0.9, 1.26, 1.4, 1.4, 1.4, 1.4, 1.31, 1.2, 1.2])
    x_vals = np.linspace(x_start, x_start + 2.0, 13)
    x = np.concatenate((x_vals, np.flipud(x_vals)))
    y = np.concatenate((widths / 2, -np.flipud(widths / 2)))
    v = np.transpose(np.vstack((x, y)))
    return td.Structure(geometry=td.PolySlab(vertices=[tuple(pt) for pt in v], axis=2, slab_bounds=(-H/2, H/2)), medium=mat_si)

# ==============================================================================
# 3. CONSTRUCCIÓN Y EJECUCIÓN
# ==============================================================================
sims_batch = {}
for p_name, p in platforms.items():
    H, W = p["H"], p["W"]
    clad = td.Structure(geometry=td.Box(center=(0,0,0), size=(td.inf, td.inf, td.inf)), medium=mat_sio2)
    for d_name in designs:
        structs = [clad]
        if d_name == "Short":
            x_in_inf, x_split, x_end, x_out_inf = -20.0, 0.0, 3.0, 20.0
            sim_x_min, sim_x_max = -5.0, 8.0
            structs += [make_straight(x_in_inf, x_split, 0, W, H), make_sine_bend(x_split, 0, x_end, y_pitch/2, W, H), make_sine_bend(x_split, 0, x_end, -y_pitch/2, W, H), make_straight(x_end, x_out_inf, y_pitch/2, W, H), make_straight(x_end, x_out_inf, -y_pitch/2, W, H)]
            x_src, x_mon_in, x_mon_out = -4.0, -3.5, 7.0
        else:
            w_opt, y0_bend = 0.5, 0.35
            x_in_inf, x_tap1, x_junc, x_bend, x_tap2, x_tap2_end, x_out_inf = -20.0, -3.0, 0.0, 2.0, 8.0, 10.0, 20.0
            sim_x_min, sim_x_max = -6.0, 12.0
            structs += [make_straight(x_in_inf, x_tap1, 0, W, H), make_taper(x_tap1, x_junc, 0, W, w_opt, H), make_optimized_junction(x_junc, H), make_sine_bend(x_bend, y0_bend, x_tap2, y_pitch/2, w_opt, H), make_sine_bend(x_bend, -y0_bend, x_tap2, -y_pitch/2, w_opt, H), make_taper(x_tap2, x_tap2_end, y_pitch/2, w_opt, W, H), make_taper(x_tap2, x_tap2_end, -y_pitch/2, w_opt, W, H), make_straight(x_tap2_end, x_out_inf, y_pitch/2, W, H), make_straight(x_tap2_end, x_out_inf, -y_pitch/2, W, H)]
            x_src, x_mon_in, x_mon_out = -5.0, -4.5, 11.0

        sim_len, sim_center = sim_x_max - sim_x_min, (sim_x_max + sim_x_min) / 2.0
        mon_size = (0, 3.0, 2.0)
        monitors = [
            td.ModeMonitor(center=(x_mon_out, y_pitch/2, 0), size=mon_size, freqs=freqs, name="out_top", mode_spec=td.ModeSpec(num_modes=1)),
            td.ModeMonitor(center=(x_mon_out, -y_pitch/2, 0), size=mon_size, freqs=freqs, name="out_bot", mode_spec=td.ModeSpec(num_modes=1)),
            td.ModeMonitor(center=(x_mon_in, 0, 0), size=mon_size, freqs=freqs, name="reflection", mode_spec=td.ModeSpec(num_modes=1)),
            td.FieldMonitor(center=(sim_center, 0, 0), size=(td.inf, td.inf, 0), freqs=[freq0], name="field")
        ]
        sims_batch[f"{p_name}_{d_name}"] = td.Simulation(center=(sim_center, 0, 0), size=(sim_len, y_pitch + 4.0, 2.5), grid_spec=td.GridSpec.auto(min_steps_per_wvl=15, wavelength=wl_center), structures=structs, sources=[td.ModeSource(center=(x_src, 0, 0), size=mon_size, direction="+", source_time=td.GaussianPulse(freq0=freq0, fwidth=freq0/10), mode_spec=td.ModeSpec(num_modes=1))], monitors=monitors, run_time=2e-12, boundary_spec=td.BoundarySpec.all_sides(boundary=td.PML()))

results = web.Batch(simulations=sims_batch).run(path_dir="ybranch_final_data")

# ==============================================================================
# 4. EXTRACCIÓN Y GRÁFICAS
# ==============================================================================
fig_il, axs_il = plt.subplots(1, 2, figsize=(14, 5))
freq_idx = np.argmin(np.abs(freqs - freq0))

for i, p_name in enumerate(platforms.keys()):
    ax = axs_il[i]
    for d_name in designs:
        res = results[f"{p_name}_{d_name}"]
        # Usamos .values para asegurar que obtenemos arreglos numpy
        T_top = np.abs(res['out_top'].amps.sel(direction='+').values[:, 0])**2
        T_bot = np.abs(res['out_bot'].amps.sel(direction='+').values[:, 0])**2
        T_total = np.clip(T_top + T_bot, 1e-10, 1.0)
        IL_all = -10 * np.log10(T_total)

        linestyle = '-' if d_name == "Optimized" else '--'
        ax.plot(wl_band*1000, IL_all, linestyle=linestyle, linewidth=2.5, label=f"{d_name} Design")
        il_val = IL_all[freq_idx].item()
        print(f"[{p_name} - {d_name}] IL @ 1550nm: {il_val:.3f} dB")

    ax.set_title(f"Bandwidth (Insertion Loss) - {p_name}")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Insertion Loss (dB)")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.4); ax.legend()

plt.tight_layout(); plt.show()

# Gráficas de Campo
fig_f, axs_f = plt.subplots(2, 2, figsize=(14, 10))
for i, p_name in enumerate(platforms.keys()):
    for j, d_name in enumerate(designs):
        res = results[f"{p_name}_{d_name}"]; ax = axs_f[i, j]
        Ey = np.abs(res['field'].Ey.values[:, :, 0, 0])
        x_c, y_c = res['field'].Ey.coords['x'].values, res['field'].Ey.coords['y'].values
        c = ax.pcolormesh(x_c, y_c, Ey.T, cmap='magma', shading='auto')
        ax.set_title(f"Field: {p_name} | {d_name}"); ax.set_xlabel(r"Z ($\mu$m)"); ax.set_ylabel(r"X ($\mu$m)"); ax.set_aspect('equal')
        fig_f.colorbar(c, ax=ax, label='|Ey| field')
plt.tight_layout(); plt.show()
