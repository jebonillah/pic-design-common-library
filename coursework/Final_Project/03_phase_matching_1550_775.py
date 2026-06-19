import gdsfactory as gf
import gplugins.tidy3d as gt
import matplotlib.pyplot as plt
import numpy as np
from gdsfactory.generic_tech import get_generic_pdk

# 1. SETUP DE ENTORNO
gf.config.rich_output()
PDK = get_generic_pdk()
PDK.activate()

# 2. DEFINICIÓN DE PARÁMETROS FÍSICOS
nm = 1e-3
w_fund = 1.55    # Wavelength TM0 (Fundamental)
w_shg = 0.775    # Wavelength TM2 (Second Harmonic)
t_aln = 800 * nm
s_angle_rad = np.radians(10.0)

# Índices aproximados del Cladding (SiO2) considerando dispersión material
n_clad_1550 = 1.444
n_clad_775 = 1.453

# Vector de Widths: 0.2 um a 1.4 um (200 nm a 1400 nm)
widths = np.linspace(200, 1400, 15) * nm

# Matrices de almacenamiento
n_rect_tm0_1550, n_rect_tm2_775 = [], []
n_trap_tm0_1550, n_trap_tm2_775 = [], []

print("Iniciando barrido paramétrico Dual-Wavelength (Phase Matching)...")

for i, w in enumerate(widths):
    print(f"Resolviendo paso {i+1}/15: Width = {w/nm:.0f} nm")

    # ==========================================
    # A. SIMULACIONES A 1550 nm (Buscando TM0)
    # ==========================================
    rect_1550 = gt.modes.Waveguide(
        wavelength=w_fund, core_width=w, core_thickness=t_aln,
        core_material=2.1, clad_material="sio2", num_modes=4
    )
    trap_1550 = gt.modes.Waveguide(
        wavelength=w_fund, core_width=w, core_thickness=t_aln, sidewall_angle=s_angle_rad,
        core_material=2.1, clad_material="sio2", num_modes=4
    )

    # Extracción TM0 (Usualmente Mode 1 a 1550nm)
    try: n_rect_tm0_1550.append(rect_1550.n_eff[1])
    except IndexError: n_rect_tm0_1550.append(np.nan)

    try: n_trap_tm0_1550.append(trap_1550.n_eff[1])
    except IndexError: n_trap_tm0_1550.append(np.nan)

    # ==========================================
    # B. SIMULACIONES A 775 nm (Buscando TM2)
    # ==========================================
    # Nota: A 775nm, aumentamos num_modes porque hay más modos guiados
    rect_775 = gt.modes.Waveguide(
        wavelength=w_shg, core_width=w, core_thickness=t_aln,
        core_material=2.1, clad_material="sio2", num_modes=8
    )
    trap_775 = gt.modes.Waveguide(
        wavelength=w_shg, core_width=w, core_thickness=t_aln, sidewall_angle=s_angle_rad,
        core_material=2.1, clad_material="sio2", num_modes=8
    )

    # Extracción TM2 (Usualmente Mode 5, pero sujeto a hibridación)
    try: n_rect_tm2_775.append(rect_775.n_eff[6])
    except IndexError: n_rect_tm2_775.append(np.nan)

    try: n_trap_tm2_775.append(trap_775.n_eff[6])
    except IndexError: n_trap_tm2_775.append(np.nan)

# 3. VISUALIZACIÓN DE RESULTADOS (2 GRÁFICAS)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=False)

# --- Gráfica 1: Guía Rectangular ---
ax1.plot(widths / nm, n_rect_tm0_1550, 'b-o', linewidth=2, label='TM0 @ 1550 nm')
ax1.plot(widths / nm, n_rect_tm2_775, 'r-s', linewidth=2, label='TM2 @ 775 nm')
ax1.axhline(n_clad_1550, color='blue', linestyle=':', alpha=0.6, label='Cut-off 1550nm')
ax1.axhline(n_clad_775, color='red', linestyle=':', alpha=0.6, label='Cut-off 775nm')

ax1.set_title('Geometric Dispersion: Rectangular AlN', fontsize=12)
ax1.set_xlabel('Waveguide Width (nm)', fontsize=11)
ax1.set_ylabel('Effective Index ($n_{eff}$)', fontsize=11)
ax1.legend(loc='best')
ax1.grid(True, alpha=0.4)

# --- Gráfica 2: Guía Trapezoidal ---
ax2.plot(widths / nm, n_trap_tm0_1550, 'b--^', linewidth=2, label='TM0 @ 1550 nm (Trap)')
ax2.plot(widths / nm, n_trap_tm2_775, 'r--d', linewidth=2, label='TM2 @ 775 nm (Trap)')
ax2.axhline(n_clad_1550, color='blue', linestyle=':', alpha=0.6)
ax2.axhline(n_clad_775, color='red', linestyle=':', alpha=0.6)

ax2.set_title(f'Geometric Dispersion: Trapezoidal AlN ($\\theta = 10^\\circ$)', fontsize=12)
ax2.set_xlabel('Waveguide Base Width (nm)', fontsize=11)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.4)

plt.tight_layout()
plt.show()
