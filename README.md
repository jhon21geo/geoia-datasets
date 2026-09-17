# geoia-datasets

Datos de GeoIA (espectros, superficie INGEMMET y sondajes sintéticos) y visor web del módulo de **prospectividad**.

## Visor de prospectividad

En producción (`https://geoia.site/prospectividad/`) el HTML existía, pero **no se servían** `css/style.css` ni `js/map.js` (404). La página se veía como HTML crudo: botón nativo «Seleccionar archivo», bloques apilados y sin mapa.

Esta carpeta reconstruye el módulo con el mismo layout de la plataforma (barra lateral oscura, tarjetas de resumen, mapa a pantalla completa):

```
prospectividad/
  index.html
  css/style.css
  js/map.js
  data/ingemmet_superficie.geojson
```

Para verlo en local:

```bash
python3 -m http.server 8080 --directory prospectividad
```

Abre `http://localhost:8080`.

Para corregir geoia.site, copia esa carpeta completa a la ruta `/prospectividad/` del servidor (HTML + `css/` + `js/` + `data/`). Con solo el HTML no alcanza: el visor necesita los tres directorios junto al `index.html`.
