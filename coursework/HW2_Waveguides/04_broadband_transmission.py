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
    "Plat_220": {"H": 0.22, "W_in": 0.41, "W_test": [3.0, 3.4], "L_test": [9.0, 10.0, 11.0]},
    "Plat_300": {"H": 0.30, "W_in": 0.37, "W_test": [3.0, 3.4], "L_test": [10.0, 11.0, 12.0]}
}

L_taper = 2.0
W_taper = 0.9

# ==============================================================================
# 2. FUNCIÓN CONSTRUCTORA DEL MMI
# ==============================================================================
def make_taper(x0, x1, y_center, w0, w1, H):
    v = [(x0, y_center + w0/2), (x0, y_center - w0/2), (x1, y_center - w1/2), (x1, y_center + w1/2)]
    return td.Structure(geometry=td.PolySlab(vertices=v, axis=2, slab_bounds=(-H/2, H/2)), medium=mat_si)

def make_straight(x0, x1, y, W, H):
    return td.Structure(geometry=td.Box(center=((x0+x1)/2, y, 0), size=(x1-x0, W, H)), medium=mat_si)

def build_mmi_sim(W_mmi, L_mmi, H, W_in, sim_name):
    x_in_start  = -L_mmi/2 - L_taper - 2.0
    x_in_taper  = -L_mmi/2 - L_taper
    x_mmi_in    = -L_mmi/2
    x_mmi_out   = L_mmi/2
    x_out_taper = L_mmi/2 + L_taper
    x_out_end   = L_mmi/2 + L_taper + 2.0
    y_out       = W_mmi / 4.0

    clad = td.Structure(geometry=td.Box(center=(0,0,0), size=(td.inf, td.inf, td.inf)), medium=mat_sio2)
    wg_in = make_straight(x_in_start-1.0, x_in_taper, 0, W_in, H)
    taper_in = make_taper(x_in_taper, x_mmi_in, 0, W_in, W_taper, H)
    mmi_body = make_straight(x_mmi_in, x_mmi_out, 0, W_mmi, H)
    taper_out_top = make_taper(x_mmi_out, x_out_taper, y_out, W_taper, W_in, H)
    wg_out_top = make_straight(x_out_taper, x_out_end+1.0, y_out, W_in, H)
    taper_out_bot = make_taper(x_mmi_out, x_out_taper, -y_out, W_taper, W_in, H)
    wg_out_bot = make_straight(x_out_taper, x_out_end+1.0, -y_out, W_in, H)

    structs = [clad, wg_in, taper_in, mmi_body, taper_out_top, wg_out_top, taper_out_bot, wg_out_bot]

    x_mon_in, x_src, x_mon_out = x_in_start + 0.5, x_in_start + 1.0, x_out_end - 0.5

    monitors = [
        td.ModeMonitor(center=(x_mon_out, y_out, 0), size=(0, W_in+1, H+1), freqs=freqs, name="out_top", mode_spec=td.ModeSpec(num_modes=1)),
        td.ModeMonitor(center=(x_mon_out, -y_out, 0), size=(0, W_in+1, H+1), freqs=freqs, name="out_bot", mode_spec=td.ModeSpec(num_modes=1)),
        td.ModeMonitor(center=(x_mon_in, 0, 0), size=(0, W_in+1, H+1), freqs=freqs, name="reflection", mode_spec=td.ModeSpec(num_modes=1)),
        td.FieldMonitor(center=(0, 0, 0), size=(td.inf, W_mmi+3.0, 0), freqs=[freq0], name="field_profile")
    ]

    return td.Simulation(
        size=(L_mmi + 2*L_taper + 6.0, W_mmi + 4.0, 2.0),
        grid_spec=td.GridSpec.auto(min_steps_per_wvl=15, wavelength=wl_center),
        structures=structs,
        sources=[td.ModeSource(center=(x_src, 0, 0), size=(0, W_in+1, H+1), direction="+", source_time=td.GaussianPulse(freq0=freq0, fwidth=freq0/10), mode_spec=td.ModeSpec(num_modes=1))],
        monitors=monitors, run_time=6e-13, boundary_spec=td.BoundarySpec.all_sides(boundary=td.PML())
    )

def extract_IL(res):
    freq_idx = np.argmin(np.abs(freqs - freq0))
    T_top = np.abs(res['out_top'].amps.sel(direction='+').values[freq_idx, 0])**2
    T_bot = np.abs(res['out_bot'].amps.sel(direction='+').values[freq_idx, 0])**2
    return -10 * np.log10(T_top + T_bot)

# ==============================================================================
# 3. ETAPA 1: COARSE SWEEP
# ==============================================================================
print("\n[ETAPA 1] Ejecutando Coarse Sweep...")
coarse_sims = {}
for p_name, p in platforms.items():
    for W_mmi in p["W_test"]:
        for L_mmi in p["L_test"]:
            sim_name = f"{p_name}_W{W_mmi}_L{L_mmi}"
            coarse_sims[sim_name] = build_mmi_sim(W_mmi, L_mmi, p["H"], p["W_in"], sim_name)

coarse_results = web.Batch(simulations=coarse_sims).run(path_dir="mmi_coarse")

