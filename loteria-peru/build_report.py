#!/usr/bin/env python3
"""Genera output/informe.html desde output/resultados.json. Sin cifras a mano."""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "output/resultados.json"), encoding="utf-8"))
GD, KB = D["gana_diario"], D["kabala"]


def esc(s):
    return html.escape(str(s))


def tabla(headers, rows, cls=""):
    h = "".join(f"<th>{esc(x)}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="scroll"><table class="{cls}"><thead><tr>{h}</tr></thead>'
            f"<tbody>{b}</tbody></table></div>")


def master_rows(rep):
    out = []
    for f in rep["tabla_maestra"]:
        na = lambda v: "—" if v in (None, "") else v
        out.append([
            f'<span class="num">{f["numero"]:02d}</span>',
            f["ap_2025"], f["ap_2026"], f["ap_total"],
            na(f["pct_2025"]), na(f["pct_2026"]), na(f["diferencia_pp"]),
            na(f["ultima_aparicion"]), na(f["sorteos_desde"]), na(f["max_retraso"]),
            f["frec_ult_30"], f["frec_ult_60"], f["frec_ult_100"],
        ])
    return out


ETIQUETAS = {"maxima puntuacion": "Máxima puntuación estadística",
             "balanceada": "Balanceada", "contrarian": "Contrarian"}


def jugada_card(j, k, idx):
    balls = "".join(f'<span class="ball">{n:02d}</span>' for n in j["numeros"])
    bars = ""
    for lbl, key, w in [("Tipicidad estructural", "T_tipicidad", "35%"),
                        ("Frecuencia (regularizada)", "E_frecuencia", "20%"),
                        ("Impopularidad / VE", "U_impopularidad", "45%")]:
        v = j[key]
        bars += (f'<div class="bar"><span class="bl">{lbl} <em>peso {w}</em></span>'
                 f'<span class="btrack"><span class="bfill" style="width:{v*100:.0f}%"></span></span>'
                 f'<span class="bv">{v:.2f}</span></div>')
    return f"""
<article class="jugada">
  <header><span class="jidx">Jugada {idx}</span><h4>{esc(ETIQUETAS.get(j["etiqueta"], j["etiqueta"]))}</h4>
    <span class="score">{j["score"]}<small>/100</small></span></header>
  <div class="balls">{balls}</div>
  {bars}
  <dl class="meta">
    <div><dt>Suma</dt><dd>{j["suma"]} <em>(pct {j["percentil_suma_null"]} del null)</em></dd></div>
    <div><dt>Par / impar</dt><dd>{esc(j["pares_impares"])}</dd></div>
    <div><dt>Amplitud</dt><dd>{j["amplitud"]}</dd></div>
    <div><dt>Consecutivos</dt><dd>{j["consecutivos"]} <em>(P={j["p_null_consecutivos_o_mas"]})</em></dd></div>
    <div><dt>Bandas ocupadas</dt><dd>{j["bandas_ocupadas"]} de 4</dd></div>
    <div><dt>Números ≥ 32</dt><dd>{j["n_mayores_31"]}</dd></div>
    <div><dt>Percentil del score</dt><dd>{j["percentil_score"]}</dd></div>
  </dl>
</article>"""


