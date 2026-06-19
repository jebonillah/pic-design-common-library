import numpy as np
import matplotlib.pyplot as plt
from math import factorial
import gdsfactory as gf
import gplugins.tidy3d as gt

# ---------------------------------------------------------
# 1. INICIALIZACIÓN DEL PDK Y PARÁMETROS DE DISEÑO
# ---------------------------------------------------------
gf.config.rich_output()

W = 400 * 1e-3  # Waveguide width [um]
H = 200 * 1e-3  # Waveguide height [um]
wl_center_um = 0.780  # Central wavelength 780 nm
wavelengths = np.linspace(0.660, 0.850, 31) # Rango Visible / Near-IR

print(f"Iniciando simulación FDE unificada sobre {len(wavelengths)} puntos...")

# ---------------------------------------------------------
# 2. BARRIDO DEL MODE SOLVER (TE0 y TE1)
# ---------------------------------------------------------
neff_te0_vals = []
neff_te1_vals = []
aeff_vals = []

for wl in wavelengths:
    strip = gt.modes.Waveguide(
        wavelength=wl,
        core_width=W,
        core_thickness=H,
        slab_thickness=0.0,
        core_material=("Si3N4", "Luke2015Sellmeier"),
        clad_material=("SiO2", "Horiba"),
        num_modes=3 #Buscamos 3 modos para capturar TE0 y TE1
    )

    n_eff_array = np.atleast_1d(strip.n_eff)

    # Índice 0: Modo Fundamental (TE0)
    neff_te0_vals.append(float(np.real(n_eff_array[0])))

    # Índice 2: Primer Modo de Orden Superior Horizontal (TE1)

    if len(n_eff_array) > 2:
        neff_te1_vals.append(float(np.real(n_eff_array[2])))
    else:
        neff_te1_vals.append(1.453)

    a_eff_array = np.atleast_1d(strip.mode_area)
    aeff_vals.append(float(a_eff_array[0]))

neff_te0_vals = np.array(neff_te0_vals)
neff_te1_vals = np.array(neff_te1_vals)
aeff_vals = np.array(aeff_vals)

# ---------------------------------------------------------
# 3. EXTRACCIÓN DE TENSORES DE DISPERSIÓN (GNLSE INPUTS)
# ---------------------------------------------------------
c_m_s = 299792458.0
lambda_m = wavelengths * 1e-6
wl_center_m = wl_center_um * 1e-6

omega = (2 * np.pi * c_m_s) / lambda_m
omega_ps = omega * 1e-12
omega_0_ps = ((2 * np.pi * c_m_s) / wl_center_m) * 1e-12
dw = omega_ps - omega_0_ps

# Constante de Propagación usando el modo Fundamental (TE0)
beta_m = (omega * neff_te0_vals) / c_m_s
coeffs = np.polyfit(dw, beta_m, 4)

# Tensores de Dispersión
beta_0 = coeffs[4]
beta_1 = coeffs[3] * factorial(1)                # [ps/m]
beta_2 = coeffs[2] * factorial(2)                # [ps^2/m] -> GVD
beta_3 = coeffs[1] * factorial(3)                # [ps^3/m] -> TOD
beta_4 = coeffs[0] * factorial(4)                # [ps^4/m] -> FOD

# ---------------------------------------------------------
# 4. CÁLCULO DE MÉTRICAS OPERATIVAS A 780 nm
# ---------------------------------------------------------
n_eff_0 = np.interp(wl_center_um, wavelengths, neff_te0_vals)
a_eff_0 = np.interp(wl_center_um, wavelengths, aeff_vals) # [um^2]

ng_0 = c_m_s * (beta_1 * 1e-12)
A_core_um2 = W * H
Gamma = min(A_core_um2 / a_eff_0, 1.0)
alpha_total = 0.5 # [dB/cm] Heurística estándar para Si3N4

# ---------------------------------------------------------
# 5. REPORTE EN CONSOLA (TEXTO)
# ---------------------------------------------------------
print("\n" + "="*50)
print(f"  PICS DESIGN SPECS - {W*1000:.0f}x{H*1000:.0f} nm Si3N4 a {wl_center_um*1000:.0f} nm")
print("="*50)
print(f"1. Effective Index (n_eff):   {n_eff_0:.4f}")
print(f"2. Group Index (n_g):         {ng_0:.4f}")
print(f"3. Confinement Factor (Γ):    {Gamma*100:.2f} %")
print(f"   - Effective Area (A_eff):  {a_eff_0:.4f} um^2")
print(f"4. Dispersion Coefficients:")
print(f"   - Beta_2 (GVD):            {beta_2:.4e} ps^2/m")
print(f"   - Beta_3 (TOD):            {beta_3:.4e} ps^3/m")
print(f"   - Beta_4 (FOD):            {beta_4:.4e} ps^4/m")
print(f"5. Propagation Loss:")
print(f"   - Total Est. (w/ Scatter): {alpha_total:.2f} dB/cm")
print("="*50)

# ---------------------------------------------------------
# 6. VISUALIZACIÓN PROBATORIA (GRÁFICA PARA EL REPORTE)
# ---------------------------------------------------------
n_clad_approx = 1.453 # Índice típico del Cladding

plt.figure(figsize=(9, 6))
# Graficamos TE0 y TE1
plt.plot(wavelengths * 1000, neff_te0_vals, 'b-', linewidth=2.5, label='$TE_0$ (Fundamental Mode)')
plt.plot(wavelengths * 1000, neff_te1_vals, 'g--', linewidth=2.5, label='$TE_1$ (Higher-Order Horizontal)')

# Líneas de referencia
plt.axhline(y=n_clad_approx, color='k', linestyle=':', linewidth=2, label='Cladding Index ($SiO_2$)')
plt.axvline(x=780, color='gray', linestyle='-.', alpha=0.7, label='$\lambda_0 = 780$ nm')

# Zona de Cut-off
plt.fill_between(wavelengths * 1000, 1.4, n_clad_approx, color='red', alpha=0.1)
plt.text(670, 1.445, 'Cut-off Region (Radiation)', color='darkred', fontweight='bold')

# Configuración estética de la gráfica
plt.xlabel('Wavelength (nm)', fontsize=12, fontweight='bold')
plt.ylabel('Effective Index ($n_{eff}$)', fontsize=12, fontweight='bold')
plt.title('TE-Polarization Single-Mode Verification: $400 \\times 200$ nm $Si_3N_4$', fontsize=14)
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)
plt.ylim(1.4, max(neff_te0_vals) + 0.05)
plt.tight_layout()

# Forzamos la renderización de la gráfica
plt.show()