best_coarse = {}
for p_name, p in platforms.items():
    min_IL = float('inf')
    for W_mmi in p["W_test"]:
        for L_mmi in p["L_test"]:
            sim_name = f"{p_name}_W{W_mmi}_L{L_mmi}"
            IL = extract_IL(coarse_results[sim_name])
            if IL < min_IL:
                min_IL = IL
                best_coarse[p_name] = {"W": W_mmi, "L": L_mmi, "IL": IL}
    print(f" -> Mejor Coarse para {p_name}: W={best_coarse[p_name]['W']}, L={best_coarse[p_name]['L']} (IL={best_coarse[p_name]['IL']:.3f} dB)")

# ==============================================================================
# 4. ETAPA 2: FINE SWEEP (Centrado en el mejor resultado)
# ==============================================================================
print("\n[ETAPA 2] Ejecutando Fine Sweep alrededor de los óptimos...")
fine_sims = {}
fine_L_steps = [-0.4, -0.2, 0.0, 0.2, 0.4] # Barrido fino de longitud focal

for p_name, p in platforms.items():
    W_opt = best_coarse[p_name]["W"]
    L_opt = best_coarse[p_name]["L"]

    for dL in fine_L_steps:
        L_fine = round(L_opt + dL, 2)
        sim_name = f"{p_name}_FINE_W{W_opt}_L{L_fine}"
        fine_sims[sim_name] = build_mmi_sim(W_opt, L_fine, p["H"], p["W_in"], sim_name)

fine_results = web.Batch(simulations=fine_sims).run(path_dir="mmi_fine")

best_fine = {}
for p_name in platforms.keys():
    min_IL = float('inf')
    best_res = None
    best_L = 0
    W_opt = best_coarse[p_name]["W"]

    for dL in fine_L_steps:
        L_fine = round(best_coarse[p_name]["L"] + dL, 2)
        sim_name = f"{p_name}_FINE_W{W_opt}_L{L_fine}"
        res = fine_results[sim_name]
        IL = extract_IL(res)
        if IL < min_IL:
            min_IL = IL
            best_res = res
            best_L = L_fine

    best_fine[p_name] = {"W": W_opt, "L": best_L, "res": best_res, "IL": min_IL}
    print(f" => ÓPTIMO ABSOLUTO {p_name}: W={W_opt}, L={best_L} (IL={min_IL:.3f} dB)")

# ==============================================================================
# 5. GRÁFICAS DEL MMI ÓPTIMO DEFINITIVO
# ==============================================================================
fig_fields, axs_fields = plt.subplots(2, 1, figsize=(12, 8))
fig_spectra, axs_spectra = plt.subplots(1, 2, figsize=(14, 5))

for idx, p_name in enumerate(platforms.keys()):
    opt = best_fine[p_name]
    res = opt["res"]

    # -- Perfil de Campo --
    Ey_xarray = res['field_profile'].Ey
    E_mag = np.abs(Ey_xarray.values[:, :, 0, 0])
    x_coords, y_coords = Ey_xarray.coords['x'].values, Ey_xarray.coords['y'].values

    ax = axs_fields[idx]
    c = ax.pcolormesh(x_coords, y_coords, E_mag.T, cmap='magma', shading='auto')
    ax.set_title(f"Field Profile: {p_name} (W={opt['W']} $\mu$m, L={opt['L']} $\mu$m)", fontsize=12)
    ax.set_xlabel('Propagation Distance Z ($\mu$m)')
    ax.set_ylabel('Width X ($\mu$m)')
    ax.set_aspect('equal')
    fig_fields.colorbar(c, ax=ax, label='|Ey| field')

    # -- Espectro de Banda Ancha --
    T_top_broad = np.abs(res['out_top'].amps.sel(direction='+'))**2
    T_bot_broad = np.abs(res['out_bot'].amps.sel(direction='+'))**2
    IL_broad = -10 * np.log10(T_top_broad + T_bot_broad)

    ax_spec = axs_spectra[idx]
    ax_spec.plot(wl_band*1000, T_top_broad, color='tab:blue', label='Top Port', linewidth=2)
    ax_spec.plot(wl_band*1000, T_bot_broad, color='tab:orange', linestyle='--', label='Bottom Port', linewidth=2)
    ax_spec.set_xlabel('Wavelength (nm)', fontsize=11)
    ax_spec.set_ylabel('Transmission (Linear)', color='black', fontsize=11)
    ax_spec.axvline(1550, color='gray', linestyle=':', alpha=0.7)
    # Límite Y dinámico
    ax_spec.set_ylim(min(np.min(T_top_broad), np.min(T_bot_broad)) - 0.05, 0.55)

    ax2 = ax_spec.twinx()
    ax2.plot(wl_band*1000, IL_broad, color='tab:red', label='Total IL', linewidth=2)
    ax2.set_ylabel('Insertion Loss (dB)', color='tab:red', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='tab:red')

    ax_spec.set_title(f"Broadband Performance: {p_name}", fontsize=12)
    lines_1, labels_1 = ax_spec.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper center')

fig_fields.tight_layout()
fig_spectra.tight_layout()
plt.show()
