# 08 — Reglas de Sintaxis Visual para la Probabilidad v0.1

**Autores:** UX Researcher + DX/Visual Designer
**Fuente de verdad:** `lineamiento_del_proyecto.md` (DTR, sección 8: entregable final normativo), `docs/03_sistema_diseno.md`, `docs/06_plan_analisis.md`, `analysis/run_analysis.py`.
**Relacionado:** `docs/07_arquitectura_agentes.md` (Subagente 4.2 "Diseñador de Alternativas").

---

## Estado del documento

**v0.1 — teórica, n=0.** Este documento existe *antes* de tener datos porque el DTR (sección 8) exige un entregable normativo al final del proyecto, y bloquear su redacción hasta tener los 30 participantes desperdiciaría el trabajo teórico ya hecho en `docs/03_sistema_diseno.md`. En vez de eso, cada regla se declara ahora **grounded en teoría** (Gestalt + semiótica peirceana) con una **predicción medible explícita**, y queda con un estado que se actualiza cuando lleguen los datos:

| Estado | Significado |
|---|---|
| `[TEÓRICA]` | Fundamentada en Gestalt/Peirce y en el diseño de `docs/03`, sin evidencia empírica propia todavía. Estado inicial de las 14 reglas. |
| `[VALIDADA]` | El desglose por pregunta de `run_analysis.py` (o el t-test agregado) confirma la dirección predicha con la significancia definida en `docs/06_plan_analisis.md`. |
| `[REFUTADA]` | Los datos muestran el efecto contrario o nulo al predicho. La regla se retira o se invierte explícitamente, no se borra (trazabilidad del error, ver DTR §7). |
| `[REVISADA]` | Los datos confirman una tendencia pero con matices (ej. solo para cierto tipo de concepto o dificultad) — la regla se reescribe con el alcance acotado. |

Ninguna regla de este documento debe leerse como verdad establecida mientras diga `[TEÓRICA]`. Es una **hipótesis de diseño operacionalizada**, no una convención probada.

---

## 1. Reglas normativas

### R1 — Color fijo y consistente por evento

**Enunciado:** Todo evento/conjunto (A, B, y cada rama del árbol) debe recibir un único color, fijo a través de las 10 preguntas de una misma condición. Nunca reasignar colores entre preguntas.

**Fundamento teórico:** Ley de Gestalt de **semejanza** (similarity) — el sistema visual agrupa elementos del mismo color en la etapa preatencional. Peirce: el color-por-evento es un **símbolo** (convención arbitraria aprendida), no un ícono ni un índice (`docs/03` §4.1).

**Predicción medible:** en el desglose por pregunta de `run_analysis.py` (`per_question_breakdown`), las preguntas de concepto `union` e `intersection` (q01-q02, Venn, dependen más de rastrear qué región es cuál) deberían mostrar `accuracy_B > accuracy_A` y `median_latency_B < median_latency_A` de forma más marcada que en preguntas de `bayes` (q08-q10), donde la carga cognitiva depende más de la operación aritmética que del etiquetado de eventos.

**Estado:** `[TEÓRICA]`

---

### R2 — Relleno sólido y opaco en la intersección, nunca solo contorno

**Enunciado:** La región de intersección A∩B debe rellenarse con opacidad alta (≥0.85) y visualmente más densa que las regiones exclusivas ("solo A", "solo B"). Prohibido representar la intersección únicamente con líneas de contorno cruzadas.

**Fundamento teórico:** Ley de Gestalt de **cierre** (closure) — una región delimitada y rellena se percibe como unidad figura/fondo más fuerte que una delimitada solo por líneas. Peirce: el Venn completo es un **ícono** de semejanza topológica (`docs/03` §4.2).

**Predicción medible:** q02 (`intersection`) debería mostrar la mayor diferencia `accuracy_diff = accuracy_B − accuracy_A` de todo el banco, dado que es la única pregunta cuyo concepto nuclear es exactamente esta región. Si `accuracy_diff` en q02 no es la mayor o es negativa, la regla queda candidata a refutación.

**Estado:** `[TEÓRICA]`

---

### R3 — Grosor de rama proporcional a la probabilidad

**Enunciado:** En diagramas de árbol, el grosor de cada rama debe ser proporcional a su valor de probabilidad. Prohibido usar grosor uniforme cuando las probabilidades de las ramas hermanas difieren en más de un orden de magnitud.

