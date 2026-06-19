import numpy as np

def calculate_fsr(group_index, length, wavelength):
    """
    Description:
        Calculates the Free Spectral Range (FSR) of a resonant cavity (like a ring)
        based on its physical length and the group index of the waveguide mode.
        
    Inputs:
        group_index (float): The group refractive index (n_g) of the mode.
        length (float): The round-trip length (circumference) of the cavity.
        wavelength (float): The central operating vacuum wavelength.
        
    Outputs:
        fsr (float): The Free Spectral Range.
        
    Units:
        length and wavelength must be in micrometers (um).
        group_index is dimensionless.
        fsr is returned in nanometers (nm).
        
    Example:
        >>> calculate_fsr(4.2, 100.0, 1.55)
        5.719047619047619
    """
    # FSR in wavelength domain: delta_lambda = lambda^2 / (n_g * L)
    # Since lambda and L are in um, the result is in um. Multiply by 1000 for nm.
    fsr_um = (wavelength**2) / (group_index * length)
    return fsr_um * 1000.0

def ring_circumference_and_radius(target_fsr, group_index, wavelength):
    """
    Description:
        Calculates the required circumference and radius of a ring resonator 
        to achieve a specific target Free Spectral Range (FSR).
        
    Inputs:
        target_fsr (float): The desired Free Spectral Range.
        group_index (float): The group refractive index (n_g) of the mode.
        wavelength (float): The central operating vacuum wavelength.
        
    Outputs:
        circumference (float): The total round-trip length of the ring.
        radius (float): The physical radius of the ring.
        
    Units:
        target_fsr must be in nanometers (nm).
        wavelength must be in micrometers (um).
        circumference and radius are returned in micrometers (um).
        
    Example:
        >>> ring_circumference_and_radius(20.0, 4.2, 1.55)
        (28.595238095238095, 4.551073167198126)
    """
    # Convert FSR to um for calculation
    target_fsr_um = target_fsr / 1000.0
    
    # L = lambda^2 / (n_g * delta_lambda)
    circumference = (wavelength**2) / (group_index * target_fsr_um)
    radius = circumference / (2 * np.pi)
    
    return circumference, radius
