# 📖 Guía de Uso: PIC Design Common Library

Bienvenido a la guía de uso de la librería. Aquí encontrarás ejemplos prácticos de cómo utilizar los módulos físicos y analíticos para diseñar circuitos fotónicos pasivos.

## 1. Diseño de Guías de Onda (Waveguides)

Antes de simular, puedes usar métodos analíticos para estimar si tu guía de onda de silicio es monomodo y estimar sus pérdidas.

```python
from picdesign.waveguides import approximate_single_mode_condition, convert_propagation_loss
from picdesign.materials import get_silicon_index

# Definir parámetros
wavelength = 1.55  # um
n_core = get_silicon_index(wavelength)
n_clad = 1.444     # SiO2
width = 0.45       # um

# 1. Verificar condición monomodo
is_single, v_num = approximate_single_mode_condition(width, n_core, n_clad, wavelength)
print(f"¿Es monomodo?: {is_single} (V = {v_num:.2f})")

# 2. Convertir pérdidas de literatura (ej. 2.5 dB/cm a m^-1)
loss_m1 = convert_propagation_loss(2.5, to_db_per_cm=False)
print(f"Pérdida de propagación: {loss_m1:.2f} m^-1")

from picdesign.resonators import ring_circumference_and_radius
from picdesign.interferometers import mzi_path_length_imbalance

target_fsr_nm = 20.0  # FSR deseado
group_index = 4.2     # n_g típico del silicio a 1550nm
wavelength = 1.55     # um

# Calcular radio del anillo
circ, radius = ring_circumference_and_radius(target_fsr_nm, group_index, wavelength)
print(f"Para un FSR de 20nm, el radio del anillo debe ser: {radius:.2f} um")

# Calcular desbalance del MZI
delta_L = mzi_path_length_imbalance(target_fsr_nm, group_index, wavelength)
print(f"Para un FSR de 20nm, el desbalance del MZI (Delta L) es: {delta_L:.2f} um")

from picdesign.lca import simple_lca_score

# Supongamos un proceso litográfico para un chip pequeño
volumen_si = 0.5   # cm^3 de Silicio procesado
energia = 120.0    # kWh usados en el cleanroom
agua = 50.0        # Litros de agua ultrapura

co2_emissions = simple_lca_score(volumen_si, energia, agua, material="silicon")
print(f"Huella de Carbono estimada: {co2_emissions:.2f} kg CO2 eq")

import gdsfactory as gf
from picdesign.gds_helpers import attach_grating_couplers, export_to_gds

# Crear un componente base
mi_guia = gf.components.straight(length=100)

# Añadir Grating Couplers automáticamente
chip_final = attach_grating_couplers(mi_guia)

# Exportar a GDS
export_to_gds(chip_final, "mi_primer_chip.gds")