**Fundamento teórico:** Ley de Gestalt de **buena continuidad** (good continuation) aplicada a las curvas de Bézier de las ramas, más una capa icónica superpuesta: el grosor *se parece* a la magnitud (ícono de cantidad sobre un índice de dirección). Peirce: la rama es un **índice** (apunta a una consecuencia); el grosor variable añade semejanza icónica de cantidad (`docs/03` §4.3).

**Predicción medible:** q09 (test de enfermedad, tasa base 1%, la falacia de tasa base de manual) es el caso crítico documentado en `docs/03` §4.3 como ambiguo a propósito. Predicción principal: `accuracy_B > accuracy_A` en q09 porque la rama "Sano" gruesa comunica dominancia antes de cualquier cálculo. Predicción de riesgo (documentada porque es plausible que ocurra lo contrario): el grosor podría anclar al participante en la rama gruesa y producir un patrón de error sistemático hacia "confundir P(enfermo|positivo) con P(positivo|enfermo)" — si aparece, la regla se revisa para acotar cuándo el grosor ayuda vs. cuándo ancla.

**Estado:** `[TEÓRICA]`

---

### R4 — Codificación directa de valores, no leyenda separada

**Enunciado:** Los valores numéricos (probabilidades) y las etiquetas de evento deben aparecer **sobre o adyacentes a la marca visual que representan** (region/rama). Prohibida una leyenda o tabla de referencia separada que obligue a alternar la mirada entre marca y clave.

**Fundamento teórico:** Teoría de la Carga Cognitiva de Sweller — el "efecto de atención dividida" (split-attention effect): cuando la información relevante está espacialmente separada, el usuario gasta memoria de trabajo en integrar mentalmente ambas fuentes en vez de en el contenido. Es un principio de diseño de información transversal a Gestalt, no una ley Gestalt específica.

**Predicción medible:** Es una regla de diseño ya aplicada de forma universal en `optimized` (no hay variante A/B interna para testearla aisladamente con el material actual). Su evidencia vendrá indirectamente: si la latencia en `B` no baja respecto de `A` pese a que R1-R3 se validen, es señal de que el etiquetado directo por sí solo no alcanza y merece una iteración con el Subagente 4.2 (Diseñador de Alternativas) aislando esta variable.

**Estado:** `[TEÓRICA]` — nota: sin contraste directo A/B interno en el diseño actual; requiere iteración 2 dedicada.

---

### R5 — Notación `P(A)` como símbolo neutro al idioma, nunca palabras completas

**Enunciado:** Usar siempre notación matemática estándar (`P(A)`, `P(A∩B)`, `¬A`, `P(B|A)`) en las etiquetas, nunca su traducción en palabras ("probabilidad de A"). Excepción: cuando el `diagram_spec` de la pregunta ya usa claves semánticas largas (ej. q09: `enfermedad`/`sano`/`pos`/`neg`), abreviar a 3-4 caracteres en vez de usar la palabra completa.

**Fundamento teórico:** Peirce — `P(A)` es un **símbolo** puro (convención arbitraria sin semejanza icónica ni conexión indicial), elegido por ser neutro al idioma y no competir tipográficamente con el resto del texto en español (`docs/03` §3).

**Predicción medible:** Esta regla no predice una diferencia A/B (aplica dentro de B únicamente) sino una ausencia de correlación entre longitud de etiqueta y latencia dentro de la condición B: si preguntas con etiquetas más largas (q09/q10, con "Enf./Sano/Pos./Neg.") muestran una `median_latency_B` desproporcionadamente mayor que preguntas con notación pura de una letra (q01-q04), eso sugiere que la abreviación no fue suficiente y la regla debe revisarse (quizás iconografía en vez de texto).

**Estado:** `[TEÓRICA]`

---

### R6 — Venn para operaciones de conjuntos estáticas; árbol para procesos secuenciales/condicionales

**Enunciado:** Usar diagrama de Venn cuando el concepto es `union`, `intersection`, `complement` o `independence` (relaciones estáticas entre conjuntos, sin orden temporal). Usar árbol cuando el concepto es `conditional` o `bayes` (la probabilidad depende de una secuencia de eventos: "dado que ocurrió X, ¿qué tan probable es Y?").

