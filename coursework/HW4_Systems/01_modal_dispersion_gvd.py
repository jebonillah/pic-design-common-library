import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
from scipy.signal import savgol_filter

import gdsfactory as gf
import gplugins.tidy3d as gt
from gdsfactory.generic_tech import get_generic_pdk

# ---------------------------------------------------------
# 1. INICIALIZACIÓN DEL PDK Y GDSFACTORY
# ---------------------------------------------------------
gf.config.rich_output()
PDK = get_generic_pdk()
PDK.activate()

# Definición de unidades
nm = 1e-3
um = 1.0

# Parámetros de la Silicon Waveguide (Régimen Single-mode TE usado en la HW2)
W = 410 * nm
H = 220 * nm

# Vector de longitudes de onda de barrido (C-band y L-band)
wavelengths = np.linspace(1.500, 1.600, 21) # 21 puntos para asegurar resolución diferencial

print(f"Iniciando barrido modal paramétrico sobre {len(wavelengths)} puntos...")

neff_vals = []

# ---------------------------------------------------------
# 2. BARRIDO DEL MODE SOLVER UTILIZANDO GPLUGINS (CORREGIDO V2)
# ---------------------------------------------------------
for wl in wavelengths:
    # Definición de la estructura modal transversal
    strip = gt.modes.Waveguide(
        wavelength=wl,
        core_width=W,
        core_thickness=H,
        slab_thickness=0.0,
        core_material="si",
        clad_material="sio2",
        num_modes=1 # Extracción exclusiva del modo fundamental TE-like
    )

    n_eff_array = np.atleast_1d(strip.n_eff)
    n_eff_real = float(np.real(n_eff_array[0]))

    neff_vals.append(n_eff_real)

neff_vals = np.array(neff_vals)

# ---------------------------------------------------------
# 3. DERIVACIÓN ROBUSTA: EXPANSIÓN DE TAYLOR CENTRADA (PDK EXTRACTION METHOD)
# ---------------------------------------------------------
# Definimos la longitud de onda central
wl_center = 1.55 # um

# 1. Centramos el eje X para garantizar estabilidad numérica extrema
x = wavelengths - wl_center

# 2. Ajuste polinomial de grado 2 (Expansión de Taylor de 2do orden)
coeffs = np.polyfit(x, neff_vals, 2)

# Reconstruimos la curva suavizada
neff_smooth = np.polyval(coeffs, x)

# 3. Derivadas Analíticas Exactas a partir del polinomio centrado
dneff_dl = 2 * coeffs[0] * x + coeffs[1]
d2neff_dl2 = 2 * coeffs[0] * np.ones_like(x)

# 4. Cálculo Físico de Métricas
# Group Index (ng)
ng_vals = neff_smooth - wavelengths * dneff_dl

# Group Velocity Dispersion (Beta_2)
c_m_s = 299792458.0 # Velocidad de la luz [m/s]
lambda_m = wavelengths * 1e-6 # Wavelength en metros [m]

d2neff_dl2_m2 = d2neff_dl2 * 1e12 # Conversión a [1/m^2]
beta2_ps2_m = (lambda_m**3 / (2 * np.pi * c_m_s**2)) * d2neff_dl2_m2 * 1e24 # a [ps^2/m]

# Sobrescribimos para la gráfica
neff_vals = neff_smooth

# ---------------------------------------------------------
# 4. VISUALIZACIÓN DE MÉTRICAS ÓPTICAS
# ---------------------------------------------------------

# --- GRÁFICA 1: Effective Index y Group Index ---
fig1, ax1 = plt.subplots(figsize=(8, 5))

color1 = 'tab:blue'
ax1.set_xlabel('Wavelength (nm)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Effective Index ($n_{eff}$)', color=color1, fontsize=12, fontweight='bold')
ax1.plot(wavelengths * 1000, neff_vals, color=color1, linewidth=2.5, label='$n_{eff}$')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

ax1_twin = ax1.twinx()
color2 = 'tab:red'
ax1_twin.set_ylabel('Group Index ($n_g$)', color=color2, fontsize=12, fontweight='bold')
ax1_twin.plot(wavelengths * 1000, ng_vals, color=color2, linestyle='--', linewidth=2.5, label='$n_g$')
ax1_twin.tick_params(axis='y', labelcolor=color2)

plt.title(f'Modal Dispersions for {W*1000:.0f}x{H*1000:.0f} nm SOI Waveguide', fontsize=14)
fig1.tight_layout()

# --- GRÁFICA 2: Parámetro Beta 2 (GVD) ---
fig2, ax2 = plt.subplots(figsize=(8, 5))

color3 = 'tab:green'
ax2.set_xlabel('Wavelength (nm)', fontsize=12, fontweight='bold')
ax2.set_ylabel('GVD $\\beta_2$ ($ps^2/m$)', color=color3, fontsize=12, fontweight='bold')
ax2.plot(wavelengths * 1000, beta2_ps2_m, color=color3, linewidth=2.5)
ax2.tick_params(axis='y', labelcolor=color3)
ax2.grid(True, alpha=0.3)
ax2.axhline(0, color='black', linestyle=':', linewidth=1.5) # Línea de Zero-Dispersion

plt.title('Group Velocity Dispersion ($\\beta_2$)', fontsize=14)
fig2.tight_layout()
