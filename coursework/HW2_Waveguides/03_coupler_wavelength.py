import os
import numpy as np
import matplotlib.pyplot as plt
import tidy3d as td
import tidy3d.web as web
import tidy3d.plugins.mode as mode

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

gap = 0.21 # um
mat_si = td.material_library["cSi"]["Li1993_293K"]
mat_sio2 = td.material_library["SiO2"]["Horiba"]

platforms = {
    "Plat1_220nm": {"H": 0.22, "W": 0.41},
    "Plat2_300nm": {"H": 0.30, "W": 0.37} # <--- NUESTRA PLATAFORMA OBJETIVO
}

# ==============================================================================
# 2. CÁLCULO ANALÍTICO DE SUPERMODOS
# ==============================================================================
analytical_results = {}
print("--- CÁLCULO DE SUPERMODOS (300 nm) ---")

# Calculamos solo para la plataforma de 300nm para ahorrar tiempo
target_plat = "Plat2_300nm"
H, W = platforms[target_plat]["H"], platforms[target_plat]["W"]

core1 = td.Structure(geometry=td.Box(center=(0, W/2 + gap/2, 0), size=(td.inf, W, H)), medium=mat_si)
core2 = td.Structure(geometry=td.Box(center=(0, -W/2 - gap/2, 0), size=(td.inf, W, H)), medium=mat_si)
clad = td.Structure(geometry=td.Box(center=(0,0,0), size=(td.inf, td.inf, td.inf)), medium=mat_sio2)

sim_2d = td.Simulation(
    size=(0, 3.0, 2.0), grid_spec=td.GridSpec.auto(min_steps_per_wvl=20, wavelength=wl_center),
    structures=[clad, core1, core2], run_time=1e-12,
    boundary_spec=td.BoundarySpec(x=td.Boundary.periodic(), y=td.Boundary.pml(), z=td.Boundary.pml())
)

mode_solver = mode.ModeSolver(
    simulation=sim_2d, plane=td.Box(center=(0, 0, 0), size=(0, 3.0, 2.0)),
    mode_spec=td.ModeSpec(num_modes=2, target_neff=2.8), freqs=[freq0] # Target neff un poco más alto por el H=300nm
)
mode_data = mode_solver.solve()

n_sym = np.real(mode_data.n_eff.values[0, 0])
n_anti = np.real(mode_data.n_eff.values[0, 1])
Lx = wl_center / (2 * (n_sym - n_anti))
L_3dB = Lx / 2.0
L_10 = (2 * Lx / np.pi) * np.arcsin(np.sqrt(0.1))

lengths = {"Lx": Lx, "L_3dB": L_3dB, "L_10": L_10}

print(f"{target_plat}: n_sym = {n_sym:.4f} | n_anti = {n_anti:.4f}")
print(f" -> L_x (100%) = {Lx:.2f} um | L_3dB (50%) = {L_3dB:.2f} um | L_10 (10%) = {L_10:.2f} um\n")

# ==============================================================================
# 3. CONSTRUCCIÓN GEOMÉTRICA FDTD ROBUSTA (Transiciones Adiabáticas)
# ==============================================================================
def make_straight(x0, x1, y, W, H):
    return td.Structure(geometry=td.Box(center=((x0+x1)/2, y, 0), size=(x1-x0, W, H)), medium=mat_si)

def make_linear_bend(x0, y0, x1, y1, W, H):
    v = [(x0, y0 + W/2), (x0, y0 - W/2), (x1, y1 - W/2), (x1, y1 + W/2)]
    return td.Structure(geometry=td.PolySlab(vertices=v, axis=2, slab_bounds=(-H/2, H/2)), medium=mat_si)

y_port = 1.0
y_c = W/2 + gap/2

# CORRECCIÓN FÍSICA: Alargamos la curva de 4.0 um a 15.0 um para evitar Radiation Loss
L_bend = 15.0

sims_batch = {}
print("--- ENVIANDO BATCH FDTD (Barrido de L para 300 nm) ---")

