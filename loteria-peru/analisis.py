#!/usr/bin/env python3
"""
Analisis estadistico reproducible de Gana Diario y Kabala (Peru).

Ejecuta: python3 analisis.py
Requiere: numpy

Todo el analisis se calcula desde data/*.csv. No hay ningun numero
"hardcodeado" en las conclusiones: si se agregan sorteos al CSV, todos
los resultados (tablas, tests, scores y jugadas) se recalculan solos.

Semilla fija (SEED) => resultados identicos en cada corrida.
"""

import csv
import json
import os
from datetime import date, timedelta
from itertools import combinations
from collections import Counter, defaultdict
from math import factorial, comb

import numpy as np

SEED = 20260811
N_SIM = 200_000          # simulaciones Monte Carlo por juego (> 100k pedido)
N_CAND = 400_000         # combinaciones candidatas evaluadas por juego
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# Configuracion de cada juego
# --------------------------------------------------------------------------
GAMES = {
    "gana_diario": {
        "nombre": "GANA DIARIO",
        "csv": "data/gana_diario.csv",
        "k": 5, "maxnum": 35,
        "bandas": [("bajos 1-10", 1, 10), ("medios 11-20", 11, 20),
                   ("altos 21-30", 21, 30), ("muy altos 31-35", 31, 35)],
        # sorteo 4660 == 2026-08-01, numeracion diaria consecutiva
        # (verificado tambien con sorteo 4390 == 2025-11-04)
        "epoch_sorteo": 4660, "epoch_fecha": date(2026, 8, 1),
        "dias_sorteo": None,               # todos los dias
    },
    "kabala": {
        "nombre": "KABALA",
        "csv": "data/kabala.csv",
        "k": 6, "maxnum": 40,
        "bandas": [("bajos 1-10", 1, 10), ("medios 11-20", 11, 20),
                   ("altos 21-30", 21, 30), ("muy altos 31-40", 31, 40)],
        "epoch_sorteo": None, "epoch_fecha": None,
        "dias_sorteo": {1, 3, 5},          # martes, jueves, sabado
    },
}

FECHA_CORTE = date(2026, 8, 11)
INICIO = date(2025, 1, 1)


# --------------------------------------------------------------------------
# 1. Carga y validacion estricta
# --------------------------------------------------------------------------
def cargar(cfg):
    """Lee el CSV y valida cada fila. Devuelve (sorteos_validos, rechazos)."""
    path = os.path.join(HERE, cfg["csv"])
    draws, rechazos = [], []
    with open(path, encoding="utf-8-sig") as fh:
        rows = [ln for ln in fh if not ln.lstrip().startswith("#")]
    for row in csv.DictReader(rows):
        f = date.fromisoformat(row["fecha"])
        nums = sorted(int(row[f"n{i}"]) for i in range(1, cfg["k"] + 1))
        errs = []
        if len(set(nums)) != cfg["k"]:
            errs.append("numeros duplicados")
        if not all(1 <= n <= cfg["maxnum"] for n in nums):
            errs.append(f"fuera de rango 1-{cfg['maxnum']}")
        if not (INICIO <= f <= FECHA_CORTE):
            errs.append("fuera del periodo de analisis")
        if cfg["dias_sorteo"] and f.weekday() not in cfg["dias_sorteo"]:
            errs.append(f"dia de semana invalido ({f.weekday()})")
        if cfg["epoch_sorteo"] and row.get("sorteo"):
            esperado = cfg["epoch_sorteo"] + (f - cfg["epoch_fecha"]).days
            if int(row["sorteo"]) != esperado:
                errs.append(f"sorteo {row['sorteo']} != esperado {esperado}")
        rec = {"fecha": f, "nums": nums, "fuentes": row.get("fuentes", ""),
               "sorteo": int(row["sorteo"]) if row.get("sorteo") else None}
        (rechazos if errs else draws).append({**rec, "errores": errs})
    draws.sort(key=lambda d: d["fecha"])
    return draws, rechazos


def universo_sorteos(cfg):
    """Cuantos sorteos DEBERIAN existir entre INICIO y FECHA_CORTE."""
    dias = (FECHA_CORTE - INICIO).days + 1
    if cfg["dias_sorteo"] is None:
        return dias
    return sum(1 for i in range(dias)
               if (INICIO + timedelta(days=i)).weekday() in cfg["dias_sorteo"])