**Fundamento teórico:** Peirce: el Venn es icónico por semejanza espacial *atemporal* (superposición = superposición lógica, sin secuencia); el árbol es indicial *direccional/temporal* (la flecha apunta de un evento a su consecuencia). Mapea directamente a la pregunta secundaria del DTR §2: "¿el árbol impone una comprensión temporal/secuencial que la fórmula no explicita?".

**Predicción medible:** Esto ya está fijo en el diseño actual (`data/questions.json`: q01-q04 → `venn`, q05-q10 → `tree`), así que no hay contraste Venn-vs-árbol para el mismo concepto en el material actual. La validación vendrá de que **dentro de cada grupo**, `accuracy_B > accuracy_A` se sostenga con magnitud comparable — si el grupo árbol (`conditional`/`bayes`) muestra una ganancia B mucho menor que el grupo Venn, es evidencia de que el árbol es una traducción semiótica menos eficiente que el Venn para su categoría de concepto, y motivaría una iteración 2 que pruebe Venn condicional (áreas proporcionales anidadas) como alternativa para `conditional`/`bayes`.

**Estado:** `[TEÓRICA]`

---

### R7 — Sin efectos 3D ni pseudo-profundidad

**Enunciado:** Prohibidos biseles, sombras proyectadas, gradientes que simulen volumen, o cualquier efecto que sugiera profundidad en un diagrama que representa una cantidad 2D (área o proporción).

**Fundamento teórico:** El área en un Venn es icónica de la probabilidad (`docs/03` §4.2); un efecto 3D introduce una variable perceptual (profundidad aparente) que no corresponde a ninguna magnitud matemática real, generando una lectura ambigua entre "esto es más grande" vs. "esto está más cerca". Es ruido semiótico: un ícono que sugiere una relación que no existe en los datos.

**Predicción medible:** No aplica al material actual (`generate_diagrams.py` no genera 3D en ninguna variante), por lo que no hay una fila de `per_question_breakdown` que la confirme o refute directamente todavía. Se mantiene como anti-regla preventiva basada en literatura de dataviz (Cleveland & McGill, jerarquía de precisión perceptual: área 2D > volumen 3D para juicios de magnitud) y queda pendiente de una validación explícita si el Subagente 4.2 propone alguna vez una variante 3D para comparar.

**Estado:** `[TEÓRICA]` — sin variante de contraste en el material actual; regla preventiva por literatura externa, no por diseño interno del experimento.

---

### R8 — Leyenda nunca separada de la marca (anti-patrón de atención dividida)

**Enunciado:** Si por alguna razón se necesita una clave de referencia (ej. escala de color), debe ubicarse a menos de una "distancia de sacada ocular corta" del elemento que describe (regla operacional: dentro del mismo cuadro visual, no en un margen o pie de imagen separado).

**Fundamento teórico:** Extensión directa del split-attention effect (Sweller) ya citado en R4, aplicado específicamente al caso de leyendas/claves en vez de etiquetas de valor.

**Predicción medible:** Igual que R4: sin contraste interno A/B en el material del MVP (los `optimized` actuales no usan leyendas separadas del todo — es la aplicación consistente de la regla, no una variante a testear). Evidencia indirecta: si el análisis cualitativo (protocolo de pensar en voz alta, DTR §5) futuro registra fragmentos de "confusión" correlacionados con necesidad de releer una clave, se cuenta como apoyo cualitativo a R8 aunque no haya contraste cuantitativo A/B propio.

**Estado:** `[TEÓRICA]`

---

### R9 — Sin marginales redundantes cuando son derivables de las regiones dibujadas

**Enunciado:** No anotar valores marginales (`P(A)`, `P(B)`, `P(A∪B)`) como texto adicional si ya son matemáticamente derivables sumando las regiones (`solo A` + intersección) que el diagrama ya dibuja. Mostrarlos solo si aportan un atajo de lectura que el participante no puede reconstruir visualmente en menos de un vistazo.

**Fundamento teórico:** Es la traducción directa a regla normativa del hallazgo de `docs/03` §6.3: el `diagram_spec` de q02 y q01/q02/q04 incluye `p_union`/`p_a`/`p_b` marginales que son redundantes con `set_a_only + intersection`, y el script de generación **deliberadamente no los dibuja** porque matplotlib-venn solo necesita las áreas atómicas para el área proporcional. Redundancia visual no aporta información nueva y compite por atención con la región que sí importa (riesgo de ruido cognitivo, ver anti-regla).