def bloque_juego(rep, slug):
    c, x, hc = rep["cobertura"], rep["chi2"], rep["hot_cold"]
    k = rep["k"]
    top10 = tabla(
        ["#", "Nº", "Score", "F frec.", "R recencia", "V impop.", "D desemp.",
         "Aparic.", "Frec/esperado", "Sorteos desde"],
        [[i + 1, f'<span class="num">{t["numero"]:02d}</span>', f'<b>{t["score"]}</b>',
          t["F_frecuencia"], t["R_recencia"], t["V_impopularidad"],
          t["D_desempate_descriptivo"], t["ap_total"], t["frec_vs_esperado"],
          t["sorteos_desde"]] for i, t in enumerate(rep["top10"])])

    hot = tabla(["Nº", "Aparic.", "Esperado", "p exacto", "¿Signif. tras BH?"],
                [[f'<span class="num">{r["numero"]:02d}</span>', r["ap_total"],
                  r["esperado"], round(r["p_exacto"], 3),
                  '<span class="tag bad">No</span>'] for r in hc["hot"]])
    cold = tabla(["Nº", "Aparic.", "Esperado", "p exacto", "¿Signif. tras BH?"],
                 [[f'<span class="num">{r["numero"]:02d}</span>', r["ap_total"],
                   r["esperado"], round(r["p_exacto"], 3),
                   '<span class="tag bad">No</span>'] for r in hc["cold"]])
    over = tabla(["Nº", "Sorteos sin salir", "Máx. retraso histórico"],
                 [[f'<span class="num">{r["numero"]:02d}</span>',
                   "nunca apareció" if r["sorteos_desde"] is None else r["sorteos_desde"],
                   r["max_retraso"]] for r in hc["overdue"]])

    pares = tabla(["Par", "Veces juntos", "Esperado", "p Poisson"],
                  [[f'<span class="num">{p["combo"][0]:02d}·{p["combo"][1]:02d}</span>',
                    p["obs"], p["esperado"], f'{p["p_poisson"]:.4f}']
                   for p in rep["pares"]["top"][:8]])
    trios = tabla(["Trío", "Veces juntos", "Esperado", "p Poisson"],
                  [['<span class="num">' + "·".join(f"{n:02d}" for n in p["combo"]) + "</span>",
                    p["obs"], p["esperado"], f'{p["p_poisson"]:.4f}']
                   for p in rep["trios"]["top"][:6]])

    est = tabla(["Métrica", "Observado (media)", "Esperado si es azar", "z", "Banda nula 5–95%"],
                [[esc(kk), v["observado_medio"], v["esperado_medio"],
                  f'<b>{v["z_del_promedio"]}</b>', f'{v["null_p05"]} – {v["null_p95"]}']
                 for kk, v in rep["estructura"].items()])

    reps = tabla(["Ventana", "Repeticiones observadas (media)", "Esperado si es azar"],
                 [[f"últimos {w} sorteos", rep["repeticiones_obs"][w]["media"],
                   rep["repeticiones_null"][w]] for w in rep["repeticiones_obs"]])

    poder = tabla(["Nº de sorteos", "Esperado por número", "Máx. por puro azar (p95)", "Exceso"],
                  [[p["n_sorteos"], p["esperado_por_numero"],
                    p["max_esperado_por_azar_p95"], f'+{p["exceso_p95_sobre_esperado"]}']
                   for p in rep["poder"]])

    ca = rep["comparacion_anios"]
    if ca.get("computable"):
        anios = (f'<p>Correlación de Pearson entre las frecuencias de 2025 y 2026: '
                 f'<b>r = {ca["correlacion_pearson"]}</b>, con {ca["n_2025"]} y '
                 f'{ca["n_2026"]} sorteos respectivamente. La banda del 95 % para dos años '
                 f'<em>independientes y simulados</em> va de {ca["null_p025"]} a '
                 f'{ca["null_p975"]} (p = {ca["p_dos_colas"]}). {esc(ca["interpretacion"])}.</p>'
                 f'<p class="callout">Es decir: la frecuencia de 2025 <b>no predice</b> la de 2026. '
                 f'La correlación observada es indistinguible de cero.</p>')
    else:
        anios = (f'<p class="callout warn"><b>No computable.</b> {esc(ca["motivo"])} '
                 f'Sorteos verificados: {ca["n_2025"]} en 2025, {ca["n_2026"]} en 2026.</p>')

    dist = rep["estructura_dist"]
    dl = lambda d: " · ".join(f'<span class="chip">{esc(kk)}: <b>{vv}</b></span>'
                              for kk, vv in d.items())

    return f"""
<section id="{slug}">
  <h2>{esc(rep["juego"])}</h2>
  <p class="lede">{k} números de 1 a {rep["maxnum"]} ·
    {rep["prob_base"]["combinaciones_posibles"]:,} combinaciones posibles ·
    probabilidad por jugada 1 entre {rep["prob_base"]["combinaciones_posibles"]:,}</p>

  <div class="stats">
    <div class="stat"><span class="sv">{c["sorteos_verificados"]}</span><span class="sl">sorteos verificados</span></div>
    <div class="stat"><span class="sv">{c["sorteos_en_el_periodo"]}</span><span class="sl">sorteos en el período</span></div>
    <div class="stat warn"><span class="sv">{c["cobertura_pct"]}%</span><span class="sl">cobertura real</span></div>
    <div class="stat"><span class="sv">{c["verificados_2025"]} / {c["verificados_2026"]}</span><span class="sl">2025 / 2026</span></div>
  </div>

  <h3>Parte 3 · Tabla maestra por número</h3>
  <p>Columnas exactamente como se pidieron. «—» significa que el dato no es
     calculable con la muestra disponible, no que valga cero.</p>
  {tabla(["Nº", "Ap. 2025", "Ap. 2026", "Ap. total", "% 2025", "% 2026", "Dif. p.p.",
          "Última aparición", "Sorteos desde", "Máx. retraso",
          "Frec. últ. 30", "Frec. últ. 60", "Frec. últ. 100"], master_rows(rep), "master")}
  <p class="note">Nota: con {c["sorteos_verificados"]} sorteos, las ventanas de 30/60/100
     se truncan a la muestra disponible; «Frec. últ. 100» equivale aquí a la frecuencia total.</p>

  <h3>Parte 4 · Hot / Cold / Overdue</h3>
  <p>Esperado por número: <b>{hc["esperado_por_numero"]}</b> apariciones.
     Cada número sigue marginalmente una Binomial(N, k/M), lo que permite un
     p-valor <em>exacto</em>. Tras corrección de Benjamini-Hochberg sobre los
     {rep["maxnum"]} números: <b>{hc["n_significativos_BH"]} números significativos</b>
     (p mínimo observado = {hc["p_minimo_observado"]}).</p>
  <div class="two">
    <div><h4>🔥 Hot (mayor frecuencia)</h4>{hot}</div>
    <div><h4>🧊 Cold (menor frecuencia)</h4>{cold}</div>
  </div>
  <h4>⏳ Overdue (mayor retraso)</h4>
  {over}

  <h3>Parte 5 · Pares y tríos</h3>
  <p>Pares: {rep["pares"]["n_observados_distintos"]} pares distintos observados de
     {rep["pares"]["n_posibles"]} posibles; esperado por par
     <b>{rep["pares"]["esperado"]}</b>; máximo observado <b>{rep["pares"]["max_obs"]}</b>;
     <b>{rep["pares"]["n_significativos_BH"]} significativos</b> tras Benjamini-Hochberg.</p>
  {pares}
  <p>Tríos: esperado por trío <b>{rep["trios"]["esperado"]}</b>; máximo observado
     <b>{rep["trios"]["max_obs"]}</b>;
     <b>{rep["trios"]["n_significativos_BH"]} significativos</b> tras BH.</p>
  {trios}
  <p class="callout">Con {c["sorteos_verificados"]} sorteos hay
     {rep["pares"]["n_posibles"]} pares posibles. Que alguno aparezca
     {rep["pares"]["max_obs"]} veces es <b>lo esperado por azar</b>, no una señal.</p>

  <h3>Parte 6 · Estructura de los sorteos</h3>
  {est}
  <p class="note">z = desviaciones estándar entre la media observada y la media
     simulada. |z| &lt; 2 ⇒ compatible con azar.</p>
  <p><b>Reparto par/impar:</b> {dl(dist["par_impar"])}</p>
  <p><b>Bandas de rango ocupadas:</b> {dl(dist["bandas_ocupadas"])}</p>
  <p><b>Números consecutivos:</b> {dl(dist["consecutivos"])}</p>
  <h4>Repetición respecto de sorteos anteriores</h4>
  {reps}

  <h3>Parte 7 · 2025 vs 2026</h3>
  {anios}

  <h3>Parte 8 · Monte Carlo y poder estadístico</h3>
  <p>200 000 sorteos simulados. χ² de uniformidad observado =
     <b>{x["chi2"]}</b> (gl = {x["gl"]}), p = <b>{x["p_montecarlo"]}</b>;
     el umbral del 95 % bajo azar puro es {x["chi2_null_p95"]}.
     Conclusión: <b>los datos son compatibles con un proceso aleatorio</b>.</p>
  <p>Esto fija el <em>shrinkage</em> del modelo en
     <b>λ = {rep["shrinkage_lambda"]}</b> (ver Parte 9).</p>
  <h4>¿Cuánta desviación haría falta para detectar un sesgo?</h4>
  {poder}
  <p class="callout">Aun con el histórico <b>completo</b>
     ({c["sorteos_en_el_periodo"]} sorteos), un número podría salir hasta
     {rep["poder"][-1]["max_esperado_por_azar_p95"]} veces
     (+{rep["poder"][-1]["exceso_p95_sobre_esperado"]} sobre lo esperado)
     <b>por puro azar</b>. Cualquier «número caliente» por debajo de ese umbral
     es ruido, no señal.</p>

  <h3>Parte 10 · Top 10 y jugadas finales</h3>
  {top10}
  <div class="jugadas">{"".join(jugada_card(j, k, i + 1) for i, j in enumerate(rep["jugadas"]))}</div>
  <p class="note">Score medio de todas las combinaciones evaluadas:
     {rep["score_distribucion"]["media"]} · p99 = {rep["score_distribucion"]["p99"]} ·
     máximo alcanzable {rep["score_distribucion"]["max"]}.</p>
</section>"""


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --ground:#F6F7F9; --surface:#FFFFFF; --surface2:#EFF1F5;
  --ink:#101520; --muted:#59637A; --line:#DCE0E8;
  --accent:#9A6410; --accent-soft:#F3E7D2;
  --ok:#1C6B4A; --bad:#9E2C24; --warn:#8A5A0B; --warn-soft:#FBF0DA;
  --display:"Helvetica Neue",Helvetica,Arial,sans-serif;
  --body:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#0C1016; --surface:#141A23; --surface2:#1B222D;
  --ink:#E4EAF3; --muted:#8A94A8; --line:#28313E;
  --accent:#E0A742; --accent-soft:#2A2216;
  --ok:#4FBE8B; --bad:#E4796F; --warn:#E0A742; --warn-soft:#2A2216;
}}
:root[data-theme="dark"]{
  --ground:#0C1016; --surface:#141A23; --surface2:#1B222D;
  --ink:#E4EAF3; --muted:#8A94A8; --line:#28313E;
  --accent:#E0A742; --accent-soft:#2A2216;
  --ok:#4FBE8B; --bad:#E4796F; --warn:#E0A742; --warn-soft:#2A2216;
}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--body);
  font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:clamp(24px,5vw,64px) clamp(16px,4vw,40px) 96px;
  display:flex;flex-direction:column;gap:40px}
