# Operacionalización de Variables — Visualizando lo Incierto

**Versión:** 1.0
**Fecha:** 2026-07-06
**Relacionado:** `docs/02_protocolo_investigacion.md`, `data/questions.json`.

## Tabla de operacionalización

| Variable | Tipo | Cómo se captura | Escala |
|---|---|---|---|
| **Condición (A/B)** | Independiente, intra-sujeto | Etiqueta asignada por la app según la regla de contrabalanceo (paridad del ID de participante); registrada junto a cada respuesta como `condition` (`"A"` (fórmula) \| `"B"` (diagrama)) — columna real de `src/data/export.py` | Nominal, 2 niveles |
| **Orden de bloques** | Control | No se exporta como columna propia: `analysis/run_analysis.py` (`derive_order_block`) la deriva post-hoc a partir de qué condición aparece en `block == 1` para cada participante, dando `"A_primero"` \| `"B_primero"` | Nominal, 2 niveles |
| **Latencia** | Dependiente | `timestamp_submit − timestamp_render` por pregunta, en segundos; registrada como `latency_seconds` | Razón (continua, segundos), rango válido 2–300 |
| **Exactitud** | Dependiente | `answer_index == correct_index` por pregunta; registrada como `correct` (0/1). La tasa de exactitud por condición = promedio de `correct` sobre las 10 preguntas del bloque | Binaria por ítem; proporción (0.0–1.0) por condición/sujeto |
| **Perfil de formación** | Control (covariable) | Autoreporte en el formulario demográfico; registrada como `education_profile` (perfil) | Nominal, 3 niveles (`Humanistico`, `Tecnico`, `Mixto`) |
| **Familiaridad con probabilidad** | Control (covariable) | Autoreporte, escala Likert; registrada como `probability_familiarity` (familiaridad) | Ordinal, 1–5 |
| **Rango etario** | Control (covariable, descriptiva) | Autoreporte; registrada como `age_range` (rango etario) | Ordinal por bandas (`18-24` … `55+`) |
| **Concepto de la pregunta** | Control (para análisis por subtipo) | Tomado de `concept` en `data/questions.json` (`union`, `intersection`, `complement`, `independence`, `conditional`, `bayes`) | Nominal, 6 niveles |
| **Dificultad de la pregunta** | Control (para análisis por subtipo) | Tomado del diseño del banco de preguntas (fijo, no autoreportado): 3 fáciles, 4 medias, 3 difíciles | Ordinal, 3 niveles |

## Notas de uso

- **Condición** y **orden de bloques** son variables distintas: la primera indica qué estímulo vio el sujeto en esa pregunta puntual; la segunda indica en qué bloque (1° o 2°) ocurrió, para poder controlar el efecto de orden/aprendizaje en el análisis (t-test pareado, sección 6 del DTR). La condición se persiste como columna (`condition`); el orden de bloques **no** se persiste — se deriva en el momento del análisis (ver `docs/06_plan_analisis.md`), porque es 100% reconstruible a partir de `condition` + `block` y no vale la pena duplicarlo como columna en el export.
- **Latencia** y **exactitud** se registran a nivel de pregunta individual (10 filas × 2 condiciones × 30 sujetos = 600 observaciones máximo), no solo a nivel de bloque, para permitir tanto el análisis agregado por condición como el análisis por concepto/dificultad.
- Las covariables (`education_profile`, `probability_familiarity`, `age_range`) no se usan para excluir datos; se reportan de forma segmentada según el riesgo de sesgo de muestra identificado en `docs/01_product_brief.md` (sección 6).
- Los criterios de exclusión de `latency_seconds` (< 2 o > 300 segundos) y de sesiones incompletas se aplican antes de calcular las medias por condición — ver `docs/02_protocolo_investigacion.md`, sección 4, y se implementan en `src/data/export.py` (`apply_exclusions`).
