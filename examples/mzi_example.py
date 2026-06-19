import sys
import os
import gdsfactory as gf

# Añadimos el directorio raíz al path para poder importar 'picdesign'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picdesign.interferometers import mzi_path_length_imbalance
from picdesign.gds_helpers import attach_grating_couplers, export_to_gds

def main():
    print("--- PIC DESIGN: MZI Tape-out Example ---")
    
    # 1. Diseño Analítico del MZI
    target_fsr = 25.0  # nm
    group_index = 4.2
    wl = 1.55          # um
    
    delta_L = mzi_path_length_imbalance(target_fsr, group_index, wl)
    print(f"Target FSR: {target_fsr} nm")
    print(f"Required MZI arm imbalance (Delta L): {delta_L:.3f} um")
    
    # 2. Construcción del Layout usando gdsfactory
    # Creamos un MZI usando la diferencia de longitud calculada analíticamente
    print("\nGenerating layout...")
    base_mzi = gf.components.mzi(delta_length=delta_L)
    
    # 3. Añadir Grating Couplers y Exportar
    # Usamos nuestra función wrapper de picdesign
    final_chip = attach_grating_couplers(base_mzi)
    
    output_filename = "mzi_test_chip.gds"
    export_to_gds(final_chip, output_filename)
    
    # Para visualizar en un entorno local (opcional)
    # final_chip.show()

if __name__ == "__main__":
    main()
