# Obras futuras: PET, decretos y PGP

## Plan de Expansión de la Transmisión (PET)

- Documentos por año en la carpeta del proyecto (`00_Plan de Obras/PET/PET 20XX/`): ITD/ITF (informe técnico) y, desde
  2024, “Anexo-1 Ingenierías conceptuales”.
- Cada obra trae, en “Descripción general y ubicación”, la capacidad exigida: **“al menos X MVA de capacidad de
  transmisión por circuito a 35 °C con sol”** (líneas) y “al menos X MVA con 75 °C” (barras/conductor de S/E: no es la de
  la línea). `pet.py` asocia cada frase al título de la obra más cercano hacia atrás.
- No traen la capacidad de los equipos de paño (sólo cantidades) → líneas futuras sin detalle de paños.
- Decretos (para citar): PET 2019: 171/2020 y 185/2020; PET 2020: 185/2021 y 229/2021; PET 2021–2024 y el ITD PET 2025
  (CNE, sept. 2026) ya están en el informe de Cumbres como referencias.
- Obras antiguas (D418/2017, plan 2017) no están en la carpeta: buscar en PGP.

## PGP (pgp.coordinador.cl, sin sesión)

- Búsqueda: `GET /api/request/irs?page=1&project=<NUP o texto>&company_name=&type=all` → `items[]` con `correlativo`
  (NUP), `name`, `description`, `extra_data` (`capacity` [MVA], `tension_level`, `connection_point`), `stage`,
  `service_estimate_date`, `id` (página `https://pgp.coordinador.cl/irequests/<id>`). La búsqueda por NUP trae parciales.
- La descripción suele traer la capacidad (NUP 1087: “al menos 90 MVA por circuito, a 25 °C con sol”; NUP 1077:
  “485 MVA”). `extra_data.capacity` puede ser la del proyecto completo.
- Descarga en dos pasos (pedir OK): `GET /api/task/get_file_link/{fileId}` → `link_id`; `GET /api/task/download/{link_id}`.
  El `fileId` está en la página del proyecto (atributo `data-for="history-<fileId>"` del enlace del documento): abrirla con
  el navegador integrado.
- Lo público: minutas y DUF (ZIP de planos). La capacidad de equipos casi nunca aparece; no vale la pena bajar planos.

## Cuando no hay nada

Usar el estándar de una obra equivalente (p. ej. Dichato–Tomé 66 kV ≈ Hualqui–Chiguayante 90 MVA, misma obra D418), con la
fuente marcada “(ref.)”, y decírselo al usuario.