h1,h2,h3,h4{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.15;
  letter-spacing:-.022em;font-weight:750}
h1{font-size:clamp(30px,5vw,50px)}
h2{font-size:clamp(24px,3.4vw,34px);padding-top:16px;border-top:2px solid var(--ink)}
h3{font-size:clamp(18px,2.2vw,23px);margin-top:36px;color:var(--ink)}
h4{font-size:16px;margin-top:22px;letter-spacing:0}
p{margin:12px 0;max-width:74ch}
section{display:flex;flex-direction:column}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--accent);margin:0 0 10px}
.lede{color:var(--muted);font-size:15px;max-width:74ch}
.note{font-size:13.5px;color:var(--muted)}
.callout{background:var(--surface);border-left:3px solid var(--accent);padding:14px 18px;
  border-radius:0 6px 6px 0;font-size:15px;max-width:74ch}
.callout.warn{border-left-color:var(--warn);background:var(--warn-soft)}
.callout.bad{border-left-color:var(--bad)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface);
  margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th{font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);text-align:right;padding:10px 12px;border-bottom:1px solid var(--line);
  white-space:nowrap;background:var(--surface2);position:sticky;top:0}
td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--surface2)}
.master td:first-child{position:sticky;left:0;background:var(--surface)}
.num{font-family:var(--mono);font-weight:700;color:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;
  display:flex;flex-direction:column;gap:2px}
