# Análisis estadístico — Gana Diario y Kábala (Perú)

Fecha de corte: **2026-08-11**.

```bash
pip install numpy
python3 analisis.py
```

- `data/*.csv` — sorteos **verificados** (ver `DATA_PROVENANCE.md`). Ninguno inventado.
- `analisis.py` — pipeline completo: validación, tabla maestra, chi², pares/tríos con
  corrección BH, estructura vs. null, comparación interanual, Monte Carlo (200 000
  simulaciones por juego), análisis de poder y modelo de scoring.
- `output/` — `resultados.json` + tablas maestras en CSV.

Semilla fija (`SEED = 20260811`): la corrida es determinista y reproducible.

**Lea `DATA_PROVENANCE.md` antes de usar cualquier cifra**: la cobertura real es
del 3.1 % (Gana Diario) y 9.1 % (Kábala) porque el entorno bloquea el acceso a
los portales de lotería.
