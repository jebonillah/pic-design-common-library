import gdsfactory as gf
import gplugins.tidy3d as gt
import matplotlib.pyplot as plt
import numpy as np
from gdsfactory.generic_tech import get_generic_pdk

# 1. SETUP INICIAL
gf.config.rich_output()
PDK = get_generic_pdk()
PDK.activate()

nm = 1e-3
wavelength = 1.55
w_base = 800 * nm
t_aln = 400 * nm
s_angle_deg = 10.0
s_angle_rad = np.radians(s_angle_deg)

# Definición de materiales (Asegúrate que 'si', 'aln' y 'sio2' estén en tu PDK o usa índices)
# n_si = 3.48, n_aln = 2.1, n_sio2 = 1.44

# 2. GUÍA RECTANGULAR (AlN/SiO2/Si)
rect_wg = gt.modes.Waveguide(
    wavelength=wavelength,
    core_width=w_base,
    core_thickness=t_aln,
    core_material=2.1,
    clad_material="sio2", # Tidy3D asume este cladding alrededor del core
    num_modes=4
)

# 3. GUÍA TRAPEZOIDAL (AlN/SiO2/Si)
trap_wg = gt.modes.Waveguide(
    wavelength=wavelength,
    core_width=w_base,
    core_thickness=t_aln,
    sidewall_angle=s_angle_rad,
    core_material=2.1,
    clad_material="sio2",
    num_modes=4
)

# Visualización para verificar la geometría rectangular
print(f"Visualizando geometría rectangular")
rect_wg.plot_index()
plt.show()

# Visualización para verificar la geometría trapezoidal
print(f"Visualizando geometría trapezoidal (Angle: {s_angle_deg} deg)...")
trap_wg.plot_index()
plt.show()

# Extracción de n_eff para comparar
print(f"n_eff Rectangular (Mode 0,1): {rect_wg.n_eff[:2]}")
print(f"n_eff Trapezoidal (Mode 0,1): {trap_wg.n_eff[:2]}")

# Observación de los modos TM solicitados (TM0 suele ser index 1 en esta geometría)
print("Graficando campo Ey (TM0) en guía rectangular...")
rect_wg.plot_field(field_name="Ey", mode_index=1)
plt.show()

print("Graficando campo Ey (TM0) en guía trapezoidal...")
trap_wg.plot_field(field_name="Ey", mode_index=1)
plt.show()