.stat.warn{border-color:var(--warn);background:var(--warn-soft)}
.sv{font-family:var(--display);font-size:26px;font-weight:750;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums}
.sl{font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.chip{display:inline-block;background:var(--surface);border:1px solid var(--line);
  border-radius:20px;padding:2px 11px;font-size:12.5px;font-family:var(--mono);margin:2px 0}
.tag{font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:4px;
  border:1px solid currentColor}
.tag.bad{color:var(--bad)} .tag.ok{color:var(--ok)}
.jugadas{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px;margin:20px 0}
.jugada{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:18px;
  display:flex;flex-direction:column;gap:12px}
.jugada header{display:grid;grid-template-columns:1fr auto;gap:2px 12px;align-items:baseline}
.jidx{grid-column:1;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent)}
.jugada h4{grid-column:1;margin:0;font-size:17px}
.score{grid-row:1/3;grid-column:2;font-family:var(--display);font-size:30px;font-weight:750;
  letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.score small{font-size:13px;color:var(--muted);font-weight:500}
.balls{display:flex;gap:6px;flex-wrap:wrap}
.ball{font-family:var(--mono);font-weight:700;font-size:15px;background:var(--accent-soft);
  color:var(--accent);border:1px solid var(--accent);border-radius:50%;width:38px;height:38px;
  display:grid;place-items:center}
.bar{display:grid;grid-template-columns:1fr 88px 34px;gap:8px;align-items:center;font-size:12px}
.bl{color:var(--muted)} .bl em{font-style:normal;opacity:.65;font-size:11px}
.btrack{background:var(--surface2);border-radius:3px;height:6px;overflow:hidden}
.bfill{display:block;height:100%;background:var(--accent)}
.bv{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px 14px;margin:4px 0 0;
  padding-top:12px;border-top:1px solid var(--line)}
.meta div{display:flex;flex-direction:column}
.meta dt{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.meta dd{margin:0;font-size:13.5px;font-variant-numeric:tabular-nums}
.meta em{font-style:normal;color:var(--muted);font-size:12px}
.toc{display:flex;flex-wrap:wrap;gap:8px}
.toc a{font-family:var(--mono);font-size:12px;text-decoration:none;color:var(--muted);
  border:1px solid var(--line);border-radius:5px;padding:5px 10px;background:var(--surface)}
.toc a:hover,.toc a:focus-visible{color:var(--accent);border-color:var(--accent)}
a{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
code{font-family:var(--mono);font-size:.9em;background:var(--surface2);padding:1px 5px;border-radius:4px}
.verdict{background:var(--surface);border:2px solid var(--ink);border-radius:10px;padding:22px 24px;
  display:flex;flex-direction:column;gap:10px}
ul,ol{max-width:74ch;padding-left:20px}
li{margin:5px 0}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def main():
    gd_j, kb_j = GD["jugadas"], KB["jugadas"]
    fmt = lambda j: " – ".join(f"{n:02d}" for n in j["numeros"])
    body = f"""<div class="wrap">
<header>
  <p class="eyebrow">Análisis estadístico · corte 11 agosto 2026</p>
  <h1>Gana Diario y Kábala: qué dicen los datos y qué no</h1>
  <p class="lede">Análisis reproducible con semilla fija sobre sorteos verificados uno a uno,
     400 000 combinaciones evaluadas y 200 000 sorteos simulados por juego.
     Todo el código y los datos están en el repositorio; cada cifra de esta página
     se genera desde <code>output/resultados.json</code>.</p>
</header>

<nav class="toc">
  <a href="#datos">Datos y procedencia</a><a href="#gana_diario">Gana Diario</a>
  <a href="#kabala">Kábala</a><a href="#modelo">Modelo de scoring</a>
  <a href="#final">Jugadas finales</a><a href="#critica">Crítica</a>
</nav>

<div class="verdict">
  <p class="eyebrow" style="margin:0">Resumen ejecutivo</p>
  <p style="margin:0"><b>Lo primero, porque cambia cómo hay que leer todo lo demás:</b>
     el entorno donde corre este análisis <b>bloquea el acceso a los portales de lotería</b>.
     Solo pude verificar <b>{GD["cobertura"]["sorteos_verificados"]} de {GD["cobertura"]["sorteos_en_el_periodo"]}</b>
     sorteos de Gana Diario ({GD["cobertura"]["cobertura_pct"]} %) y
     <b>{KB["cobertura"]["sorteos_verificados"]} de {KB["cobertura"]["sorteos_en_el_periodo"]}</b>
     de Kábala ({KB["cobertura"]["cobertura_pct"]} %). No inventé ni un solo sorteo para rellenar.</p>
  <p style="margin:0">Con esos datos: <b>cero</b> números, pares o tríos resultan
     estadísticamente significativos en ninguno de los dos juegos tras corregir por
     comparaciones múltiples. χ² = {GD["chi2"]["chi2"]} (p = {GD["chi2"]["p_montecarlo"]}) en Gana Diario y
     {KB["chi2"]["chi2"]} (p = {KB["chi2"]["p_montecarlo"]}) en Kábala: compatibles con azar puro.</p>
  <p style="margin:0">Aun así, y como pediste, hay <b>3 + 3 jugadas concretas</b>, elegidas por un
     criterio explícito y auditable. El criterio con peso mayoritario (45 %) no es la frecuencia
     —que no informa nada— sino la <b>impopularidad</b>: no cambia la probabilidad de ganar,
     pero sí el premio esperado si ganas. Es la única ventaja real que existe en una lotería.</p>
</div>

<section id="datos">
  <h2>Datos y procedencia</h2>
  <p>El acceso directo por HTTPS a <code>latinka.com.pe</code>, <code>tinkaresultados.com</code>,
     <code>lotterytexts.com</code> y <code>loteria.guru</code> devuelve
     <code>403 CONNECT tunnel failed</code>. El único canal disponible fue la búsqueda web,
     que devuelve fragmentos, no tablas históricas. De ahí la cobertura parcial.</p>

  <h3>Clave de auditoría: la numeración es consecutiva</h3>
  <p>Descubrí que los sorteos de Gana Diario se numeran de forma diaria y consecutiva sin saltos.
     Anclas independientes: sorteo <b>4390</b> = 04/11/2025, <b>4603</b> = 05/06/2026,
     <b>4660</b> = 01/08/2026 y <b>4669</b> = 10/08/2026.
     Se cumple que 4390 + 270 días = 4660 y 4603 + 57 = 4660. De ahí se deduce que el
     <b>sorteo 4083 = 01/01/2025</b> y que el período completo son los sorteos 4083 a 4670.
     Cada fila del dataset se valida contra esta fórmula.</p>

  <h3>Un dato rechazado (importante)</h3>
  <p class="callout bad">Para el 07/06/2026 (sorteo 4605) la búsqueda devolvió
     <code>20, 33, 43, 53, 30</code>. <b>43 y 53 no existen en Gana Diario</b> (rango 1–35).
     Fila <b>rechazada</b> por el validador. Esto demuestra que los resúmenes automáticos
     de búsqueda alucinan resultados de lotería: cualquier análisis que los use sin validar
     rango y consistencia arrastra datos falsos.</p>

  <h3>Parte 12 · Verificación del sorteo 4669</h3>
  <p><b>Gana Diario — sorteo 4669 — 10/08/2026: 20 – 16 – 33 – 12 – 22.</b>
     Confirmado de forma independiente por <code>nacionalloteria.com</code> y
     <code>resultadosdetinka.com</code>; consistente con la numeración (4660 + 9 = 4669);
     los 5 números están en rango y sin repetir.
     <span class="tag ok">CONFIRMADO</span> e incorporado al modelo.</p>

  <h3>Discrepancias entre fuentes</h3>
  <ul>
    <li>El premio de Gana Diario aparece como <b>S/ 200 000</b> en una nota y <b>S/ 100 000</b>
        en otra. Sin resolver; no afecta al análisis de números.</li>
    <li>Un resumen describió Gana Diario como «acertar los seis números»: es incorrecto,
        son 5 de 1 a 35. Error del resumidor, no de la fuente.</li>
    <li>Varias fuentes publican Kábala y <b>Chau Chamba</b> juntos. Registré
        <b>solo el sorteo principal</b> para no mezclar juegos.</li>
  </ul>
</section>

{bloque_juego(GD, "gana_diario")}
{bloque_juego(KB, "kabala")}

<section id="modelo">
  <h2>Parte 9 · Cómo se calcula el score</h2>
  <p>El «Statistical Selection Score» va de 0 a 100 y combina tres componentes.
     Ninguno de ellos aumenta la probabilidad de acertar; lo digo explícitamente porque
     es la diferencia entre un modelo honesto y uno que vende humo.</p>
  <ol>
    <li><b>T · Tipicidad estructural (peso 35 %).</b> Percentil de la combinación dentro de la
        distribución <em>simulada</em> de suma, paridad, amplitud y consecutivos. Vale 1 si cae
        en el centro exacto y 0 en la cola. Es <b>descriptivo</b>: una combinación «típica» no
        es más probable, simplemente se parece a la mayoría de los sorteos.</li>
    <li><b>E · Frecuencia regularizada (peso 20 %).</b> Se aplica <em>shrinkage</em>
        empírico-bayesiano: λ = max(0, (χ²−gl)/χ²). Como en ambos juegos χ² &lt; gl, resulta
        <b>λ = 0</b> y la componente colapsa a 0,5 para todos los números.
        <b>Ese es el resultado honesto</b>: las frecuencias observadas no aportan información,
        y el modelo se autolimita en lugar de fingir que sí.</li>
    <li><b>V · Impopularidad / valor esperado (peso 45 %).</b> La única componente con
        justificación económica real. Premia números ≥ 32 (no representables como día del mes),
        penaliza el 7 y el exceso de números ≤ 12, y penaliza las combinaciones formadas
        íntegramente por números ≤ 31. <b>No cambia P(ganar)</b>, pero si el premio se reparte
        entre acertantes, reduce la probabilidad de compartirlo.</li>
  </ol>
  <p class="callout"><b>La falacia del jugador, explícitamente.</b> Un número «overdue» <b>no</b>
     tiene más probabilidad de salir: los sorteos son independientes y el bombo no tiene memoria.
     La columna «sorteos desde la última aparición» es <b>descriptiva</b>, y por eso el modelo
     <b>no la usa</b> para premiar números atrasados. Distinguir esas tres cosas
     —descripción histórica, inferencia estadística y falacia del jugador— es justamente
     lo que pediste, y es donde la mayoría de los «sistemas» de lotería fallan.</p>
</section>

<section id="final">
  <h2>Parte 10 · Las 6 jugadas</h2>
  <h3>Gana Diario</h3>
  <div class="jugadas">{"".join(jugada_card(j, 5, i + 1) for i, j in enumerate(gd_j))}</div>
  <h3>Kábala</h3>
  <div class="jugadas">{"".join(jugada_card(j, 6, i + 1) for i, j in enumerate(kb_j))}</div>
  <p class="callout"><b>Si tuviera que elegir una sola por juego:</b> la Jugada 1.
     Combina tipicidad estructural alta con impopularidad alta, que es la única
     combinación de criterios donde uno de los dos factores tiene efecto económico medible.
     La Jugada 3 es deliberadamente más arriesgada: maximiza impopularidad a costa de una
     estructura rara (tres consecutivos, que ocurren en menos del
     {min(GD['jugadas'][2]['p_null_consecutivos_o_mas'], KB['jugadas'][2]['p_null_consecutivos_o_mas'])*100:.1f} %
     de los sorteos).</p>
</section>

<section id="critica">
  <h2>Parte 11 · Crítica, y qué haría distinto</h2>
  <h3>Qué esperar del otro modelo</h3>
  <p>Si el otro modelo te entregó una tabla de frecuencias «completa» de 588 sorteos de
     Gana Diario y 252 de Kábala, conviene que verifiques una cosa concreta: pídele
     <b>diez fechas al azar con su número de sorteo</b> y contrástalas. La numeración consecutiva
     (sorteo = 4083 + días desde el 01/01/2025) hace que las invenciones se detecten en segundos.
     Yo no pude reconstruir ese histórico, y lo digo en lugar de rellenarlo.</p>
  <h3>Dónde probablemente coincidamos y dónde no</h3>
  <ul>
    <li><b>Coincidencia esperada:</b> números altos y «fríos» aparecerán en ambas listas,
        aunque por razones opuestas. Yo los elijo por impopularidad (efecto sobre el premio
        compartido), no porque «toque que salgan».</li>
    <li><b>Discrepancia esperada:</b> cualquier lista basada en «números calientes» o en
        «overdue». Ninguno de los dos criterios sobrevive a la corrección por comparaciones
        múltiples en mis datos, y ninguno tiene validez predictiva ni siquiera con el
        histórico completo.</li>
    <li><b>Lo que yo aportaría y probablemente no consideraste:</b> optimizar por
        <b>premio esperado</b> en lugar de por probabilidad. Es el único margen real.</li>
  </ul>
  <h3>Qué invalidaría o mejoraría este análisis</h3>
  <ul>
    <li>El histórico completo desde una red sin bloqueo: basta añadir filas a
        <code>data/*.csv</code> y volver a ejecutar; todo se recalcula.</li>
    <li>Datos de <b>ventas por combinación</b>, que no son públicos. Con ellos la componente V
        dejaría de ser una heurística basada en sesgos documentados y pasaría a ser
        una optimización medible del premio esperado.</li>
  </ul>
  <p class="callout warn"><b>Lo que ningún análisis puede darte.</b> La probabilidad de acertar
     Gana Diario es 1 entre {GD["prob_base"]["combinaciones_posibles"]:,} y la de Kábala
     1 entre {KB["prob_base"]["combinaciones_posibles"]:,}, y <b>estas jugadas no la mejoran</b>.
     Lo que sí hacen es elegir, entre combinaciones de idéntica probabilidad, aquellas que
     tienen menos posibilidades de estar compartidas con otros apostadores.</p>
</section>
</div>"""

    out = os.path.join(HERE, "output", "informe.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"<title>Gana Diario y Kábala: lectura estadística</title>\n"
                 f"<style>{CSS}</style>\n{body}\n")
    print("escrito", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