# --------------------------------------------------------------------------
# 2. Tabla maestra por numero
# --------------------------------------------------------------------------
def tabla_maestra(draws, cfg):
    M, k, N = cfg["maxnum"], cfg["k"], len(draws)
    d25 = [d for d in draws if d["fecha"].year == 2025]
    d26 = [d for d in draws if d["fecha"].year == 2026]
    c25 = Counter(n for d in d25 for n in d["nums"])
    c26 = Counter(n for d in d26 for n in d["nums"])
    tot = Counter(n for d in draws for n in d["nums"])

    filas = []
    for n in range(1, M + 1):
        # indices (desde el final) de los sorteos donde aparecio
        idx = [i for i, d in enumerate(draws) if n in d["nums"]]
        ult = draws[idx[-1]]["fecha"].isoformat() if idx else None
        desde = (N - 1 - idx[-1]) if idx else None
        # rachas de ausencia (gaps) observadas, incluyendo la actual
        gaps, prev = [], -1
        for i in idx:
            gaps.append(i - prev - 1)
            prev = i
        gaps.append(N - 1 - prev)
        filas.append({
            "numero": n,
            "ap_2025": c25[n], "ap_2026": c26[n], "ap_total": tot[n],
            "pct_2025": round(100 * c25[n] / (len(d25) * k), 2) if d25 else None,
            "pct_2026": round(100 * c26[n] / (len(d26) * k), 2) if d26 else None,
            "ultima_aparicion": ult,
            "sorteos_desde": desde,
            "max_retraso": max(gaps) if gaps else None,
            "frec_ult_30": sum(1 for d in draws[-30:] if n in d["nums"]),
            "frec_ult_60": sum(1 for d in draws[-60:] if n in d["nums"]),
            "frec_ult_100": sum(1 for d in draws[-100:] if n in d["nums"]),
        })
    for f in filas:
        f["diferencia_pp"] = (round(f["pct_2026"] - f["pct_2025"], 2)
                              if f["pct_2025"] is not None and f["pct_2026"] is not None
                              else None)
    return filas


