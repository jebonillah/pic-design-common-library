import gdsfactory as gf

def attach_grating_couplers(device_component):
    """
    Description:
        A reusable helper function that attaches standard TE elliptical grating 
        couplers to the input and output ports of a given photonic component.
        
    Inputs:
        device_component (gdsfactory.Component): The base PIC component.
        
    Outputs:
        top_component (gdsfactory.Component): A new component containing the 
                                              device with grating couplers attached.
        
    Units:
        Spatial units in the resulting GDS are in micrometers (um).
        
    Example:
        >>> import gdsfactory as gf
        >>> wg = gf.components.straight(length=100)
        >>> wg_with_pads = attach_grating_couplers(wg)
    """
    top = gf.Component(name=f"{device_component.name}_with_GCs")
    device_inst = top << device_component
    
    gc = gf.components.grating_coupler_elliptical_te()
    gc_left = top << gc
    gc_right = top << gc
    
    gc_left.rotate(180)
    
    # Conexiones (asumiendo puertos estándar 'o1' y 'o2')
    if "o1" in device_inst.ports:
        gc_left.connect("o1", device_inst.ports["o1"])
    if "o2" in device_inst.ports:
        gc_right.connect("o1", device_inst.ports["o2"])
        
    return top

def export_to_gds(component, filename):
    """
    Description:
        Exports a given gdsfactory component to a standard GDSII file 
        ready for foundry tape-out.
        
    Inputs:
        component (gdsfactory.Component): The finalized layout component.
        filename (str): The desired output filename (e.g., 'final_chip.gds').
        
    Outputs:
        None (saves the file to the disk).
        
    Units:
        Output file is written in GDSII database units (typically nm precision).
        
    Example:
        >>> wg = gf.components.straight(length=100)
        >>> export_to_gds(wg, 'my_waveguide.gds')
    """
    if not filename.endswith('.gds'):
        filename += '.gds'
    
    component.write_gds(filename)
    print(f"✅ Layout successfully exported to {filename}")
