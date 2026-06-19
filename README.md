# 🌟 PIC Design Common Library & Course Portfolio

**Autor:** [Tu Nombre / Jesús David]  
**Curso:** UNAL-BSU: PIC Design
**Profesor:** Dr. Samuel Serna  

## 📖 Descripción General
Este repositorio sirve como un portafolio integral y una librería de herramientas desarrolladas a lo largo del curso **Diseño de Circuitos Fotonicos Integrados**. 

El repositorio está dividido en dos propósitos principales:
1. **`picdesign/`**: Una librería de Python modular, reutilizable y documentada para el diseño analítico y numérico de Circuitos Integrados Fotónicos (PICs) pasivos. Incluye cálculos de dispersión, pérdidas, resonadores, interferómetros y herramientas de exportación GDS.
2. **`coursework/`**: El registro histórico de todas las tareas (Homeworks 1 al 5) y el Proyecto Final del curso, demostrando la evolución en el diseño fotónico, desde el análisis de modos hasta el *Inverse Design* y modelado de óptica no lineal (GNLSE).

## 🗂️ Estructura del Repositorio

El proyecto sigue una jerarquía estricta para separar la librería de los scripts de las tareas:

```text
pic-design-common-library/
├── README.md                  # Este archivo
├── requirements.txt           # Dependencias del proyecto (numpy, scipy, gdstk, etc.)
├── picdesign/                 # 🛠️ LIBRERÍA PRINCIPAL
│   ├── __init__.py           
│   ├── materials.py           # Modelos de dispersión de materiales (Sellmeier, etc.)
│   ├── waveguides.py          # Condiciones monomodo, confinamiento, pérdidas
│   ├── resonators.py          # FSR, radios de anillos, acoplamientos
│   ├── interferometers.py     # Desbalance de MZI, acopladores direccionales
│   ├── lca.py                 # Calculadora de Life Cycle Assessment (LCA)
│   └── gds_helpers.py         # Funciones para automatizar la exportación a .gds
├── docs/                      # Documentación adicional y guías de uso
│   └── usage.md              
├── examples/                  # Scripts rápidos para probar la librería
│   ├── mzi_example.py        
│   └── ring_example.py       
└── coursework/                # 📚 TAREAS Y PROYECTO DEL CURSO
    ├── HW1_Intro_Modes/       
    ├── HW2_Waveguides/        
    ├── HW3_Components/        
    ├── HW4_Systems/           
    ├── HW5_Sustainable_PIC/   # Lab 5 actual (LCA, Inverse Design, GNLSE)
    └── Final_Project/         # Proyecto final integrador
