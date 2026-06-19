def simple_lca_score(volume_cm3, energy_kwh, water_liters, material="silicon"):
    """
    Description:
        A simplified Life Cycle Assessment (LCA) calculator for photonic chips.
        It estimates the equivalent CO2 emissions based on manufacturing inputs.
        
    Inputs:
        volume_cm3 (float): Total volume of the wafer/chip material processed.
        energy_kwh (float): Electrical energy consumed during lithography/etching.
        water_liters (float): Ultra-pure water consumed during cleaning.
        material (str): Type of material ('silicon', 'silicon_nitride', etc.).
        
    Outputs:
        co2_equivalent_kg (float): Estimated kilograms of CO2 emitted.
        
    Units:
        volume_cm3 in cubic centimeters (cm^3).
        energy_kwh in kilowatt-hours (kWh).
        water_liters in liters (L).
        Output is in kilograms (kg CO2 eq).
        
    Example:
        >>> simple_lca_score(0.5, 120.0, 50.0, "silicon")
        56.85
    """
    # Simplified emission factors (fictitious baseline for the assignment)
    # kg CO2 per unit
    factors = {
        "energy": 0.4,       # 0.4 kg CO2 / kWh (average grid)
        "water": 0.015,      # 0.015 kg CO2 / Liter of ultra-pure water
    }
    
    material_factors = {
        "silicon": 12.0,         # kg CO2 per cm3 of monocrystalline Si grown
        "silicon_nitride": 15.0, # Higher energy LPCVD deposition
        "lithium_niobate": 25.0
    }
    
    mat_factor = material_factors.get(material.lower(), 10.0)
    
    # Calculate total footprint
    co2_material = volume_cm3 * mat_factor
    co2_energy = energy_kwh * factors["energy"]
    co2_water = water_liters * factors["water"]
    
    total_footprint = co2_material + co2_energy + co2_water
    
    return total_footprint
