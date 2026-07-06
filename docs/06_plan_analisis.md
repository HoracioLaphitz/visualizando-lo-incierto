# Plan de Análisis (pre-registro) — Visualizando lo Incierto

**Versión:** 1.0
**Fecha:** 2026-07-06
**Relacionado:** `lineamiento_del_proyecto.md` (DTR, secciones 6-7), `docs/02b_operacionalizacion.md`, `docs/02_protocolo_investigacion.md`, `analysis/run_analysis.py`.

Este documento fija, antes de mirar los resultados agregados, qué hipótesis se testean, con qué prueba, con qué alfa, y qué patrón de resultados las refutaría. El objetivo es evitar HARKing (formular la hipótesis después de ver los datos).

---

## 1. Unidad de análisis

El análisis pareado usa **medias por participante y condición** (latencia media, tasa de exactitud), no filas de ensayo individuales. Las 10 preguntas por condición no son observaciones independientes entre sí (mismo sujeto, mismo bloque), así que promediarlas a nivel participante es el nivel correcto para la prueba T de muestras pareadas — de lo contrario se viola el supuesto de independencia y se infla artificialmente el n.

## 2. Hipótesis operacionalizadas

**H2 (Percepción y Carga Cognitiva)**, tal como aparece en el DTR sección 1:

- **H2a (latencia):** `latencia_B < latencia_A` — la latencia media por participante bajo la condición diagrama es menor que bajo la condición fórmula.
- **H2b (exactitud):** `accuracy_B > accuracy_A` — la tasa de exactitud por participante bajo la condición diagrama es mayor que bajo la condición fórmula.

**H1 (Semántica Visual)** no se testea directamente con estas pruebas cuantitativas; se aborda con el desglose por pregunta/concepto (sección 5) y con el análisis cualitativo fuera del alcance de este script.

## 3. Pruebas estadísticas

| Hipótesis | Prueba principal | Robustez | Alfa |
|---|---|---|---|
| H2a, H2b | T de Student para muestras pareadas (`scipy.stats.ttest_rel`) sobre agregados por participante | Wilcoxon signed-rank si Shapiro-Wilk sobre las diferencias da p < .05 | 0.05, dos colas |
| Contrabalanceo | T de Student para muestras independientes (`scipy.stats.ttest_ind`, Welch) comparando el grupo A-primero vs B-primero sobre la diferencia intra-sujeto (A − B) | — | 0.05, dos colas |

Para cada t-test pareado se reporta: `t`, grados de libertad, `p`, diferencia media, IC 95% de la diferencia, y `d` de Cohen para muestras pareadas (`dz = media_diferencias / DE_diferencias`).

## 4. Regla de decisión

- **p < 0.05** (dos colas): se rechaza la hipótesis nula de que no hay diferencia entre condiciones.
- El signo de la diferencia debe coincidir con la dirección predicha por H2 (latencia_B menor, exactitud_B mayor). Un resultado significativo en la dirección **opuesta** no confirma H2 — indica el efecto contrario.
- Si `n` de participantes con datos completos en ambas condiciones es menor a 5, se omite toda inferencia y se reportan solo descriptivos (el poder estadístico y la robustez a outliers con n < 5 no son interpretables).

## 5. Análisis exploratorios / secundarios (no confirmatorios)

- **Desglose por pregunta:** exactitud y latencia mediana por pregunta y condición, para identificar qué diagramas (Venn vs árbol, por concepto: unión, intersección, complemento, independencia, condicional, Bayes) ayudaron o perjudicaron — insumo directo para la matriz de correlación de la sección 7 del DTR (elemento visual vs comprensión).
- **Efecto de orden:** valida que el contrabalanceo (paridad de `participant_id`, ver `docs/02_protocolo_investigacion.md` sección 1.1) neutralizó el aprendizaje/fatiga entre bloques. No es una hipótesis del proyecto — es un chequeo de validez interna del diseño.

## 6. Exclusiones (ya aplicadas antes de este análisis)

Aplicadas en `src/data/export.py` (`apply_exclusions`), aguas arriba de este script — ver también `docs/02_protocolo_investigacion.md` sección 4:

1. Filas con `latency_seconds` fuera de [2, 300] segundos.
2. Participantes sin `finalized_at` (sesión incompleta).
3. Participantes con menos de 20 respuestas (diseño pareado incompleto).

Este plan de análisis no aplica exclusiones adicionales; si `analysis/run_analysis.py` detecta un participante sin datos en ambas condiciones a pesar del filtro de export, lo excluye del análisis pareado y lo reporta explícitamente (no lo descarta en silencio).

## 7. Qué patrón de resultados REFUTARÍA cada hipótesis

- **H2a se refuta** si la diferencia de latencia (A − B) no es significativa (p ≥ 0.05), o si es significativa pero en la dirección opuesta (latencia_B > latencia_A, es decir, el diagrama fue más lento).
- **H2b se refuta** si la diferencia de exactitud (A − B) no es significativa (p ≥ 0.05), o si es significativa pero en la dirección opuesta (accuracy_B < accuracy_A, es decir, el diagrama produjo menos aciertos).
- Un patrón mixto (ej. H2a confirmada pero H2b refutada) no refuta H2 en bloque — se reporta cada sub-hipótesis por separado, ya que miden carga cognitiva desde ángulos distintos (velocidad vs precisión) y podrían disociarse (ej. respuestas más rápidas pero no más precisas sugeriría un atajo heurístico sin comprensión real, lo cual sería en sí un hallazgo relevante para H1).
- Si el chequeo de efecto de orden resulta significativo (p < 0.05), no refuta H2 pero **debilita la validez interna** del contraste A vs B, porque parte de la diferencia observada podría deberse a orden/aprendizaje y no al estímulo (fórmula vs diagrama) en sí.
