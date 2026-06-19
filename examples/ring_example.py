import sys
import os

# Añadimos el directorio raíz al path para poder importar 'picdesign'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picdesign.materials import get_silicon_index
from picdesign.waveguides import approximate_single_mode_condition
from picdesign.resonators import ring_circumference_and_radius
from picdesign.lca import simple_lca_score

def main():
    print("--- PIC DESIGN: Ring Resonator Example ---")
    
    # 1. Parámetros físicos
    wl = 1.55       # um
    n_clad = 1.444  # SiO2
    width = 0.45    # um
    
    # 2. Verificación de la Guía de Onda
    n_core = get_silicon_index(wl)
    is_sm, v_num = approximate_single_mode_condition(width, n_core, n_clad, wl)
    print(f"Silicon Index at {wl}um: {n_core:.3f}")
    print(f"Is waveguide single-mode? {is_sm} (V = {v_num:.2f})")
    
    # 3. Diseño del Anillo (Target FSR = 15 nm)
    target_fsr = 15.0
    group_index = 4.2 # Típico para SOI a 1550nm
    circ, radius = ring_circumference_and_radius(target_fsr, group_index, wl)
    print(f"\nTarget FSR: {target_fsr} nm")
    print(f"Calculated Ring Radius: {radius:.3f} um")
    
    # 4. Evaluación de Sostenibilidad (LCA)
    # Supongamos que fabricamos un lote de estos chips
    print("\n--- Sustainability Check ---")
    co2 = simple_lca_score(volume_cm3=2.5, energy_kwh=300, water_liters=150, material="silicon")
    print(f"Estimated Manufacturing Carbon Footprint: {co2:.2f} kg CO2 eq")

if __name__ == "__main__":
    main()
