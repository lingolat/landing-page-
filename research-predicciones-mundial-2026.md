# Plataforma de Predicciones Deportivas — Mundial 2026
### Research Completo | Junio 2026

---

## Contexto del Proyecto

- **Objetivo:** Plataforma que usa datos históricos de fútbol para generar probabilidades precisas de resultados
- **Foco inicial:** FIFA World Cup 2026 (en curso)
- **Modelo de negocio:** Venta de predicciones por suscripción
- **Perfil:** Fundador sin experiencia técnica, aprendiendo desde cero

---

## 1. APIs de Datos Históricos

| API | Precio | Qué incluye |
|-----|--------|-------------|
| **TheStatsAPI** | Trial gratis | Historial desde 1930, todos los Mundiales |
| **worldcupapi.com** | Gratis | Scores en vivo, estadísticas, lineups |
| **GitHub Open Source** | Gratis | Datos World Cup 2026 en tiempo real |
| **Sportmonks** | €69–129/mes | Histórico + predicciones + xG + Pressure Index |
| **SportsDataIO** | Pago | Odds, lineups, stats, historial completo |

**Para empezar:** `TheStatsAPI` (trial gratis, datos desde 1930) + repo GitHub con datos del Mundial 2026.

### Links
- https://www.thestatsapi.com/world-cup
- https://worldcupapi.com/
- https://www.sportmonks.com/football-api/world-cup-api/
- https://sportsdata.io/fifa-world-cup-api
- https://github.com/rezarahiminia/worldcup2026

---

## 2. Modelos Predictivos

### Nivel 1 — ELO Rating (más fácil de entender)
- Cada equipo tiene un puntaje que sube/baja según resultados históricos
- Comparas puntajes → generas probabilidad de ganar
- Punto de entrada ideal para aprender

### Nivel 2 — Poisson Model
- Modela cuántos goles anotará cada equipo basado en promedios históricos
- Tutorial completo con código Python disponible

### Nivel 3 — Dixon-Coles (estándar profesional)
- Mejora el Poisson para partidos de bajos goles (0-0, 1-1)
- Da probabilidades más precisas
- Código disponible en Python y Jupyter Notebooks

### Repo Clave — Usar como Base
**`github.com/Hicruben/world-cup-2026-prediction-model`**
- Combina ELO + Dixon-Coles + Monte Carlo
- Diseñado específicamente para el Mundial 2026
- Open source, sin caja negra de ML

### Tutoriales
- Dixon-Coles tutorial: https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/
- ELO + Poisson: https://johnknightstats.com/posts/elo_sim_model/index.html

---

## 3. Modelo de Negocio

### Opciones probadas

**A) Suscripción mensual** ← Recomendado
- Usuarios pagan $9–29/mes
- Reciben predicciones diarias o por partido
- Ingresos predecibles, bajo costo de marketing recurrente

**B) Paquetes por partido**
- Vendes cada predicción individualmente ($2–10)
- Más volátil pero fácil para probar el mercado

**C) Acceso API premium**
- Para apostadores profesionales
- $50–200/mes, nicho pero lucrativo

### Insight clave
> El éxito no depende solo del modelo matemático — depende del **marketing y adquisición de clientes**. Construir audiencia en Telegram, Instagram o TikTok mostrando resultados reales es crítico.

### Herramientas para cobrar
- **Stripe** — 2.9% por transacción, fácil de integrar
- **Gumroad** — ideal para empezar sin código
- **Whop** — plataforma específica para vender acceso a comunidades/predicciones

---

## 4. Stack Tecnológico Recomendado

### Ruta rápida (semanas, no meses)

```
Datos históricos → Python → Streamlit → Telegram Bot → Stripe
```

| Herramienta | Para qué | Costo |
|-------------|----------|-------|
| **Python** | Correr los modelos predictivos | Gratis |
| **Google Colab** | Ejecutar código sin instalar nada | Gratis |
| **Streamlit** | Dashboard visual sin necesidad de frontend | Gratis |
| **Telegram Bot** | Enviar predicciones a suscriptores automáticamente | Gratis |
| **Stripe** | Cobrar suscripciones | 2.9% por transacción |
| **Carrd.co / Webflow** | Landing page sin código | Gratis / $16 mes |

### Para la landing page
El repo `lingolat/landing-page-` puede ser la landing de ventas de la plataforma.

---

## 5. Competencia — Plataformas Existentes

| Plataforma | Modelo | Lección |
|------------|--------|---------|
| **Forebet** | Gratis, algorítmico, 1200+ ligas | Modelo estadístico funciona, pero gratis no monetiza |
| **Kickform** | Histórico + forma actual, estadísticas avanzadas | Nicho específico pero audiencia fiel |
| **Foobol** | Gratis, fútbol | Monetiza con publicidad |
| **Bet2Invest** | Tipsters certificados + suscripción | Comunidad + comisión funciona bien |

### Tu ventaja diferencial
Enfocarte 100% en el **Mundial 2026 ahora mismo** — audiencia masiva, urgencia real, competencia dispersa.

---

## 6. Hoja de Ruta — 4 Semanas

| Semana | Acción |
|--------|--------|
| **1** | Clonar repo `Hicruben/world-cup-2026-prediction-model`, publicar primeras predicciones gratis en Telegram/Instagram |
| **2** | Montar landing page en este repo, agregar formulario de suscripción |
| **3** | Integrar Stripe, lanzar tier de pago ($9–15/mes) |
| **4** | Iterar con feedback, agregar dashboard Streamlit para suscriptores |

---

## Fuentes

- https://www.thestatsapi.com/blog/best-world-cup-2026-apis
- https://github.com/Hicruben/world-cup-2026-prediction-model
- https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/
- https://www.boydsbets.com/sell-sports-picks/
- https://ideas.maxincubator.com/football-betting-saas-37k-year/
- https://www.valuethemarkets.com/prediction-markets/forebet-review-how-data-driven-football-forecasts-work-and-their-limits
- https://bet2invest.com/blog/Tipster-Platform:-Our-Vision-of-Freedom-and-Transparency-in-Sports-Betting-Predictions
- https://anotherwrapper.com/tools/micro-saas-ideas/10-micro-saas-ideas-for-sports-betting-punters