for L_name, L_val in lengths.items():
    x_in = -L_val/2 - L_bend
    x_out = L_val/2 + L_bend

    t_in = make_straight(x_in - 2.0, x_in, y_port, W, H)
    t_b1 = make_linear_bend(x_in, y_port, -L_val/2, y_c, W, H)
    t_mid = make_straight(-L_val/2, L_val/2, y_c, W, H)
    t_b2 = make_linear_bend(L_val/2, y_c, x_out, y_port, W, H)
    t_out = make_straight(x_out, x_out + 2.0, y_port, W, H)

    b_in = make_straight(x_in - 2.0, x_in, -y_port, W, H)
    b_b1 = make_linear_bend(x_in, -y_port, -L_val/2, -y_c, W, H)
    b_mid = make_straight(-L_val/2, L_val/2, -y_c, W, H)
    b_b2 = make_linear_bend(L_val/2, -y_c, x_out, -y_port, W, H)
    b_out = make_straight(x_out, x_out + 2.0, -y_port, W, H)

    structures = [clad, t_in, t_b1, t_mid, t_b2, t_out, b_in, b_b1, b_mid, b_b2, b_out]
    sim_len = L_val + 2*L_bend + 4.0

    sim = td.Simulation(
        size=(sim_len, 3.5, 2.0),
        grid_spec=td.GridSpec.auto(min_steps_per_wvl=15, wavelength=wl_center),
        structures=structures,
        sources=[
            td.ModeSource(
                center=(x_in - 1.0, y_port, 0), size=(0, W+0.8, H+0.8), direction="+",
                source_time=td.GaussianPulse(freq0=freq0, fwidth=freq0/10), mode_spec=td.ModeSpec(num_modes=1)
            )
        ],
        monitors=[
            td.ModeMonitor(center=(x_out + 1.0, y_port, 0), size=(0, W+0.8, H+0.8), freqs=freqs, name="through", mode_spec=td.ModeSpec(num_modes=1)),
            td.ModeMonitor(center=(x_out + 1.0, -y_port, 0), size=(0, W+0.8, H+0.8), freqs=freqs, name="cross", mode_spec=td.ModeSpec(num_modes=1))
        ],
        run_time=8e-13,
        boundary_spec=td.BoundarySpec.all_sides(boundary=td.PML())
    )
    sims_batch[L_name] = sim

batch = web.Batch(simulations=sims_batch)
results = batch.run(path_dir="dc_data_300nm_fixed")
print("Simulaciones completadas.")

# ==============================================================================
# 4. EXTRACCIÓN DE DATOS Y GRÁFICAS (300 nm)
# ==============================================================================
fig, axs = plt.subplots(1, 3, figsize=(16, 4))
freq_idx = np.argmin(np.abs(freqs - freq0))

# --- 1. Coupling Ratio vs L at 1550 nm ---
L_analitico = np.linspace(0, lengths["Lx"]*1.2, 100)
P_cross_analitico = np.sin(np.pi * L_analitico / (2 * lengths["Lx"]))**2

axs[0].plot(L_analitico, P_cross_analitico, 'r-', label='Cross (Analytical)')
axs[0].plot(L_analitico, 1 - P_cross_analitico, 'b-', label='Through (Analytical)')

for L_name, L_val in lengths.items():
    res = results[L_name]
    T_th = np.abs(res['through'].amps.sel(direction='+').values[freq_idx, 0])**2
    T_cr = np.abs(res['cross'].amps.sel(direction='+').values[freq_idx, 0])**2
    axs[0].plot(L_val, T_cr, 'ro', markersize=8, markeredgecolor='k')
    axs[0].plot(L_val, T_th, 'bo', markersize=8, markeredgecolor='k')

axs[0].set(xlabel='Coupling Length $L$ ($\mu$m)', ylabel='Power Transmission', title='Coupling Ratio vs $L$ (300 nm Platform)')
axs[0].legend()
axs[0].grid(alpha=0.4)

# --- 2. Splitting Ratio vs Wavelength ---
res_50 = results["L_3dB"]
T_th_broad = np.abs(res_50['through'].amps.sel(direction='+'))**2
T_cr_broad = np.abs(res_50['cross'].amps.sel(direction='+'))**2

axs[1].plot(wl_band*1000, T_cr_broad, 'r.-', label='Cross (FDTD)')
axs[1].plot(wl_band*1000, T_th_broad, 'b.-', label='Through (FDTD)')
axs[1].axvline(1550, color='k', linestyle='--')
axs[1].set(xlabel='Wavelength (nm)', ylabel='Transmission', title='Splitting Ratio vs Wavelength ($L_{3dB}$)')
axs[1].legend()
axs[1].grid(alpha=0.4)

# --- 3. Excess Loss Estimate ---
Excess_Loss = -10 * np.log10(T_th_broad + T_cr_broad)
axs[2].plot(wl_band*1000, Excess_Loss, 'm.-', label='Excess Loss')
axs[2].set(xlabel='Wavelength (nm)', ylabel='Loss (dB)', title='Excess Loss (Radiation)')
axs[2].set_ylim(0, max(0.5, np.max(Excess_Loss)*1.2))
axs[2].grid(alpha=0.4)

plt.tight_layout()
plt.show()