**Predicción medible:** Si en una iteración futura el Subagente 4.2 (`docs/07` §5, comando `alternatives`) propone una variante que sí anota los marginales redundantes para q01/q02/q04, la predicción es que esa variante **no mejore** `accuracy` ni `latency` respecto del `optimized` actual (porque no agrega información, solo texto) — sirviendo como test de control de la hipótesis "más anotación = mejor comprensión", que H1/H2 predicen que es falsa en general.

**Estado:** `[TEÓRICA]` — grounded en el hallazgo de diseño documentado en `docs/03` §6.3, pendiente de contraste empírico en iteración 2.

---

### R10 — Jerarquía tipográfica proporcional a la dificultad cognitiva del valor, no al orden de lectura

**Enunciado:** El tamaño/peso de fuente de cada etiqueta numérica debe ser mayor para el valor que requiere más operaciones mentales para derivarse de la fórmula original (ej. la intersección, que requiere retener y combinar 3 números), y menor para valores atómicos de lectura directa.

**Fundamento teórico:** Aplicación de jerarquía visual (peso visual, principio de dataviz general) calibrada específicamente por *carga cognitiva de la fórmula equivalente* (Sweller), no por convención tipográfica arbitraria — ver `docs/03` §3.

**Predicción medible:** Comparar `median_latency_B` entre preguntas donde el valor jerarquizado (mayor tamaño) es el que se pregunta directamente (debería bajar latencia) vs. preguntas donde se pregunta por un valor atómico (la jerarquía no debería afectar, o podría incluso distraer levemente). Si no hay diferencia, sugiere que la jerarquía tipográfica no es un canal Gestalt suficientemente fuerte por sí solo comparado con color/cierre/grosor.

**Estado:** `[TEÓRICA]`

---

### R11 — Paleta con doble canal de distinción (matiz + luminancia), nunca solo matiz

**Enunciado:** Todo par de colores que codifique eventos distintos (A vs B) debe ser distinguible por al menos dos canales perceptuales independientes (ej. matiz Y luminancia), no solo por matiz.

**Fundamento teórico:** No es una ley Gestalt sino un requisito de accesibilidad perceptual que *condiciona* si la ley de semejanza (R1) puede aplicarse en absoluto para un subconjunto de la muestra: sin el segundo canal, un participante con daltonismo rojo-verde no puede ejecutar el agrupamiento perceptual que R1 predice. `docs/03` §2 ya fundamenta la elección de Okabe-Ito por esta razón, con n=30 sin poder para excluir por condición visual.

**Predicción medible:** No es directamente testeable con el desglose por pregunta (no se captura visión del color como covariable — omisión reconocida, ver Anti-rules). Su validación depende de que ningún participante reporte confusión de eventos en el protocolo de pensar en voz alta atribuible a color. Se recomienda agregar una pregunta de screening de daltonismo al formulario demográfico para la iteración 2 si se quiere validar esta regla directamente en vez de por inferencia negativa.

**Estado:** `[TEÓRICA]` — gap de instrumentación identificado: falta covariable de daltonismo en `docs/02b_operacionalizacion.md`.

---

### R12 — Atenuación de contraste para la rama/región "no objetivo"

**Enunciado:** Toda rama o región que no es la respuesta objetivo de la pregunta (ej. la rama complementaria en un árbol de Bayes) debe dibujarse con contraste deliberadamente bajo (gris neutro) respecto de la rama/región objetivo, que mantiene el color de acento saturado.

**Fundamento teórico:** Extensión de la ley de semejanza combinada con jerarquía de atención: el contraste bajo es una señal preatencional de "menor relevancia", guiando la primera fijación ocular predicha (ver rol de "Analista Gestáltico" en `docs/07`) hacia la rama relevante sin necesidad de instrucción textual.

**Predicción medible:** El Subagente 1.2 "Analista Gestáltico" (`docs/07` §3, `semiotist.GestaltAnalyst`) puede predecir teóricamente el punto de primera fijación antes de tener eye-tracking real; cuando el DTR §5 obtenga datos de eye-tracking/grabación de pantalla, la predicción a validar es que la primera fijación cae sobre la rama de acento (verde azulado) y no sobre la rama gris, para las preguntas de concepto `bayes`.

