# Datos sintéticos

Este directorio se llena con `python -m alteration_ml.cli generate`.

| Archivo | Contenido |
| --- | --- |
| `synthetic_merged.csv` | Tabla única: coordenadas, scores SWIR/VNIR, geoquímica y `MOD_ALT` |
| `synthetic_spectral.csv` | Abundancias minerales (0–100) al estilo Ausspec |
| `synthetic_geochemistry.csv` | 34 elementos multielementales |
| `synthetic_labels.csv` | Dominio de alteración y flag `labeled` |

Los datos **no corresponden a un yacimiento real**. Replican las asociaciones
mineralógicas y las proporciones de dominios de Mallma (2026), con ruido y
solapamiento entre zonas vecinas.

Semilla por defecto: `42`.
