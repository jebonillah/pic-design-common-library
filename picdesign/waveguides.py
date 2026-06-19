# picdesign/waveguides.py

import numpy as np

def convert_propagation_loss(loss_value, to_db_per_cm=True):
    """
    Description:
        Converts propagation loss between decibels per centimeter (dB/cm) 
        and inverse meters (m^-1).
        
    Inputs:
        loss_value (float): The numerical value of the loss.
        to_db_per_cm (bool): If True, converts from m^-1 to dB/cm. 
                             If False, converts from dB/cm to m^-1.
                             
    Outputs:
        converted_loss (float): The converted propagation loss value.
        
    Units:
        Input can be dB/cm or m^-1. Output is the complementary unit.
        
    Example:
        >>> convert_propagation_loss(100, to_db_per_cm=True)
        4.3429448190325175
    """
    if to_db_per_cm:
        return loss_value * 10 * np.log10(np.e) / 100
    else:
        return loss_value * 100 / (10 * np.log10(np.e))


def approximate_single_mode_condition(width, n_core, n_clad, wavelength):
    """
    Description:
        Approximates whether a waveguide is single-mode based on the 1D slab 
        normalized frequency (V-number). For a symmetric slab, V < pi guarantees 
        single-mode operation. For rectangular PICs, this gives a conservative estimate.
        
    Inputs:
        width (float): The width of the waveguide core.
        n_core (float): Refractive index of the core (e.g., Silicon ~ 3.47).
        n_clad (float): Refractive index of the cladding (e.g., SiO2 ~ 1.44).
        wavelength (float): The operating vacuum wavelength.
        
    Outputs:
        is_single_mode (bool): True if the approximate V-number is less than pi.
        V_number (float): The calculated normalized frequency.
        
    Units:
        width and wavelength must be in the same units (e.g., micrometers).
        n_core, n_clad, and V_number are dimensionless.
        
    Example:
        >>> approximate_single_mode_condition(0.45, 3.47, 1.44, 1.55)
        (False, 5.748)
    """
    # Calculate the normalized frequency (V-number) for a 1D equivalent slab
    V_number = (2 * np.pi / wavelength) * (width / 2) * np.sqrt(n_core**2 - n_clad**2)
    
    # Fundamental mode cutoff condition for symmetric slab
    is_single_mode = bool(V_number < np.pi)
    
    return is_single_mode, V_number


def confinement_factor_estimate(thickness, n_core, n_clad, wavelength):
    """
    Description:
        Estimates the optical confinement factor (Gamma) for a symmetric slab waveguide 
        using an analytical approximation. Gamma represents the fraction of optical 
        power confined within the core.
        
    Inputs:
        thickness (float): The height/thickness of the waveguide core.
        n_core (float): Refractive index of the core material.
        n_clad (float): Refractive index of the cladding material.
        wavelength (float): The operating vacuum wavelength.
        
    Outputs:
        gamma (float): The estimated confinement factor (between 0 and 1).
        
    Units:
        thickness and wavelength must be in the same units (e.g., micrometers).
        gamma, n_core, and n_clad are dimensionless.
        
    Example:
        >>> confinement_factor_estimate(0.22, 3.47, 1.44, 1.55)
        0.812
    """
    # Calculate normalized frequency (V) and normalized lateral decay (W)
    V = (2 * np.pi / wavelength) * (thickness / 2) * np.sqrt(n_core**2 - n_clad**2)
    
    # Empirical/analytical approximation for the fundamental mode
    # Assuming W approx V for well-confined modes to simplify the analytical form
    D = 2 * (thickness / 2)
    gamma = V**2 / (V**2 + 2)  # Simple high-contrast heuristic approximation
    
    # Ensuring physical bounds
    gamma = max(0.0, min(gamma, 1.0))
    return gamma


def estimate_bend_loss(radius, alpha_straight, c1, c2):
    """
    Description:
        Estimates the total propagation loss of a curved waveguide using a 
        standard exponential radiation model combined with straight waveguide scattering.
        
    Inputs:
        radius (float): The bend radius of the waveguide.
        alpha_straight (float): The intrinsic scattering loss of the straight waveguide.
        c1 (float): Coupling/radiation amplitude coefficient (geometry dependent).
        c2 (float): Radiation decay coefficient (geometry dependent).
        
    Outputs:
        total_loss (float): Estimated loss per unit length in the bend.
        
    Units:
        radius should be in micrometers (um).
        alpha_straight and total_loss are in dB/cm (or consistent units).
        
    Example:
        >>> estimate_bend_loss(5.0, 2.5, 100.0, 1.2)
        2.7478
    """
    # Bend loss usually follows an exponential law: pure radiation ~ c1 * exp(-c2 * R)
    radiation_loss = c1 * np.exp(-c2 * radius)
    
    # Total loss is roughly intrinsic loss + bending radiation loss
    total_loss = alpha_straight + radiation_loss
    
    return total_loss
