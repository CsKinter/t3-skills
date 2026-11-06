# Caso trabajado: PE Andino Suiza (NUP 3665)

Sirve de ejemplo de cómo se resuelve una contradicción de potencia entre la
ficha de Acceso Abierto, el SEIA y el informe de restricciones. Estudio: PE
Cumbres del Ñuble (Bulí 154 kV), 02-11-2026.

## El problema

Tres cifras que no calzaban:

- Acceso Abierto: 150 MW eólico + 115 MW de BESS.
- SEIA: 16 aerogeneradores, 115,2 MW, sin mención de almacenamiento en la nota
  de prensa del MMA.
- Informe de restricciones: 150 MW eólicos + 150 MW de BESS, en dos filas
  separadas, 300 MW en Bulí.

## Lo que dijo cada registro

| Registro | Fecha | Eólico | BESS | Inyección / retiro | Punto |
|---|---|---|---|---|---|
| SAC original (id 1253, desistida) | 14-09-2022 | 150 MW | — | — | Bulí 154 kV, paño A4 |
| **AA, NUP 3665** (id 1254) | IAC 15-01-2026 | **150 MW**, tecnología «Eólico», sin campos de almacenamiento | — | — | Bulí 154 kV, paño A4, barra principal |
| IAC definitivo (confidencial, leído en el portal) | 15-01-2026 | 150 MW | 115 MW / 5 h / 575 MWh | 150 / 115 | paño A3 según esa lectura |
| **RCA** (doc. 2169405718) | 21-08-2026 | **115,2 MW** (16 × 7,2) | **115 MW / 5 h**, 184 × 3,0 MWh = 552 MWh | no declara | Bulí 154 kV |
| CNE, Reporte ERNC | 09-2026 | 115 MW | «Almacenamiento: Si» | — | — |
| Estudio | — | 150 | 150 | — | 2 filas |

## Qué se concluyó

1. **Un solo proyecto, un solo NUP, una sola RCA.** El BESS está dentro de la
   DIA (la RCA describe el «Area BESS», los 184 contenedores y la conexión del
   BESS a la red colectora de 33 kV). No hay RCA ni pertinencia propia del BESS.
2. **El 150 es la potencia declarada en 2022 y nunca se actualizó.** No es un
   límite de inyección ni un error de lectura: es el registro administrativo.
3. **La RCA manda para lo construible** (115,2 MW) por ser posterior. El IAC
   manda para lo despachable (150 MW de inyección, 115 de retiro).
4. **El estudio debía modelar una CRCA**: 115,2 MW eólicos + 115 MW / 552 MWh,
   con tope de inyección 150 MW y retiro 115 MW. Modelaba 300 MW.

## Lecciones

- La nota de prensa del MMA decía «EIA» y el expediente es **DIA**. La prensa
  institucional también se equivoca; el expediente manda.
- La ficha de AA no tenía ningún campo de almacenamiento aunque el IAC y la RCA
  sí. Los campos `potencia_caa`, `energia_caa` y `horas_almacenamiento_caa`
  vacíos **no** significan que no haya BESS: significan que la SAC no lo declaró
  en ese registro.
- El paño cambió: A3 en la carta de ingeniería de 2025, A4 en la base de AA. Los
  paños se renumeran; citar el de la fuente y la fecha.
- En Bulí había cinco eólicos/solares compitiendo por posiciones en 2022 (Belén,
  San Carlos, San Nicolás, PFV Bulí, Eloise). Todos rechazados menos Andino
  Suiza. El punto de conexión tiene historia y la cola explica por qué el NUP es
  de 2022 y la RCA de 2026.