# --------------------------------------------------------------------------
# 3. Tests de aleatoriedad
# --------------------------------------------------------------------------
def chi2_uniformidad(draws, cfg, rng):
    """Chi-cuadrado de bondad de ajuste + p-valor por Monte Carlo."""
    M, k, N = cfg["maxnum"], cfg["k"], len(draws)
    obs = np.zeros(M)
    for d in draws:
        for n in d["nums"]:
            obs[n - 1] += 1
    esp = N * k / M
    chi2 = float(((obs - esp) ** 2 / esp).sum()) if esp > 0 else 0.0

    sims = simular(N, cfg, rng, N_SIM // 20)   # muestra para el null de chi2
    null = []
    for s in sims:
        c = np.bincount(s.ravel() - 1, minlength=M).astype(float)
        null.append(((c - esp) ** 2 / esp).sum())
    null = np.array(null)
    p = float((null >= chi2).mean())
    return {"chi2": round(chi2, 2), "gl": M - 1, "p_montecarlo": round(p, 4),
            "obs_max": int(obs.max()), "obs_min": int(obs.min()),
            "esperado_por_numero": round(esp, 2),
            "chi2_null_media": round(float(null.mean()), 2),
            "chi2_null_p95": round(float(np.percentile(null, 95)), 2)}


def simular(n_draws, cfg, rng, n_sim):
    """n_sim simulaciones de n_draws sorteos justos. -> array (n_sim,n_draws,k)"""
    M, k = cfg["maxnum"], cfg["k"]
    out = np.empty((n_sim, n_draws, k), dtype=np.int16)
    for i in range(n_sim):
        # muestreo sin reemplazo por sorteo
        out[i] = np.argsort(rng.random((n_draws, M)), axis=1)[:, :k] + 1
    return out


def poder_estadistico(cfg, rng, n_list):
    """Cuanta desviacion haria falta para detectar sesgo, segun el N de sorteos."""
    M, k = cfg["maxnum"], cfg["k"]
    res = []
    for N in n_list:
        esp = N * k / M
        sims = simular(N, cfg, rng, 4000)
        maxc, chis = [], []
        for s in sims:
            c = np.bincount(s.ravel() - 1, minlength=M).astype(float)
            maxc.append(c.max())
            chis.append(((c - esp) ** 2 / esp).sum())
        maxc = np.array(maxc)
        res.append({
            "n_sorteos": N,
            "esperado_por_numero": round(esp, 1),
            "max_esperado_por_azar_p50": round(float(np.percentile(maxc, 50)), 1),
            "max_esperado_por_azar_p95": round(float(np.percentile(maxc, 95)), 1),
            "exceso_p95_sobre_esperado": round(float(np.percentile(maxc, 95) - esp), 1),
            "chi2_umbral_p95": round(float(np.percentile(chis, 95)), 1),
        })
    return res


# --------------------------------------------------------------------------
# 4. Pares y trios
# --------------------------------------------------------------------------
def coapariciones(draws, cfg, r=2):
    M, k, N = cfg["maxnum"], cfg["k"], len(draws)
    c = Counter()
    for d in draws:
        for combo in combinations(d["nums"], r):
            c[combo] += 1
    n_pos = len(list(combinations(range(M), r)))
    por_sorteo = len(list(combinations(range(k), r)))
    esp = N * por_sorteo / n_pos if n_pos else 0
    filas = []
    for combo, obs in c.items():
        # cola de Poisson: P(X >= obs) con media esp
        p = 1.0 - sum(np.exp(-esp) * esp ** i / factorial(i)
                      for i in range(obs))
        filas.append({"combo": combo, "obs": obs, "esperado": round(esp, 3),
                      "p_poisson": p})
    filas.sort(key=lambda x: (-x["obs"], x["combo"]))
    # correccion por multiples comparaciones (Benjamini-Hochberg sobre TODAS
    # las combinaciones posibles, no solo las observadas)
    if filas:
        ps = sorted(f["p_poisson"] for f in filas)
        m = n_pos
        signif = sum(1 for i, p in enumerate(ps, 1) if p <= 0.05 * i / m)
    else:
        signif = 0
    return {"top": filas[:15], "n_posibles": n_pos, "esperado": round(esp, 3),
            "max_obs": filas[0]["obs"] if filas else 0,
            "n_significativos_BH": signif,
            "n_observados_distintos": len(filas)}


# --------------------------------------------------------------------------
# 5. Estructura de los sorteos
# --------------------------------------------------------------------------
def estructura(nums, cfg):
    M = cfg["maxnum"]
    nums = sorted(nums)
    a = np.array(nums)
    consec = sum(1 for i in range(len(nums) - 1) if nums[i + 1] - nums[i] == 1)
    bandas = [sum(1 for n in nums if lo <= n <= hi) for _, lo, hi in cfg["bandas"]]
    return {
        "suma": int(a.sum()),
        "pares": int((a % 2 == 0).sum()),
        "impares": int((a % 2 == 1).sum()),
        "amplitud": int(a.max() - a.min()),
        "consecutivos": consec,
        "bandas": bandas,
        "n_bandas_ocupadas": sum(1 for b in bandas if b > 0),
        "terminaciones_distintas": len({n % 10 for n in nums}),
        "n_mayores_31": int((a >= 32).sum()),
        "media": float(a.mean()),
    }


def perfil_estructural(draws, cfg, rng):
    """Compara la estructura observada contra el null simulado."""
    obs = [estructura(d["nums"], cfg) for d in draws]
    sims = simular(1, cfg, rng, 1)  # placeholder, se usa el bloque de abajo
    M, k = cfg["maxnum"], cfg["k"]
    big = np.argsort(rng.random((N_SIM, M)), axis=1)[:, :k] + 1
    big.sort(axis=1)
    null = {
        "suma": big.sum(axis=1),
        "pares": (big % 2 == 0).sum(axis=1),
        "amplitud": big[:, -1] - big[:, 0],
        "consecutivos": (np.diff(big, axis=1) == 1).sum(axis=1),
        "n_mayores_31": (big >= 32).sum(axis=1),
    }
    resumen = {}
    for key in ["suma", "pares", "amplitud", "consecutivos", "n_mayores_31"]:
        o = np.array([x[key] for x in obs], dtype=float)
        nl = null[key].astype(float)
        # z del promedio observado respecto al null del promedio
        se = nl.std(ddof=0) / np.sqrt(len(o)) if len(o) else np.nan
        resumen[key] = {
            "observado_medio": round(float(o.mean()), 2),
            "esperado_medio": round(float(nl.mean()), 2),
            "z_del_promedio": round(float((o.mean() - nl.mean()) / se), 2) if se else None,
            "null_p05": round(float(np.percentile(nl, 5)), 1),
            "null_p95": round(float(np.percentile(nl, 95)), 1),
        }
    # distribuciones categoricas observadas
    dist = {
        "reparto_par_impar": Counter(f"{x['pares']}P-{x['impares']}I" for x in obs),
        "n_bandas_ocupadas": Counter(x["n_bandas_ocupadas"] for x in obs),
        "consecutivos": Counter(x["consecutivos"] for x in obs),
    }
    return resumen, dist, obs, null


def repeticiones(draws, ventanas=(1, 2, 3, 5, 10)):
    """Cuantos numeros se repiten respecto de los W sorteos anteriores."""
    out = {}
    for w in ventanas:
        vals = []
        for i in range(w, len(draws)):
            prev = set().union(*[set(draws[i - j]["nums"]) for j in range(1, w + 1)])
            vals.append(len(set(draws[i]["nums"]) & prev))
        out[w] = {"n": len(vals),
                  "media": round(float(np.mean(vals)), 3) if vals else None}
    return out


def repeticiones_null(cfg, rng, ventanas=(1, 2, 3, 5, 10), n=40000):
    M, k = cfg["maxnum"], cfg["k"]
    seq = np.argsort(rng.random((n, M)), axis=1)[:, :k] + 1
    out = {}
    for w in ventanas:
        vals = []
        for i in range(w, min(n, 6000)):
            prev = set(seq[i - j][m] for j in range(1, w + 1) for m in range(k))
            vals.append(len(set(seq[i]) & prev))
        out[w] = round(float(np.mean(vals)), 3)
    return out


# --------------------------------------------------------------------------
# 6. Modelo de scoring
# --------------------------------------------------------------------------
def shrinkage_lambda(chi2, gl):
    """Empirical-Bayes: cuanto creerle a las frecuencias observadas.
    Si chi2 <= gl no hay evidencia de sesgo -> lambda = 0 -> frecuencias
    colapsan a la uniforme."""
    if chi2 <= gl:
        return 0.0
    return float(max(0.0, (chi2 - gl) / chi2))


def score_numeros(draws, cfg, lam):
    """Score 0-100 por numero. Cuatro componentes explicitos y auditables:

      F (20%) frecuencia historica REGULARIZADA por shrinkage empirico-bayesiano.
              Si el chi2 no supera sus grados de libertad -> lam=0 -> F=0.5
              para todos: las frecuencias observadas no aportan informacion.
      R (15%) recencia (mitad mas nueva de la muestra), tambien regularizada.
      V (55%) impopularidad / valor esperado. UNICA componente con justificacion
              economica real: en premios repartidos entre acertantes, elegir
              numeros poco jugados no cambia P(ganar) pero si el premio esperado
              condicionado a ganar.
      D (10%) desempate DESCRIPTIVO por frecuencia bruta observada. Sin validez
              predictiva; solo evita empates en el ranking.
    """
    M, k, N = cfg["maxnum"], cfg["k"], len(draws)
    tabla = {f["numero"]: f for f in tabla_maestra(draws, cfg)}
    u = k / M                                     # tasa uniforme por sorteo
    mitad = draws[len(draws) // 2:]

    crudo = {}
    for n in range(1, M + 1):
        f = tabla[n]
        r = f["ap_total"] / N if N else u
        rec = sum(1 for d in mitad if n in d["nums"]) / (len(mitad) or 1)
        # componente EV: numeros no representables como fecha son menos jugados
        ev = 1.0 if n >= 32 else (0.55 if n > 12 else 0.0)
        if n == 7:
            ev = 0.0                              # el numero mas jugado del mundo
        crudo[n] = {"r": r, "rec": rec, "ev": ev, "fila": f}

    def norm(vals):
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-12:
            return {kk: 0.5 for kk in vals}
        return None

    r_sh = {n: u + lam * (c["r"] - u) for n, c in crudo.items()}
    rec_sh = {n: u + lam * (c["rec"] - u) for n, c in crudo.items()}

    def escalar(d):
        lo, hi = min(d.values()), max(d.values())
        if hi - lo < 1e-12:
            return {n: 0.5 for n in d}
        return {n: (v - lo) / (hi - lo) for n, v in d.items()}

    F = escalar(r_sh)
    R = escalar(rec_sh)
    # D: rango percentil de la frecuencia bruta (descriptivo)
    orden = sorted(crudo, key=lambda n: crudo[n]["r"])
    D = {n: i / (M - 1) for i, n in enumerate(orden)}

    out = {}
    for n in range(1, M + 1):
        f = crudo[n]["fila"]
        score = 100.0 * (0.20 * F[n] + 0.15 * R[n] +
                         0.55 * crudo[n]["ev"] + 0.10 * D[n])
        out[n] = {
            "numero": n,
            "score": round(score, 1),
            "F_frecuencia": round(F[n], 3),
            "R_recencia": round(R[n], 3),
            "V_impopularidad": round(crudo[n]["ev"], 3),
            "D_desempate_descriptivo": round(D[n], 3),
            "ap_total": f["ap_total"],
            "frec_vs_esperado": (round(crudo[n]["r"] / u, 2) if u else None),
            "sorteos_desde": f["sorteos_desde"],
            "max_retraso": f["max_retraso"],
        }
    return out


def clasificar_hot_cold(draws, cfg):
    """HOT / COLD / OVERDUE + test exacto por numero.

    Marginalmente, el numero de sorteos en que aparece un numero dado sigue
    una Binomial(N, k/M): en cada sorteo aparece (1) o no (0) con prob k/M.
    Eso permite un p-valor EXACTO por numero, y luego correccion BH.
    """
    M, k, N = cfg["maxnum"], cfg["k"], len(draws)
    p = k / M
    tabla = tabla_maestra(draws, cfg)

    def binom_pmf(x, n, pp):
        return comb(n, x) * pp ** x * (1 - pp) ** (n - x)

    filas = []
    for f in tabla:
        x = f["ap_total"]
        pmf_obs = binom_pmf(x, N, p)
        # p-valor exacto de dos colas (metodo de la densidad minima)
        pv = sum(binom_pmf(i, N, p) for i in range(N + 1)
                 if binom_pmf(i, N, p) <= pmf_obs * (1 + 1e-9))
        filas.append({**f, "esperado": round(N * p, 2),
                      "p_exacto": min(1.0, pv)})
    # Benjamini-Hochberg
    orden = sorted(filas, key=lambda r: r["p_exacto"])
    signif = []
    for i, r in enumerate(orden, 1):
        r["bh_umbral"] = round(0.05 * i / M, 4)
        r["significativo"] = r["p_exacto"] <= 0.05 * i / M
        if r["significativo"]:
            signif.append(r["numero"])
    por_frec = sorted(filas, key=lambda r: (-r["ap_total"], r["numero"]))
    por_gap = sorted(filas, key=lambda r: (-(r["sorteos_desde"] if r["sorteos_desde"]
                                             is not None else 10 ** 6), r["numero"]))
    return {
        "hot": por_frec[:8],
        "cold": por_frec[-8:],
        "overdue": por_gap[:8],
        "n_significativos_BH": len(signif),
        "numeros_significativos": signif,
        "p_minimo_observado": round(min(r["p_exacto"] for r in filas), 4),
        "esperado_por_numero": round(N * p, 2),
    }


# --------------------------------------------------------------------------
# 6b. Comparacion 2025 vs 2026
# --------------------------------------------------------------------------
def comparar_anios(draws, cfg, rng):
    """Correlacion entre frecuencias 2025 y 2026, con su banda nula."""
    M, k = cfg["maxnum"], cfg["k"]
    d25 = [d for d in draws if d["fecha"].year == 2025]
    d26 = [d for d in draws if d["fecha"].year == 2026]
    res = {"n_2025": len(d25), "n_2026": len(d26)}
    if len(d25) < 2 or len(d26) < 2:
        res["computable"] = False
        res["motivo"] = ("No hay sorteos verificados suficientes en uno de los "
                         "dos anios; la comparacion interanual no es computable.")
        return res
    c25 = np.array([sum(1 for d in d25 if n in d["nums"]) for n in range(1, M + 1)],
                   dtype=float)
    c26 = np.array([sum(1 for d in d26 if n in d["nums"]) for n in range(1, M + 1)],
                   dtype=float)
    r = float(np.corrcoef(c25, c26)[0, 1])
    # banda nula: correlacion entre dos anios SIMULADOS independientes
    nulos = []
    for _ in range(3000):
        a = np.argsort(rng.random((len(d25), M)), axis=1)[:, :k] + 1
        b = np.argsort(rng.random((len(d26), M)), axis=1)[:, :k] + 1
        ca = np.bincount(a.ravel() - 1, minlength=M).astype(float)
        cb = np.bincount(b.ravel() - 1, minlength=M).astype(float)
        if ca.std() > 0 and cb.std() > 0:
            nulos.append(np.corrcoef(ca, cb)[0, 1])
    nulos = np.array(nulos)
    res.update({
        "computable": True,
        "correlacion_pearson": round(r, 3),
        "null_media": round(float(nulos.mean()), 3),
        "null_p025": round(float(np.percentile(nulos, 2.5)), 3),
        "null_p975": round(float(np.percentile(nulos, 97.5)), 3),
        "p_dos_colas": round(float((np.abs(nulos) >= abs(r)).mean()), 4),
        "interpretacion": ("La correlacion observada cae dentro de la banda "
                           "esperada por puro azar" if abs(r) <= np.percentile(np.abs(nulos), 95)
                           else "La correlacion observada excede la banda del 95% del azar"),
    })
    return res


def construir_scorer(draws, cfg, rng, lam):
    """Devuelve una funcion que puntua matrices de combinaciones (n,k)."""
    M, k = cfg["maxnum"], cfg["k"]
    # --- null estructural para la componente de tipicidad
    big = np.argsort(rng.random((N_SIM, M)), axis=1)[:, :k] + 1
    big.sort(axis=1)
    null_stats = {
        "suma": np.sort(big.sum(axis=1)),
        "pares": np.sort((big % 2 == 0).sum(axis=1)),
        "amplitud": np.sort(big[:, -1] - big[:, 0]),
        "consecutivos": np.sort((np.diff(big, axis=1) == 1).sum(axis=1)),
    }

    def centralidad(vals, key):
        """1 = en el centro exacto de la distribucion nula, 0 = cola extrema."""
        ref = null_stats[key]
        F = np.searchsorted(ref, vals, side="left") / len(ref)
        return 1.0 - np.abs(2 * F - 1)

    # --- frecuencias regularizadas por numero
    N = len(draws)
    cnt = np.zeros(M + 1)
    for d in draws:
        for n in d["nums"]:
            cnt[n] += 1
    u = k / M
    r = cnt[1:] / (N or 1)
    r_shrunk = u + lam * (r - u)
    e_norm = ((r_shrunk - r_shrunk.min()) /
              (r_shrunk.max() - r_shrunk.min() + 1e-12)) if lam > 0 else np.full(M, 0.5)

    bandas = cfg["bandas"]

    def scorer(C):
        """C: array (n,k) ordenado. Devuelve dict de componentes + score."""
        Cs = np.sort(C, axis=1)
        suma = Cs.sum(axis=1)
        pares = (Cs % 2 == 0).sum(axis=1)
        ampl = Cs[:, -1] - Cs[:, 0]
        cons = (np.diff(Cs, axis=1) == 1).sum(axis=1)
        ocup = np.zeros(len(Cs), dtype=np.int8)
        for _, lo, hi in bandas:
            ocup += (((Cs >= lo) & (Cs <= hi)).sum(axis=1) > 0).astype(np.int8)
        T = (centralidad(suma, "suma") + centralidad(pares, "pares") +
             centralidad(ampl, "amplitud") + centralidad(cons, "consecutivos")) / 4.0

        E = e_norm[Cs - 1].mean(axis=1)

        # --- componente EV / impopularidad
        n_alto = (Cs >= 32).sum(axis=1)
        u1 = np.minimum(1.0, n_alto / 2.0)                    # no-fecha
        u2 = np.minimum(1.0, cons / 1.0)                      # jugadores evitan consecutivos
        n_bajo = (Cs <= 12).sum(axis=1)
        u3 = 1.0 - np.minimum(1.0, n_bajo / 3.0)              # evitar exceso de "meses"
        u4 = 1.0 - (Cs == 7).any(axis=1).astype(float)        # el 7 es el mas jugado
        n_fecha = (Cs <= 31).sum(axis=1)
        u5 = 1.0 - (n_fecha == k).astype(float)               # combo 100% cumpleanos
        U = 0.34 * u1 + 0.18 * u2 + 0.20 * u3 + 0.10 * u4 + 0.18 * u5

        score = 100.0 * (0.35 * T + 0.20 * E + 0.45 * U)
        return {"score": score, "T": T, "E": E, "U": U, "suma": suma,
                "pares": pares, "amplitud": ampl, "consecutivos": cons,
                "n_alto": n_alto, "bandas_ocupadas": ocup}

    return scorer, null_stats


def elegir_jugadas(cfg, scorer, rng, null_ref):
    """Evalua N_CAND combinaciones y elige 3 con criterios distintos."""
    M, k = cfg["maxnum"], cfg["k"]
    C = np.argsort(rng.random((N_CAND, M)), axis=1)[:, :k] + 1
    C.sort(axis=1)
    C = np.unique(C, axis=0)
    s = scorer(C)

    def pick(order_key, mask=None):
        vals = s[order_key].copy()
        if mask is not None:
            vals = np.where(mask, vals, -np.inf)
        i = int(np.argmax(vals))
        return i

    i1 = pick("score")
    # Jugada 2 "balanceada": maxima tipicidad estructural EXIGIENDO que ocupe
    # todas las bandas de rango posibles (diversidad de rangos, Parte 9).
    max_bandas = int(s["bandas_ocupadas"].max())
    umbral = np.percentile(s["score"], 60)
    i2 = pick("T", mask=(s["score"] >= umbral) &
              (s["bandas_ocupadas"] >= max_bandas) &
              (np.arange(len(C)) != i1))
    # Jugada 3 "contrarian": maxima impopularidad (EV), distinta de las otras
    i3 = pick("U", mask=(np.arange(len(C)) != i1) & (np.arange(len(C)) != i2))

    # rarezas estructurales bajo el null, para reportar honestamente
    n_null = len(null_ref["consecutivos"])

    res = []
    for etiqueta, i in [("maxima puntuacion", i1), ("balanceada", i2),
                        ("contrarian", i3)]:
        cons_i = int(s["consecutivos"][i])
        p_cons = float((null_ref["consecutivos"] >= cons_i).mean())
        suma_i = int(s["suma"][i])
        pct_suma = float((null_ref["suma"] <= suma_i).mean() * 100)
        res.append({
            "etiqueta": etiqueta,
            "numeros": [int(x) for x in C[i]],
            "score": round(float(s["score"][i]), 1),
            "T_tipicidad": round(float(s["T"][i]), 3),
            "E_frecuencia": round(float(s["E"][i]), 3),
            "U_impopularidad": round(float(s["U"][i]), 3),
            "suma": suma_i,
            "percentil_suma_null": round(pct_suma, 1),
            "pares_impares": f"{int(s['pares'][i])}P-{k - int(s['pares'][i])}I",
            "amplitud": int(s["amplitud"][i]),
            "consecutivos": cons_i,
            "p_null_consecutivos_o_mas": round(p_cons, 4),
            "bandas_ocupadas": int(s["bandas_ocupadas"][i]),
            "n_mayores_31": int(s["n_alto"][i]),
            "percentil_score": round(float((s["score"] <= s["score"][i]).mean() * 100), 2),
        })
    return res, s


# --------------------------------------------------------------------------
# Ejecucion por juego
# --------------------------------------------------------------------------
def analizar(key):
    cfg = GAMES[key]
    rng = np.random.default_rng(SEED)
    draws, rechazos = cargar(cfg)
    N = len(draws)
    esperados = universo_sorteos(cfg)

    rep = {"juego": cfg["nombre"], "k": cfg["k"], "maxnum": cfg["maxnum"]}
    rep["cobertura"] = {
        "sorteos_verificados": N,
        "sorteos_en_el_periodo": esperados,
        "cobertura_pct": round(100 * N / esperados, 1),
        "faltantes": esperados - N,
        "verificados_2025": sum(1 for d in draws if d["fecha"].year == 2025),
        "verificados_2026": sum(1 for d in draws if d["fecha"].year == 2026),
        "rango": f"{draws[0]['fecha']} .. {draws[-1]['fecha']}" if draws else None,
        "filas_rechazadas": [
            {"fecha": r["fecha"].isoformat(), "nums": r["nums"],
             "errores": r["errores"]} for r in rechazos],
    }

    rep["tabla_maestra"] = tabla_maestra(draws, cfg)
    rep["chi2"] = chi2_uniformidad(draws, cfg, rng)
    lam = shrinkage_lambda(rep["chi2"]["chi2"], rep["chi2"]["gl"])
    rep["shrinkage_lambda"] = round(lam, 4)

    rep["pares"] = coapariciones(draws, cfg, 2)
    rep["trios"] = coapariciones(draws, cfg, 3)

    est, dist, obs_struct, _ = perfil_estructural(draws, cfg, rng)
    rep["estructura"] = est
    rep["estructura_dist"] = {
        "par_impar": dict(dist["reparto_par_impar"].most_common()),
        "bandas_ocupadas": dict(sorted(dist["n_bandas_ocupadas"].items())),
        "consecutivos": dict(sorted(dist["consecutivos"].items())),
    }
    rep["repeticiones_obs"] = repeticiones(draws)
    rep["repeticiones_null"] = repeticiones_null(cfg, rng)

    rep["poder"] = poder_estadistico(cfg, rng, [N, 100, 223, esperados])
    rep["comparacion_anios"] = comparar_anios(draws, cfg, rng)
    rep["hot_cold"] = clasificar_hot_cold(draws, cfg)

    rep["score_numeros"] = score_numeros(draws, cfg, lam)
    scorer, null_ref = construir_scorer(draws, cfg, rng, lam)
    jugadas, s_all = elegir_jugadas(cfg, scorer, rng, null_ref)
    rep["jugadas"] = jugadas
    rep["score_distribucion"] = {
        "media": round(float(s_all["score"].mean()), 2),
        "p50": round(float(np.percentile(s_all["score"], 50)), 2),
        "p99": round(float(np.percentile(s_all["score"], 99)), 2),
        "max": round(float(s_all["score"].max()), 2),
    }
    # top 10 numeros por score
    top = sorted(rep["score_numeros"].values(), key=lambda d: -d["score"])[:10]
    rep["top10"] = top

    # probabilidades base

    rep["prob_base"] = {
        "combinaciones_posibles": comb(cfg["maxnum"], cfg["k"]),
        "prob_por_jugada": 1 / comb(cfg["maxnum"], cfg["k"]),
    }
    return rep, draws


def main():
    todo = {}
    for key in GAMES:
        rep, draws = analizar(key)
        todo[key] = rep
        print(f"\n{'=' * 70}\n{rep['juego']}\n{'=' * 70}")
        c = rep["cobertura"]
        print(f"Cobertura: {c['sorteos_verificados']}/{c['sorteos_en_el_periodo']} "
              f"sorteos ({c['cobertura_pct']}%) | 2025={c['verificados_2025']} "
              f"2026={c['verificados_2026']}")
        print(f"Rechazados por validacion: {len(c['filas_rechazadas'])}")
        for r in c["filas_rechazadas"]:
            print(f"   RECHAZADO {r['fecha']} {r['nums']} -> {r['errores']}")
        x = rep["chi2"]
        print(f"Chi2 uniformidad = {x['chi2']} (gl={x['gl']}), "
              f"p={x['p_montecarlo']}, umbral p95 del null={x['chi2_null_p95']}")
        print(f"Lambda de shrinkage = {rep['shrinkage_lambda']}")
        print(f"Pares: max observado={rep['pares']['max_obs']}, "
              f"esperado={rep['pares']['esperado']}, "
              f"significativos tras BH={rep['pares']['n_significativos_BH']}")
        print(f"Trios: max observado={rep['trios']['max_obs']}, "
              f"esperado={rep['trios']['esperado']}, "
              f"significativos tras BH={rep['trios']['n_significativos_BH']}")
        print("Estructura (obs vs null):")
        for k2, v in rep["estructura"].items():
            print(f"   {k2:16s} obs={v['observado_medio']:>7} "
                  f"null={v['esperado_medio']:>7}  z={v['z_del_promedio']}")
        print("Poder estadistico (max de conteo esperado solo por azar):")
        for p in rep["poder"]:
            print(f"   N={p['n_sorteos']:>4}: esperado/numero={p['esperado_por_numero']:>6}"
                  f"  max por azar p95={p['max_esperado_por_azar_p95']:>6}"
                  f"  (+{p['exceso_p95_sobre_esperado']})")
        ca = rep["comparacion_anios"]
        if ca.get("computable"):
            print(f"2025 vs 2026: r={ca['correlacion_pearson']} "
                  f"(banda nula 95%: {ca['null_p025']}..{ca['null_p975']}, "
                  f"p={ca['p_dos_colas']}) -> {ca['interpretacion']}")
        else:
            print(f"2025 vs 2026: NO COMPUTABLE ({ca['motivo']})")
        print("TOP 10 numeros:")
        print("   " + ", ".join(f"{t['numero']}({t['score']})" for t in rep["top10"]))
        print("JUGADAS:")
        for j in rep["jugadas"]:
            print(f"   [{j['etiqueta']:>18}] {' - '.join(f'{n:02d}' for n in j['numeros'])}"
                  f"  score={j['score']}/100 (pct {j['percentil_score']})"
                  f"  suma={j['suma']} {j['pares_impares']} ampl={j['amplitud']}"
                  f" cons={j['consecutivos']} >31={j['n_mayores_31']}")

    with open(os.path.join(OUT, "resultados.json"), "w", encoding="utf-8") as fh:
        json.dump(todo, fh, ensure_ascii=False, indent=2, default=str)

    # CSV de tablas maestras
    for key, rep in todo.items():
        with open(os.path.join(OUT, f"tabla_maestra_{key}.csv"), "w",
                  newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rep["tabla_maestra"][0].keys()))
            w.writeheader()
            w.writerows(rep["tabla_maestra"])
    print(f"\nArtefactos escritos en {OUT}/")


if __name__ == "__main__":
    main()
