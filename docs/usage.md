# 📖 Guía de Uso: PIC Design Common Library

Bienvenido a la guía de uso oficial de la librería `picdesign`. Este documento proporciona ejemplos prácticos y secuenciales de cómo utilizar los módulos físicos, analíticos y de sostenibilidad para diseñar Circuitos Integrados Fotónicos (PICs) pasivos.

---

## 1. Diseño Analítico de Guías de Onda (Waveguides)

Antes de lanzar una costosa simulación numérica, puedes utilizar nuestros métodos analíticos para estimar si tu guía de onda de silicio cumple con la condición de monomodo y convertir métricas de pérdidas.

```python
from picdesign.waveguides import approximate_single_mode_condition, convert_propagation_loss
from picdesign.materials import get_silicon_index

# Definir parámetros físicos para la banda C (Telecom)
wavelength = 1.55  # um
n_core = get_silicon_index(wavelength)
n_clad = 1.444     # Índice aproximado del SiO2
width = 0.45       # um (Ancho típico de la guía)

# 1. Verificar condición monomodo
is_single, v_num = approximate_single_mode_condition(width, n_core, n_clad, wavelength)
print(f"¿Es monomodo?: {is_single} (Frecuencia Normalizada V = {v_num:.2f})")

# 2. Convertir pérdidas reportadas en la literatura (ej. 2.5 dB/cm a m^-1)
loss_m1 = convert_propagation_loss(2.5, to_db_per_cm=False)
print(f"Pérdida de propagación lineal: {loss_m1:.2f} m^-1")

```

## 2. Diseño de Resonadores e Interferómetros
Para aplicaciones de filtrado o sensado, el Rango Espectral Libre (FSR) es un parámetro crítico. Utiliza estos módulos para calcular las dimensiones físicas exactas (radios y desbalances) a partir de tu FSR objetivo.

```python
from picdesign.resonators import ring_circumference_and_radius
from picdesign.interferometers import mzi_path_length_imbalance

target_fsr_nm = 20.0  # FSR objetivo deseado
group_index = 4.2     # n_g típico del silicio a 1550 nm
wavelength = 1.55     # um

# Calcular dimensiones del Microrresonador en Anillo
circ, radius = ring_circumference_and_radius(target_fsr_nm, group_index, wavelength)
print(f"Para un FSR de 20 nm, el radio del anillo debe ser: {radius:.2f} um")

# Calcular desbalance del Mach-Zehnder Interferometer (MZI)
delta_L = mzi_path_length_imbalance(target_fsr_nm, group_index, wavelength)
print(f"Para un FSR de 20 nm, el desbalance de los brazos del MZI (Delta L) es: {delta_L:.2f} um")
```

## 3. Evaluación de Sostenibilidad (Life Cycle Assessment - LCA)
Integrar métricas de sostenibilidad en la fase de diseño es fundamental (Lab 5). Esta librería incluye una calculadora LCA simplificada para estimar la huella de carbono de tu chip durante su fabricación en la foundry.

```python
from picdesign.lca import simple_lca_score

# Datos estimados de un proceso litográfico para un lote de chips
volumen_si = 0.5   # cm^3 de Silicio procesado
energia = 120.0    # kWh de electricidad usados en el cleanroom
agua = 50.0        # Litros de agua ultrapura consumidos

# Calcular impacto ambiental
co2_emissions = simple_lca_score(volumen_si, energia, agua, material="silicon")
print(f"Huella de Carbono estimada del proceso: {co2_emissions:.2f} kg CO2 eq")
```

## 4. Ensamblaje y Exportación a GDSII (Tape-out)
Una vez que las dimensiones analíticas están validadas, puedes integrarlas con gdsfactory para generar la máscara de fotolitografía. Nuestras funciones de ayuda automatizan la inserción de acopladores (Grating Couplers) y la exportación.

```python
import gdsfactory as gf
from picdesign.gds_helpers import attach_grating_couplers, export_to_gds

# 1. Crear un componente base (ej. una guía recta simple usando las dimensiones calculadas)
mi_guia = gf.components.straight(length=100)

# 2. Añadir Grating Couplers automáticamente a los puertos
chip_final = attach_grating_couplers(mi_guia)

# 3. Exportar el layout final a GDSII para la fábrica
export_to_gds(chip_final, "mi_primer_chip_tapeout.gds")
