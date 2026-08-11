# Procedencia de los datos y limitaciones

Fecha de corte: **11 de agosto de 2026**. No se usó información posterior.

## 1. Limitación de acceso (crítica, léase primero)

Este análisis se ejecutó en un entorno cuya **política de red bloquea el acceso
directo (HTTPS) a todos los portales de lotería**. Verificado explícitamente:

```
$ curl https://lotterytexts.com/peru/kabala/past-results/
curl: (56) CONNECT tunnel failed, response 403
$ curl https://loteria.guru/...           -> 403
$ curl https://www.latinka.com.pe/        -> 403
```

`WebFetch` devuelve `EGRESS_BLOCKED` para `lotterytexts.com`,
`tinkaresultados.com`, `latinka.com.pe`, `loteria.guru`, etc.

El **único** canal disponible fue la búsqueda web, que devuelve fragmentos y un
resumen, no las tablas históricas completas. Por eso **no fue posible
reconstruir los 588 sorteos de Gana Diario ni los 252 de Kábala** del período
2025-01-01 → 2026-08-11.

Se recopiló únicamente lo verificable. **No se inventó, interpoló ni completó
ningún sorteo.** Las fechas no verificadas simplemente no están en el dataset.

## 2. Cobertura efectiva

| Juego | Verificados | Esperados en el período | Cobertura | 2025 | 2026 |
|---|---|---|---|---|---|
| Gana Diario | 18 | 588 | 3.1 % | 0 | 18 |
| Kábala | 23 | 252 | 9.1 % | 6 | 17 |

## 3. Fuentes utilizadas

- **Infobae Perú** — publica una nota por sorteo; fue la fuente más indexada y
  la principal para ambos juegos.
- **nacionalloteria.com** y **resultadosdetinka.com** — confirmación
  independiente del sorteo 4669 (10/08/2026).
- **kusiresultados.com** — confirmación del sorteo del 03/08/2026.
- **expreso.com.pe** y **elcomercio.pe** — confirmación de Kábala del 01/08/2026.
- **lotterytexts.com** — confirmación de Kábala del 28 y 30/07/2026.

## 4. Validaciones aplicadas a cada fila

Toda fila del CSV debe pasar, si no es rechazada automáticamente por `analisis.py`:

1. Cantidad correcta de números (5 en Gana Diario, 6 en Kábala).
2. Rango válido (1–35 / 1–40).
3. Sin duplicados dentro del sorteo.
4. Fecha dentro del período de análisis.
5. **Gana Diario**: `n_sorteo == 4660 + (fecha − 2026-08-01)`.
6. **Kábala**: el día de la semana debe ser martes, jueves o sábado.

### Clave de auditoría descubierta

La numeración de Gana Diario es **diaria y consecutiva sin saltos**. Anclas
independientes que lo confirman a lo largo de 9 meses:

- sorteo **4390** = 2025-11-04 (Infobae)
- sorteo **4603** = 2026-06-05 (Infobae)
- sorteo **4660** = 2026-08-01 (Infobae)
- sorteo **4669** = 2026-08-10 (nacionalloteria + resultadosdetinka)

`4390 + 270 días = 4660` ✓ y `4603 + 57 = 4660` ✓. De ahí se deduce que
**sorteo 4083 = 2025-01-01** y que el período completo abarca los sorteos
**4083 a 4670** (588 sorteos).

## 5. Datos RECHAZADOS por la validación

| Juego | Fecha | Valor devuelto por la búsqueda | Motivo del rechazo |
|---|---|---|---|
| Gana Diario | 2026-06-07 (sorteo 4605) | `20, 33, 43, 53, 30` | **43 y 53 están fuera del rango 1–35.** Extracción errónea del resumidor de búsqueda. |

Este caso es importante: demuestra que los resúmenes automáticos de búsqueda
**alucinan resultados de lotería**. Cualquier análisis que los use sin validar
rango/consistencia arrastra datos falsos.

## 6. Discrepancias entre fuentes detectadas

1. **Premio de Gana Diario**: una nota lo describe como *S/ 200 000* y otra como
   *S/ 100 000*. No se resolvió; no afecta al análisis de números.
2. **Descripción del juego**: un resumen de búsqueda describió Gana Diario como
   "acertar los seis números", lo cual es incorrecto (son 5 de 1 a 35). Error
   del resumidor, no de la fuente.
3. **Kábala vs. Chau Chamba**: varias fuentes publican ambos sorteos juntos.
   En este dataset se registró **únicamente el sorteo principal (Pozo Buenazo)**;
   las series de Chau Chamba fueron descartadas para no mezclar juegos.

## 7. Verificación del sorteo indicado en la Parte 12

**Gana Diario — sorteo 4669 — 10/08/2026: 20 – 16 – 33 – 12 – 22**

- Confirmado por `nacionalloteria.com` (consulta por fecha 2026-08-10).
- Confirmado de forma independiente por `resultadosdetinka.com`.
- Consistente con la numeración: `4660 + 9 = 4669` ✓.
- Los 5 números están en rango y sin repetir ✓.

**Resultado: CONFIRMADO** e incorporado al dataset.

## 8. Cómo completar el dataset

El pipeline no depende de estos 41 sorteos: lee `data/*.csv`. Si se agregan filas
(por ejemplo exportando el histórico oficial desde una red sin bloqueo), basta
con volver a ejecutar `python3 analisis.py` y **todas** las tablas, tests,
scores y jugadas se recalculan. La validación rechazará automáticamente
cualquier fila inconsistente.
