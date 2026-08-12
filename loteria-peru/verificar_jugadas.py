#!/usr/bin/env python3
"""Contrasta las jugadas recomendadas contra un sorteo real (fuera de muestra)."""
from math import comb

SORTEOS = {
    "GANA DIARIO": {
        "fecha": "2026-08-11 (sorteo 4670)", "k": 5, "M": 35,
        "resultado": {5, 11, 18, 20, 25},
        "top10": [32, 33, 35, 34, 16, 21, 18, 28, 27, 20],
        "jugadas": [("1 · Máxima puntuación", [8, 13, 16, 32, 33]),
                    ("2 · Balanceada",        [6, 7, 18, 28, 31]),
                    ("3 · Contrarian",        [13, 14, 15, 32, 33])],
    },
    "KÁBALA": {
        "fecha": "2026-08-11", "k": 6, "M": 40,
        "resultado": {1, 4, 14, 18, 19, 31},
        "top10": [34, 38, 37, 33, 32, 39, 35, 40, 36, 27],
        "jugadas": [("1 · Máxima puntuación", [2, 15, 19, 22, 32, 33]),
                    ("2 · Balanceada",        [1, 11, 24, 27, 28, 32]),
                    ("3 · Contrarian",        [13, 14, 15, 16, 32, 34])],
    },
}

for juego, s in SORTEOS.items():
    k, M = s["k"], s["M"]
    # distribucion hipergeometrica de aciertos
    dist = {i: comb(k, i) * comb(M - k, k - i) / comb(M, k) for i in range(k + 1)}
    print(f"\n{'='*64}\n{juego} — {s['fecha']}")
    print("Resultado:", " – ".join(f"{n:02d}" for n in sorted(s["resultado"])))
    print(f"Aciertos esperados por jugada (azar puro): {k*k/M:.3f}")
    tot = 0
    for nombre, j in s["jugadas"]:
        ac = sorted(set(j) & s["resultado"])
        tot += len(ac)
        p_igual_o_mas = sum(v for i, v in dist.items() if i >= len(ac))
        print(f"  {nombre:24s} {' '.join(f'{n:02d}' for n in j)}"
              f"  -> {len(ac)} acierto(s) {ac if ac else ''}"
              f"   P(≥{len(ac)}) = {p_igual_o_mas:.3f}")
    print(f"  Media de aciertos de mis 3 jugadas: {tot/3:.2f}  (esperado {k*k/M:.2f})")
    hits = sorted(set(s["top10"]) & s["resultado"])
    esp_top10 = 10 * k / M
    print(f"  TOP 10: {len(hits)} de los {k} números salieron -> {hits if hits else '(ninguno)'}"
          f"   (esperado por azar: {esp_top10:.2f})")
    print("  Distribución de aciertos:",
          ", ".join(f"{i}:{v:.3f}" for i, v in dist.items() if v > 0.0001))
