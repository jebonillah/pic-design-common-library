import gdsfactory as gf

# 1. BUENA PRÁCTICA CRÍTICA: Limpiar el caché del layout para evitar colisiones en Colab
gf.clear_cache()

# Aseguramos la visualización
gf.config.rich_output()

def attach_grating_couplers_horizontal_manual(device_component):
    """
    Función reutilizable para añadir Grating Couplers a cualquier PIC,
    forzando una configuración HORIZONTAL.
    """
    # 2. Dejamos que gdsfactory genere un nombre único
    top = gf.Component()

    # Instanciamos el dispositivo base
    device_inst = top << device_component

    # Instanciamos dos Grating Couplers estándar
    gc = gf.components.grating_coupler_elliptical_te()
    gc_left = top << gc
    gc_right = top << gc

    # Manipulación Geométrica
    gc_left.rotate(180)

    # Conexiones
    gc_left.connect("o1", device_inst.ports["o1"])

    if "o2" in device_inst.ports:
        gc_right.connect("o1", device_inst.ports["o2"])

    return top

# --- PRUEBA DEL CÓDIGO ---
if __name__ == "__main__":
    dummy_waveguide = gf.components.straight(length=100, width=0.5)
    test_structure_horizontal = attach_grating_couplers_horizontal_manual(dummy_waveguide)

    test_structure_horizontal.plot()
    # Guarda el diseño en un archivo GDSII estándar
    test_structure_horizontal.write_gds("Test_Horizontal_GCS.gds")
    print("Diseño guardado con éxito como 'Test_Horizontal_GCS.gds'")
