import numpy as np

def mzi_path_length_imbalance(target_fsr, group_index, wavelength):
    """
    Description:
        Calculates the required path-length difference (delta L) between the 
        two arms of a Mach-Zehnder Interferometer (MZI) to achieve a target FSR.
        
    Inputs:
        target_fsr (float): The desired wavelength spacing between transmission peaks.
        group_index (float): The group refractive index (n_g) of the waveguide.
        wavelength (float): The central operating vacuum wavelength.
        
    Outputs:
        delta_L (float): The required path-length imbalance.
        
    Units:
        target_fsr must be in nanometers (nm).
        wavelength must be in micrometers (um).
        delta_L is returned in micrometers (um).
        
    Example:
        >>> mzi_path_length_imbalance(50.0, 4.2, 1.55)
        11.438095238095238
    """
    # The physics of an MZI is mathematically identical to a ring resonator
    # for the FSR relation: delta_L = lambda^2 / (n_g * FSR)
    target_fsr_um = target_fsr / 1000.0
    delta_L = (wavelength**2) / (group_index * target_fsr_um)
    
    return delta_L