**Estado:** `[TEÓRICA]` — depende de instrumentación de eye-tracking aún no recolectada (DTR §5); sin esa señal, se puede aproximar con el patrón de errores (¿el participante confunde la rama objetivo con la atenuada?).

---

### R13 — La condición control (fórmula) no debe rediseñarse para "ayudar" — debe permanecer cruda

**Enunciado:** El material de la Condición A (fórmula) no debe recibir ninguna mejora de diseño de información (color, jerarquía, espaciado semántico) que no reciba también un tratamiento equivalente explícito y documentado. Es el control experimental de H1, no el control de diseño (ese rol lo cumple `baseline`, ver `docs/03` §1).

**Fundamento teórico:** Validez interna del diseño cuasi-experimental (DTR §5): si A recibe mejoras de diseño no controladas, cualquier diferencia A-vs-B deja de aislar la variable "fórmula vs. diagrama" y empieza a confundirse con "diseño prolijo vs. diseño descuidado".

**Predicción medible:** No es una predicción de dirección de efecto sino una condición de validez: se verifica revisando que el material A generado sea estático entre iteraciones (no debería cambiar salvo que cambie la pregunta). Si en iteración 2 se detecta que A cambió sin razón documentada, cualquier comparación con datos de iteración 1 queda invalidada.

**Estado:** `[TEÓRICA]` — regla de proceso/validez interna, no de percepción; se verifica por auditoría de artefactos, no por estadística.

---

### R14 — Toda variante Gestalt-optimizada que module H2 en dirección opuesta se documenta, no se descarta

**Enunciado:** Si un elemento de diseño Gestalt (grosor, color, cierre) produce un patrón de error sistemático o una latencia mayor en la condición B para una pregunta específica, esa observación debe registrarse como hallazgo de H1/H2 (posible sesgo perceptual inducido por la imagen, DTR §2) y disparar el pipeline de iteración del Subagente 4.2, no descartarse como ruido de muestra.

**Fundamento teórico:** Es la traducción operativa directa de la pregunta secundaria del DTR: "¿Existen sesgos perceptuales generados por la imagen que no existen en la fórmula matemática?". Una regla Gestalt bien aplicada según la teoría puede aun así introducir un sesgo (ver el caso ambiguo de R3/q09 documentado en `docs/03` §4.3) — el diseño *anticipa* esta posibilidad en vez de asumir que Gestalt siempre ayuda.

**Predicción medible:** Cualquier fila de `per_question_breakdown` con `accuracy_diff < 0` (B peor que A) o `median_latency_diff > 0` (B más lento) dispara automáticamente esta regla: no se descarta como outlier, se pasa como `--evidence` al comando `alternatives` del orquestador (`docs/07` §5) para generar 3 variantes de rediseño de esa pregunta puntual.

**Estado:** `[TEÓRICA]` — es una regla de *proceso*, no de diseño visual; se activa automáticamente ante evidencia contraria, ver sección 3 de este documento.

---

## 2. Anti-reglas (fuentes de ruido cognitivo)

Estas no son reglas normativas de "hacer X" sino advertencias explícitas de qué evitar, consolidadas de lo ya fundamentado arriba:

1. **Efectos 3D / pseudo-profundidad** en representaciones de área o proporción (R7) — introduce una lectura de magnitud ambigua entre tamaño real y profundidad aparente.
2. **Leyendas o claves de color separadas espacialmente de la marca** (R4, R8) — fuerza atención dividida (Sweller) y anula parcialmente la ganancia de la ley de semejanza.
3. **Anotaciones marginales redundantes** ya derivables de las regiones dibujadas (R9) — el hallazgo de `docs/03` §6.3 muestra que el propio `diagram_spec` contiene estos valores (`p_union`, `p_a`, `p_b`) y el generador los omite deliberadamente del dibujo por esta razón.
4. **Grosor/color uniforme cuando las probabilidades subyacentes son muy dispares** — es la negación de R3; retrocede al `baseline` monocromo de grosor fijo, que es exactamente el control de diseño que el proyecto usa para medir la ganancia de las leyes Gestalt, no el estímulo real.
5. **Traducir la notación simbólica (`P(A)`) a palabras completas** — anula la neutralidad de idioma de R5 y compite tipográficamente con el resto del texto en español.
6. **Rediseñar la Condición A "para que no se vea tan fea"** (R13) — contamina el control experimental de H1.

