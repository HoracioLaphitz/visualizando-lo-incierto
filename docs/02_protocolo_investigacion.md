# Protocolo de Investigación — Visualizando lo Incierto

**Versión:** 1.0
**Fecha:** 2026-07-06
**Fuente de verdad:** `lineamiento_del_proyecto.md` (DTR v1.0), sección 5. Este protocolo operacionaliza el diseño experimental descripto ahí para la fase MVP definida en `docs/01_product_brief.md` (sin eye-tracking ni pensar-en-voz-alta).

---

## 1. Diseño experimental

**Tipo:** Medidas repetidas, contrabalanceado, intra-sujeto.

- Cada participante responde las **mismas 10 preguntas** en las **dos condiciones**:
  - **Condición A (fórmula):** la pregunta se presenta únicamente con notación algebraica (`formula_latex` + `statement_a` en `data/questions.json`), sin ningún diagrama.
  - **Condición B (diagrama):** la misma pregunta se presenta únicamente con el diagrama Venn/árbol (`diagram_type` + `diagram_spec` + `statement_b`), sin ninguna fórmula visible.
- No se repite la misma pregunta en ambas condiciones dentro de la misma sesión con el mismo estímulo — el sujeto ve el bloque A completo (10 preguntas) y luego el bloque B completo (las mismas 10 preguntas, pero solo con diagrama), o viceversa según el orden asignado.

### 1.1 Regla de contrabalanceo (control del efecto de aprendizaje/orden)

Resolver el orden de bloques a partir de la **paridad del ID de participante** (correlativo de inscripción, 1, 2, 3…):

- **ID impar** → orden **A → B** (primero fórmulas, luego diagramas).
- **ID par** → orden **B → A** (primero diagramas, luego fórmulas).

Con n=30, esto produce 15 sujetos en cada orden. El orden asignado se registra como variable de control (`orden_bloque`) en el dataset — ver `docs/02b_operacionalizacion.md`.

Esta regla es determinística y auditable (no depende de un RNG que haya que versionar), y garantiza balance exacto 15/15 sin necesidad de aleatorización adaptativa.

---

## 2. Procedimiento paso a paso de la sesión

1. **Bienvenida y consentimiento informado** (pantalla 1): se muestra el texto de consentimiento (sección 4). El participante debe marcar "Acepto participar" para continuar. Sin aceptación, la sesión no se registra ni continúa.
2. **Datos demográficos** (pantalla 2): formulario mínimo (sección 5). Obligatorio, no tiene branching condicional.
3. **Instrucciones generales** (pantalla 3): explica que habrá dos bloques de 10 preguntas de probabilidad, que se medirá el tiempo de respuesta, que no hay penalización por responder rápido o lento, y que debe responder con la mayor precisión posible sin usar calculadora o notas externas.
4. **Bloque 1** (10 preguntas, condición según regla de contrabalanceo): cada pregunta se presenta en pantalla completa con las 4 opciones. El timer de latencia arranca en el momento de render de la pregunta (ver sección 3) y se detiene al hacer submit. No hay retroalimentación de correcto/incorrecto entre preguntas (para no introducir aprendizaje adicional en el bloque restante).
5. **Pausa obligatoria** (pantalla intermedia): mensaje fijo de descanso (ej. "Tomate 30 segundos antes de continuar") con botón "Continuar" habilitado sin demora forzada — el objetivo es demarcar el cambio de condición, no imponer un tiempo mínimo.
6. **Bloque 2** (las mismas 10 preguntas, condición complementaria a la del Bloque 1).
7. **Cierre**: pantalla de agradecimiento, sin mostrar puntaje ni respuestas correctas (para no contaminar a participantes que compartan la experiencia con otros potenciales sujetos). Se informa que los datos ya fueron guardados de forma anónima.

El flujo es lineal y no permite retroceder a pantallas anteriores una vez enviada una respuesta.

---

## 3. Qué se mide y cómo

### 3.1 Latencia (segundos)

- **Inicio del timer:** timestamp del evento de render de la pregunta (cuando el estímulo — fórmula o diagrama — se vuelve visible en pantalla).
- **Fin del timer:** timestamp del evento de submit (click/tap en una opción de respuesta que confirma la elección).
- **Cálculo:** `latencia_seg = timestamp_submit - timestamp_render`.
- Se registra por pregunta, no solo por bloque, para permitir el análisis pareado pregunta-a-pregunta entre condiciones.

### 3.2 Exactitud

- Se compara el índice de la opción elegida (`selected_index`) contra `correct_index` de `data/questions.json` para el `id` de esa pregunta.
- Se registra como binario (1 = correcto, 0 = incorrecto) por pregunta. La tasa de exactitud por condición es el promedio de esos binarios sobre las 10 preguntas del bloque correspondiente.

---

## 4. Criterios de exclusión de datos

Se excluyen del dataset de análisis (no del registro crudo, que se conserva para auditoría):

1. **Latencia inválida por pregunta:** si `latencia_seg < 2` (respuesta imposible de haber sido leída) o `latencia_seg > 300` (abandono momentáneo/distracción, 5 minutos). La pregunta puntual se marca `excluido_latencia = true` y no entra en los cálculos de latencia media, pero su exactitud puede conservarse si se decide analizar por separado (ver `docs/02b_operacionalizacion.md`).
2. **Sesiones incompletas:** si el participante no completó los dos bloques completos (20 respuestas en total), la sesión entera se excluye del análisis pareado — no se puede correr el t-test pareado con datos faltantes en una de las dos condiciones.
3. **Sesiones de demo/portfolio:** cualquier sesión marcada con el flag de modo demo (ver `docs/01_product_brief.md`, sección 2) se excluye siempre, sin excepción, del dataset de n=30.

Estos criterios se aplican en el pipeline de export (responsabilidad del Data Engineer), no de forma manual, para que el proceso sea reproducible.

---

## 5. Consentimiento informado (texto a mostrar en la app)

> **Consentimiento informado**
>
> Este experimento es parte de un proyecto de investigación sobre semiótica y cognición de la probabilidad. Tu participación es voluntaria y anónima.
>
> - No se recolecta tu nombre, email, ni ningún dato que te identifique personalmente.
> - Se registran únicamente: tus respuestas, los tiempos de respuesta, y los datos demográficos agregados que completes a continuación (rango etario, perfil de formación, familiaridad con probabilidad).
> - Los datos se analizan de forma agregada junto con los de otros participantes; en ningún informe o publicación aparecerán respuestas individuales identificables.
> - Podés abandonar la sesión en cualquier momento cerrando la ventana; los datos de sesiones incompletas no se incluyen en el análisis final.
> - La sesión toma aproximadamente 10-15 minutos.
>
> Al continuar, confirmás que sos mayor de 18 años y que aceptás participar bajo estas condiciones.
>
> [ ] Acepto participar
> [Continuar]

---

## 6. Preguntas demográficas mínimas

Formulario de una sola pantalla, todas obligatorias:

1. **Rango etario:** selección única entre `18-24`, `25-34`, `35-44`, `45-54`, `55+`.
2. **Perfil de formación:** selección única entre `Humanístico` (ej. letras, ciencias sociales, arte), `Técnico` (ej. ingeniería, ciencias exactas, informática), `Mixto` (formación combinada o no encaja claramente en las anteriores).
3. **Familiaridad autopercibida con probabilidad:** escala Likert 1-5, donde 1 = "nunca estudié probabilidad" y 5 = "uso probabilidad/estadística regularmente en mi trabajo o estudio".

Estas tres variables son covariables de control, no variables dependientes — ver `docs/02b_operacionalizacion.md` para su rol en el análisis.
