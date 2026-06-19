import numpy as np
import matplotlib.pyplot as plt
import tidy3d as td
from tidy3d.plugins.mode import ModeSolver

print("Iniciando laboratorio computacional SPDC (Análisis Espectral)...")

# ==========================================
# 1. PARÁMETROS GEOMÉTRICOS Y FÍSICOS
# ==========================================
w_pm = 1.100      # Width base
t_aln = 0.800     # Thickness
s_angle_rad = np.radians(10.0)

# Barrido de longitudes de onda (en micras)
num_points = 21   # Resolución del barrido espectral (10 es el centro exacto a 1.55)
wl_signal_arr = np.linspace(1.500, 1.600, num_points)
wl_pump_arr = wl_signal_arr / 2.0

# Conversión a frecuencias para el solver de Tidy3D
freqs_signal = td.C_0 / wl_signal_arr
freqs_pump = td.C_0 / wl_pump_arr

w_top = w_pm - 2 * t_aln * np.tan(s_angle_rad)
vertices = [(-w_pm/2, -t_aln/2), (w_pm/2, -t_aln/2), (w_top/2, t_aln/2), (-w_top/2, t_aln/2)]

mat_aln = td.Medium(permittivity=2.1**2)
mat_sio2 = td.Medium(permittivity=1.444**2)

core = td.Structure(
    geometry=td.PolySlab(vertices=vertices, slab_bounds=(-td.inf, td.inf), axis=2),
    medium=mat_aln
)

# ==========================================
# 2. CONFIGURACIÓN DEL SOLVER (FDE 2D)
# ==========================================
domain_size = (3.0, 3.0, 0)
plane = td.Box(center=(0, 0, 0), size=domain_size)
grid = td.GridSpec.uniform(dl=0.01)

boundaries_2d = td.BoundarySpec(
    x=td.Boundary.pml(),
    y=td.Boundary.pml(),
    z=td.Boundary.periodic()
)

sim_pump = td.Simulation(
    size=domain_size, grid_spec=grid, structures=[core],
    medium=mat_sio2, run_time=1e-12, boundary_spec=boundaries_2d
)
sim_signal = td.Simulation(
    size=domain_size, grid_spec=grid, structures=[core],
    medium=mat_sio2, run_time=1e-12, boundary_spec=boundaries_2d
)

solver_pump = ModeSolver(
    simulation=sim_pump, plane=plane,
    mode_spec=td.ModeSpec(num_modes=8, target_neff=2.1), freqs=freqs_pump.tolist()
)
solver_signal = ModeSolver(
    simulation=sim_signal, plane=plane,
    mode_spec=td.ModeSpec(num_modes=4, target_neff=2.1), freqs=freqs_signal.tolist()
)

print(f"Calculando campos electromagnéticos para {num_points} longitudes de onda...")
data_pump = solver_pump.solve()
data_signal = solver_signal.solve()

# ==========================================
# 3. CREACIÓN DE LA MÁSCARA ESPACIAL GEOMÉTRICA
# ==========================================
x_coords = data_pump.Ey.coords['x'].values
y_coords = data_pump.Ey.coords['y'].values
dx = np.abs(x_coords[1] - x_coords[0])
dy = np.abs(y_coords[1] - y_coords[0])
dA = dx * dy

X, Y = np.meshgrid(x_coords, y_coords, indexing='ij')
local_half_width = (w_pm / 2) - (Y - (-t_aln/2)) * np.tan(s_angle_rad)
chi2_mask = (Y >= -t_aln/2) & (Y <= t_aln/2) & (X >= -local_half_width) & (X <= local_half_width)
chi2_mask = chi2_mask.astype(float)

# ==========================================
# 4. EXTRACCIÓN Y CÁLCULO EN BUCLE (SWEEP)
# ==========================================
index_pump = 6   # TM2
index_signal = 1 # TM0

Gamma_NL_list = []

