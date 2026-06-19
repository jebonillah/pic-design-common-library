# PIC Design Common Library 🌐💡

**Course:** UNAL-BSU: PIC Design (Spring 2025)  
**Instructor:** Dr. Samuel Serna  
**Lab 5:** Sustainable Passive Integrated Photonics 

## 📖 Project Overview
This repository contains the `pic-design-common-library`, a custom Python package developed as part of Lab 5. The primary goal of this repository is to collect and organize reusable functions for integrated photonics design learned throughout the course.

## 🚀 Features and Required Functions
The library includes mathematical and physical modeling functions for passive integrated photonic structures, distributed across several modules. The implemented functions cover:

* **Resonators:** Effective-index-based Free Spectral Range (FSR) calculation, and ring circumference and radius.
* **Interferometers:** MZI path-length imbalance calculation.
* **Waveguides:** Bend loss estimation, approximate single-mode condition, confinement factor estimate, and propagation-loss conversion (between dB/cm and $m^{-1}$).
* **Sustainability:** Simple Life Cycle Assessment (LCA) score calculator.
* **Layout:** GDS export helper for fabrication layout.

## 📁 Repository Structure
The project rigorously follows the required directory structure:

```text
pic-design-common-library/
├── README.md
├── requirements.txt
├── examples/
│   ├── mzi_example.py
│   ├── ring_example.py
│   ├── waveguide_example.py
│   └── lca_example.py
├── picdesign/
│   ├── __init__.py
│   ├── materials.py
│   ├── waveguides.py
│   ├── resonators.py
│   ├── interferometers.py
│   ├── couplers.py
│   ├── lca.py
│   ├── dispersion.py
│   └── gds_helpers.py
└── docs/
    └── usage.md