---

## 3. Proceso de actualización (pipeline concreto)

```
1. src/data/export.py
   → export_raw.csv, export_clean.csv (exclusiones ya aplicadas)

2. analysis/run_analysis.py --input data/results/export_clean.csv
   → report.md: descriptivos, t-test pareado (H2a/H2b), chequeo de orden
   → per_question_breakdown: accuracy_A/B, median_latency_A/B, n_A/B, accuracy_diff, median_latency_diff
     por question_id (10 filas, mapeadas a concept vía data/questions.json)

3. Identificar diagramas con bajo desempeño:
   filtrar filas de per_question_breakdown donde
     accuracy_diff <= 0   (el diagrama no superó o empató a la fórmula)
     o median_latency_diff >= 0   (el diagrama fue igual de lento o más lento)
   → estas son las preguntas candidatas a activar R14.

4. Para cada pregunta candidata:
   python -m src.agents.orchestrator alternatives --question {qid} \
       --evidence "accuracy_diff={x}, median_latency_diff={y}"
   → {qid}_alternatives_{ts}.json: 3 variaciones de diseño Gestalt-fundamentadas
     (Subagente 4.2 "Diseñador de Alternativas", docs/07_arquitectura_agentes.md)

5. Seleccionar la variante más prometedora por pregunta (revisión humana:
   UX Researcher + DX Designer), regenerar el estímulo con
   src/diagrams/generate_diagrams.py (o script derivado) para esa pregunta.

6. Iteración 2 del experimento: comparar baseline vs. optimized-v1 (ya persistido,
   docs/03_sistema_diseno.md §1) vs. optimized-v2 (nueva variante) en las
   preguntas candidatas, con el mismo diseño pareado y las mismas pruebas de
   docs/06_plan_analisis.md.

7. Actualizar este documento (08_sintaxis_visual.md):
   por cada regla (R1-R14) cuya predicción medible se pueda evaluar con los
   datos de la iteración correspondiente, cambiar el estado a
   [VALIDADA] / [REFUTADA] / [REVISADA] y anotar la cifra concreta
   (t, p, d de Cohen o accuracy_diff/median_latency_diff) que sustenta el cambio.
```

Este pipeline no requiere cambios de código adicionales: reutiliza `export.py`, `run_analysis.py` y el comando `alternatives` del orquestador ya existentes (`docs/07_arquitectura_agentes.md` §5).

---

## 4. Trazabilidad regla → métrica (resumen)

| Regla | Concepto(s)/pregunta(s) que la ponen a prueba | Métrica de `per_question_breakdown` |
|---|---|---|
| R1 (color por evento) | union, intersection (q01-q02) vs. bayes (q08-q10) | accuracy_diff, median_latency_diff |
| R2 (cierre en intersección) | intersection (q02) | accuracy_diff (debería ser el máximo del banco) |
| R3 (grosor proporcional) | bayes (q09, caso crítico tasa base) | accuracy_diff, patrón de error (requiere dato cualitativo) |
| R5 (notación símbolo) | todas, correlación longitud etiqueta vs. latencia | median_latency_B por pregunta |
| R6 (Venn vs. árbol por concepto) | grupo venn (q01-q04) vs. grupo tree (q05-q10) | accuracy_diff promedio por grupo |
| R9 (sin marginales redundantes) | union/intersection (q01, q02, q04) en iteración 2 | accuracy_diff de variante con marginales vs. sin ellos |
| R10 (jerarquía tipográfica) | pregunta directa sobre valor jerarquizado vs. atómico | median_latency_B |
| R14 (proceso ante sesgo) | cualquier fila con accuracy_diff <= 0 o median_latency_diff >= 0 | dispara `alternatives` |

Las reglas R4, R7, R8, R11, R12, R13 no tienen una fila directa propia en `per_question_breakdown` porque no varían dentro del material actual (aplican de forma universal en `optimized`, o dependen de instrumentación no recolectada aún — eye-tracking, screening de daltonismo). Quedan marcadas explícitamente arriba como dependientes de iteración 2 o de datos cualitativos/eye-tracking futuros, en vez de omitirse silenciosamente.