print("Integrando modos a lo largo del espectro...")
for i in range(num_points):
    Ey_pump = np.squeeze(data_pump.Ey.isel(mode_index=index_pump, f=i).values)
    Ey_signal = np.squeeze(data_signal.Ey.isel(mode_index=index_signal, f=i).values)

    raw_integrand = np.conj(Ey_pump) * (Ey_signal ** 2)
    masked_integrand = raw_integrand * chi2_mask

    numerator = np.abs(np.sum(masked_integrand) * dA)

    norm_pump = np.sqrt(np.sum(np.abs(Ey_pump)**2) * dA)
    norm_signal = np.sum(np.abs(Ey_signal)**2) * dA
    denominator = norm_pump * norm_signal

    Gamma_NL = numerator / denominator
    Gamma_NL_list.append(Gamma_NL)

# Extraemos los campos centrales para la gráfica de perfiles
mid_idx = num_points // 2
Ey_pump_center = np.squeeze(data_pump.Ey.isel(mode_index=index_pump, f=mid_idx).values)
Ey_signal_center = np.squeeze(data_signal.Ey.isel(mode_index=index_signal, f=mid_idx).values)
masked_integrand_center = np.abs(np.conj(Ey_pump_center) * (Ey_signal_center ** 2) * chi2_mask)


# ==========================================
# 5. REPORTE Y VISUALIZACIÓN FINAL
# ==========================================

# Gráfica 1: Comportamiento Espectral del Overlap
plt.figure(figsize=(8, 5))
plt.plot(wl_signal_arr * 1000, Gamma_NL_list, 'b-o', linewidth=2, markersize=6)
plt.title('Bandwidth Analysis: Spatial Overlap vs Wavelength', fontsize=14)
plt.xlabel('Signal Wavelength (nm)', fontsize=12)
plt.ylabel(r'Spatial Overlap $\Gamma_{NL}$ ($\mu m^{-2}$)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# NUEVO: Imprimimos el valor exacto a la longitud de onda central en la consola
Gamma_NL_center = Gamma_NL_list[mid_idx]
central_wl_s = wl_signal_arr[mid_idx] * 1000

print("\n" + "="*60)
print(f" REPORT DATA: SPDC OVERLAP @ {central_wl_s:.0f} nm")
print("="*60)
print(f"-> Spatial Overlap (Gamma_NL) : {Gamma_NL_center:.4e} (1/um^2)")
print("="*60 + "\n")

# Gráfica 2: Perfiles Modales a la Longitud de Onda Central
figM, axes = plt.subplots(1, 3, figsize=(16, 4.5))

Ey_pump_2d = np.abs(Ey_pump_center).T
Ey_signal_2d = np.abs(Ey_signal_center).T
masked_integrand_2d = masked_integrand_center.T

central_wl_p = wl_pump_arr[mid_idx] * 1000

im0 = axes[0].imshow(Ey_pump_2d, cmap='inferno', origin='lower', extent=[x_coords[0], x_coords[-1], y_coords[0], y_coords[-1]])
axes[0].set_title(f'$|E_{{y, pump}}|$ (TM2 @ {central_wl_p:.0f}nm)', fontsize=12)
plt.colorbar(im0, ax=axes[0])

im1 = axes[1].imshow(Ey_signal_2d, cmap='inferno', origin='lower', extent=[x_coords[0], x_coords[-1], y_coords[0], y_coords[-1]])
axes[1].set_title(f'$|E_{{y, signal}}|$ (TM0 @ {central_wl_s:.0f}nm)', fontsize=12)
plt.colorbar(im1, ax=axes[1])

im2 = axes[2].imshow(masked_integrand_2d, cmap='viridis', origin='lower', extent=[x_coords[0], x_coords[-1], y_coords[0], y_coords[-1]])
axes[2].set_title(f'SPDC Generation (Masked @ {central_wl_s:.0f}nm)', fontsize=12)
plt.colorbar(im2, ax=axes[2])

for ax in axes:
    ax.set_xlim([-0.8, 0.8])
    ax.set_ylim([-0.6, 0.6])
    ax.set_xlabel(r'x ($\mu m$)')
    ax.set_ylabel(r'y ($\mu m$)')

    x_wg = [-w_pm/2, w_pm/2, w_top/2, -w_top/2, -w_pm/2]
    y_wg = [-t_aln/2, -t_aln/2, t_aln/2, t_aln/2, -t_aln/2]
    ax.plot(x_wg, y_wg, 'w--', alpha=0.8, linewidth=2.0)

plt.tight_layout()
plt.show()
