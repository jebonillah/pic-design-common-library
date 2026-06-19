# ==============================================================================
# Task 1.1 — Pick the “single-mode operation regime” (Cloud-Enabled)
# ==============================================================================

import os
import numpy as np
import matplotlib.pyplot as plt
import tidy3d as td
import tidy3d.web as web
import tidy3d.plugins.mode as mode

# ------------------------------------------------------------------------------
# 0. AUTENTICACIÓN EN LA NUBE (HPC)
# ------------------------------------------------------------------------------
# Reemplaza la cadena vacía con tu API Key real de FlexCompute
API_KEY = "API_KEY_PROPIA" #Aqui se empleo la API Key propia
os.environ["TIDY3D_API_KEY"] = API_KEY
web.configure(os.environ["TIDY3D_API_KEY"])
print("Autenticación Cloud configurada correctamente.\n")

# ------------------------------------------------------------------------------
# 1. DEFINICIÓN DEL ESPACIO PARAMÉTRICO
# ------------------------------------------------------------------------------
wavelengths = [1.50, 1.55]         # Longitudes de onda en um
thicknesses = [0.22, 0.30]         # Espesores de SOI en um (H)
widths = np.linspace(0.2, 0.8, 25) # Anchos de guía en um (W)

freqs = [td.C_0 / wl for wl in wavelengths]

# Materiales dispersivos (requieren conexión a la nube para descargar el modelo)
mat_si = td.material_library["cSi"]["Li1993_293K"]
mat_sio2 = td.material_library["SiO2"]["Horiba"]

# Dimensiones de la ventana computacional transversal
domain_y = 3.0 # um
domain_z = 2.0 # um

# Diccionario para almacenar resultados
results = {}

print("Iniciando Cloud Eigenmode Sweep (Filtrado estricto para TE-modes)...")

# ------------------------------------------------------------------------------
# 2. MOTOR COMPUTACIONAL
# ------------------------------------------------------------------------------
for H in thicknesses:
    for wl, freq in zip(wavelengths, freqs):

        # Índice del cladding para la condición de cut-off
        n_clad = np.sqrt(mat_sio2.eps_model(freq).real)
        mode_counts = []

        for W in widths:
            # Geometría
            waveguide = td.Structure(
                geometry=td.Box(center=(0, 0, 0), size=(td.inf, W, H)),
                medium=mat_si,
                name="Core"
            )
            cladding = td.Structure(
                geometry=td.Box(center=(0, 0, 0), size=(td.inf, td.inf, td.inf)),
                medium=mat_sio2,
                name="Cladding"
            )

            # Simulación 2D
            sim = td.Simulation(
                size=(0, domain_y, domain_z),
                grid_spec=td.GridSpec.auto(min_steps_per_wvl=20, wavelength=wl),
                structures=[cladding, waveguide],
                run_time=1e-12,
                boundary_spec=td.BoundarySpec(
                    x=td.Boundary.periodic(), # Eje de propagación periódico
                    y=td.Boundary.pml(),      # Absorción transversal
                    z=td.Boundary.pml()       # Absorción transversal
                )
            )

            # Mode Solver Configurado
            mode_solver = mode.ModeSolver(
                simulation=sim,
                plane=td.Box(center=(0, 0, 0), size=(0, domain_y, domain_z)),
                mode_spec=td.ModeSpec(num_modes=6, target_neff=3.4),
                freqs=[freq]
            )

            # Ejecución (Se ejecuta bajo el entorno autenticado)
            mode_data = mode_solver.solve()

            # --- EXTRACCIÓN FÍSICA Y FILTRADO ---
            n_eff_array = np.real(mode_data.n_eff.values.flatten())
            te_frac_array = mode_data.pol_fraction['te'].values.flatten()

            # Máscara lógica doble (AND)
            valid_te_modes = (n_eff_array > n_clad) & (te_frac_array > 0.5)

            # Conteo de modos guiados TE
            num_guided_te = np.sum(valid_te_modes)
            mode_counts.append(num_guided_te)

        # Guardar en diccionario y reportar progreso
        results[(H, wl)] = mode_counts
        print(f"Sweep completado: H = {H*1000:.0f} nm, Lambda = {wl*1000:.0f} nm")

# ------------------------------------------------------------------------------
# 3. VISUALIZACIÓN (MODE MAP)
# ------------------------------------------------------------------------------
plt.figure(figsize=(10, 6), dpi=150)

colors = {0.22: '#1f77b4', 0.30: '#d62728'}
linestyles = {1.50: '--', 1.55: '-'}

for H in thicknesses:
    for wl in wavelengths:
        label_text = f'H = {H*1000:.0f} nm, $\\lambda$ = {wl*1000:.0f} nm'
        plt.step(widths * 1000, results[(H, wl)], where='mid',
                 color=colors[H], linestyle=linestyles[wl], linewidth=2.5, label=label_text)

plt.xlabel('Waveguide Width, $W$ (nm)', fontsize=14, fontweight='bold')
plt.ylabel('Number of Guided TE Modes', fontsize=14, fontweight='bold')
plt.title('Single-TE-Mode Regime Map: SOI Platform', fontsize=16)
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(fontsize=12, loc='upper left')
plt.yticks(np.arange(0, 5, 1))
plt.xlim(200, 800)
plt.ylim(0.5, 3.5)

plt.tight_layout()
plt.show()
