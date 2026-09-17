"""Constantes geológicas y analíticas del pipeline.

Los seis dominios y los 13 minerales SWIR replican las asociaciones
reportadas en la tesis (Mallma, 2026, Tablas 15 y 17), anonimizadas
respecto de la unidad de origen.
"""

from __future__ import annotations

DOMAINS: tuple[str, ...] = ("Arg", "ArgAvd", "Fil", "Oxd", "Pro", "Sk")

DOMAIN_LABELS: dict[str, str] = {
    "Arg": "Argílica",
    "ArgAvd": "Argílica avanzada",
    "Fil": "Fílica",
    "Oxd": "Óxidos",
    "Pro": "Propilítica",
    "Sk": "Skarn",
}

DOMAIN_COLORS: dict[str, str] = {
    "Arg": "#c7e9b4",
    "ArgAvd": "#7fcdbb",
    "Fil": "#41b6c4",
    "Oxd": "#e6550d",
    "Pro": "#2c7fb8",
    "Sk": "#7a0177",
}

# Proporciones relativas de la Tabla 17 (n = 86 538), reescaladas.
DOMAIN_PROPORTIONS: dict[str, float] = {
    "Arg": 978 / 86538,
    "ArgAvd": 23308 / 86538,
    "Fil": 28669 / 86538,
    "Oxd": 3297 / 86538,
    "Pro": 5050 / 86538,
    "Sk": 25266 / 86538,
}

# 13 minerales SWIR retenidos tras filtrar medias nulas (Tabla 15).
SPECTRAL_MINERALS: tuple[str, ...] = (
    "WhiteMica",
    "Chlorite",
    "Carbonate",
    "Epidote",
    "Kaolinite",
    "Dickite",
    "Montmor",
    "Alunite",
    "Gypsum",
    "Pyrophyllite",
    "Diaspore",
    "Zunyite",
    "Water_silica",
)

VNIR_MINERALS: tuple[str, ...] = ("Hematite", "Goethite")

# Rasgos diagnósticos SWIR (Tabla 7; Pontual, 2013).
DIAGNOSTIC_WAVELENGTHS_NM: dict[str, tuple[int, ...]] = {
    "Alunite": (1480, 2160, 2320),
    "Pyrophyllite": (1390, 2070, 2166, 2320),
    "Kaolinite": (1400, 2162, 2208),
    "Illite": (1400, 1900, 2200),
    "Chlorite": (2250, 2350),
    "Epidote": (2160, 2335),
}

ABSORPTION_GROUPS_NM: dict[str, tuple[int, int] | tuple[int, ...]] = {
    "OH": (1400,),
    "H2O": (1400, 1900),
    "AlOH": (2160, 2220),
    "FeOH": (2230, 2295),
    "MgOH": (2300, 2360),
    "CO3": (2300, 2350),
}

# 34 elementos retenidos tras umbral de completitud 80 % (sección 3.10.1).
CHEMICAL_COLUMNS: tuple[str, ...] = (
    "Ag_ppm",
    "Al_pct",
    "As_ppm",
    "Au_ppm",
    "Ba_ppm",
    "Be_ppm",
    "Bi_ppm",
    "Ca_pct",
    "Cd_ppm",
    "Co_ppm",
    "Cr_ppm",
    "Cu_pct",
    "Fe_pct",
    "K_pct",
    "Mg_pct",
    "Mn_pct",
    "Mo_ppm",
    "Na_pct",
    "Ni_ppm",
    "P_pct",
    "Pb_ppm",
    "S_pct",
    "Sb_ppm",
    "Sc_ppm",
    "Si_pct",
    "Sr_ppm",
    "Ti_pct",
    "V_ppm",
    "W_ppm",
    "Zn_ppm",
    "Ga_ppm",
    "Rb_ppm",
    "Tl_ppm",
    "Cs_ppm",
)

ID_COLUMNS: tuple[str, ...] = (
    "sample_id",
    "holeid",
    "from_m",
    "to_m",
    "x",
    "y",
    "z",
    "depth_m",
)

TARGET_COLUMN = "MOD_ALT"
CLUSTER_COLUMN = "cluster_k5"

# Hiperparámetros publicados (Tablas 19–22). SVM usa más iteraciones
# porque el límite de 100 de Orange no suele converger en scikit-learn.
THESIS_HYPERPARAMS: dict[str, dict] = {
    "random_forest": {
        "n_estimators": 10,
        "max_features": 8,
        "max_depth": 4,
        "min_samples_split": 5,
        "class_weight": "balanced",
        "random_state": 42,
        "n_jobs": -1,
    },
    "knn": {
        "n_neighbors": 5,
        "metric": "euclidean",
        "weights": "distance",
    },
    "neural_network": {
        "hidden_layer_sizes": (100,),
        "activation": "relu",
        "solver": "adam",
        "alpha": 0.0001,
        "max_iter": 400,
        "random_state": 42,
    },
    "svm": {
        "C": 1.0,
        "kernel": "rbf",
        "gamma": "scale",
        "class_weight": "balanced",
        "max_iter": 100,
        "random_state": 42,
    },
}

ROBUST_HYPERPARAMS: dict[str, dict] = {
    "random_forest": {
        "n_estimators": 200,
        "max_features": "sqrt",
        "max_depth": None,
        "min_samples_split": 5,
        "class_weight": "balanced",
        "random_state": 42,
        "n_jobs": -1,
    },
    "knn": {
        "n_neighbors": 5,
        "metric": "euclidean",
        "weights": "distance",
    },
    "neural_network": {
        "hidden_layer_sizes": (64, 32),
        "activation": "relu",
        "solver": "adam",
        "alpha": 0.0005,
        "max_iter": 500,
        "random_state": 42,
    },
    "svm": {
        "C": 1.0,
        "kernel": "rbf",
        "gamma": "scale",
        "class_weight": "balanced",
        "max_iter": 4000,
        "random_state": 42,
    },
}

# Asociaciones mineralógicas usadas para etiquetar dominios (sección 3.12.2).
DOMAIN_ASSEMBLAGES: dict[str, str] = {
    "ArgAvd": "Pirofilita + alunita ± diásporo ± zunyita (núcleo ácido)",
    "Fil": "Mica blanca (ilita/sericita) dominante",
    "Arg": "Caolinita + mica blanca",
    "Pro": "Clorita + montmorillonita ± carbonato ± epidota",
    "Sk": "Clorita + montmorillonita + mica blanca + caolinita (halo cálcico)",
    "Oxd": "Hematita/goethita ± sílice hidratada ± yeso (supérgeno)",
}
