# 03 — Sistema de Diseño de los Estímulos Visuales (Condición B)

**Autor:** DX/Visual Designer
**Fuente de verdad:** `lineamiento_del_proyecto.md` (DTR v1.0), sección 3 (Marco Teórico).
**Script generador:** `src/diagrams/generate_diagrams.py`
**Assets:** `assets/diagrams/{id}_baseline.png` y `assets/diagrams/{id}_optimized.png` (20 archivos, 10 preguntas × 2 variantes).

---

## 1. Por qué dos variantes por diagrama

El DTR (sección 8) plantea una segunda iteración que compara variantes de diseño una vez que se detecten diagramas con alta latencia/confusión (Subagente 4.2 "Diseñador de Alternativas"). Para no bloquear esa iteración futura, cada pregunta se genera en dos versiones desde el día uno:

- **`baseline`**: el diagrama "de manual", sin decisiones de diseño — escala de grises, trazo uniforme delgado, sin cerramiento de color, sin jerarquía tipográfica. Es el control de diseño, no el control experimental (el control experimental de H1 es la Condición A con fórmulas).
- **`optimized`**: aplica las leyes de la Gestalt indicadas en el DTR (semejanza, cierre, buena continuidad) más jerarquía visual y codificación directa de valores.

**El MVP usa únicamente `optimized` como estímulo de Condición B.** `baseline` queda persistido para la iteración futura (comparar `optimized` vs `baseline` vs alternativas del Subagente 4.2), evitando tener que regenerar el material base más adelante.

## 2. Paleta de color

| Rol semántico | Color | Hex | Justificación |
|---|---|---|---|
| Evento A / primera rama | Azul | `#0072B2` | Okabe-Ito |
| Evento B / segunda rama | Vermellón | `#D55E00` | Okabe-Ito |
| Intersección A∩B | Violeta | `#6B3FA0` | Mezcla perceptual de azul+vermellón — ver §4.1 |
| Camino "objetivo" en árbol (rama que se suma, ej. caminos que llegan a B) | Verde azulado | `#009E73` | Okabe-Ito |
| Camino no-objetivo en árbol | Gris neutro | `#B0B0B0` | Bajo contraste deliberado — ver §4.3 |
| Trazos/texto baseline | Negro `#000000` sobre blanco | — | Monocromo puro, sin codificación de color |

Se eligió el subconjunto de **Okabe-Ito** (paleta estándar de facto para deuteranopía/protanopía, la forma más común de daltonismo) en vez de una paleta arbitraria porque:

1. Cada color debe ser **distinguible por al menos dos canales** (matiz + luminancia), no solo matiz — así un participante con daltonopatía rojo-verde igual puede diferenciar A de B.
2. La independencia n=30 no permite excluir participantes por condición visual sin arriesgar la potencia estadística ya al límite (ver `01_product_brief.md` §3); una paleta no accesible introduciría una variable de confusión no controlada en H2.
3. Verificación: azul `#0072B2` y vermellón `#D55E00` tienen contraste de matiz alto incluso en simulación de protanopía/deuteranopía (ambos son parte del conjunto de 8 colores validados de Okabe & Ito, 1974/2008, el estándar citado en accesibilidad de dataviz).

## 3. Tipografía

- Fuente única: sans-serif por defecto de Matplotlib (DejaVu Sans) — sin librerías adicionales, coherente en ambas variantes y con buen soporte de símbolos matemáticos (∩, ¬, subíndices).
- **Jerarquía tipográfica solo en `optimized`**: la región de intersección (el valor cognitivamente más difícil de leer en la fórmula, porque requiere retener tres números) usa el tamaño de fuente más grande y negrita; las etiquetas de "solo A"/"solo B" son un escalón menor. En `baseline` todas las etiquetas comparten el mismo tamaño y peso — no hay pista tipográfica de qué región importa más.
- Notación matemática (`P(A)`, `P(A∩B)`, `¬A`) en vez de palabras: es un **símbolo** peirceano puro (convención arbitraria, no icónico), elegido porque es neutro al idioma y no compite con el resto del texto en español de la plataforma.

## 4. Leyes de la Gestalt aplicadas — trazabilidad con Peirce y con H2

### 4.1 Ley de semejanza (similarity) → color por evento

**Dónde:** cada conjunto/evento (A, B, y las dos ramas del árbol) recibe un color fijo y consistente en todas las 10 preguntas.

**Peirce:** el color-por-evento no es un ícono (no se parece a "A" por semejanza física) ni un índice (no apunta causalmente a A); es un **símbolo**: una convención arbitraria que el participante debe aprender en el momento (azul = A) y luego reutilizar. Es la capa simbólica *dentro* de una imagen que por lo demás es icónica.

**Efecto cognitivo esperado (H2):** agrupamiento perceptual instantáneo — el sistema visual detecta "mismo color = mismo grupo" en la etapa preatencional (antes de razonamiento consciente), reduciendo la carga de memoria de trabajo necesaria para rastrear a qué evento pertenece cada número. En el árbol, esto es lo que permite identificar los dos caminos que terminan en el mismo resultado (ver §4.3) sin tener que leer las etiquetas de texto.

### 4.2 Ley de cierre (closure) → relleno sólido de la intersección

**Dónde:** en los Venn de dos conjuntos, la región A∩B se rellena con opacidad alta (0.9) en `optimized`, más opaca que las regiones "solo A"/"solo B" (0.55). En `baseline` ninguna región tiene relleno de color — solo el contorno negro delimita la forma.

**Peirce:** el diagrama de Venn completo es un **ícono**: representa la relación lógica de conjuntos por semejanza topológica real (superposición espacial = superposición lógica), y el *área* de cada círculo es proporcional a su probabilidad (no es una convención arbitraria — es icónico en sentido fuerte, siguiendo a Peirce cuando dice que los diagramas geométricos son el ejemplo paradigmático de ícono).

**Efecto cognitivo esperado (H2):** la ley de cierre predice que una región delimitada y rellena se percibe como una **unidad figura** (figure/ground) más fuerte que una región delimitada solo por líneas que se cruzan. Esto es exactamente el objetivo de H1: convertir P(A∩B) — que en la fórmula requiere leer tres términos y una resta — en una región que el ojo agrupa como "una cosa" de un solo vistazo, sin operación aritmética consciente.

### 4.3 Ley de buena continuidad (good continuation) → ramas curvas + grosor proporcional

**Dónde:** en los árboles, `optimized` usa curvas de Bézier suaves (en vez de conectores en escuadra) y el **grosor de cada rama es proporcional a su probabilidad** (rama con P=0.99 se dibuja mucho más gruesa que P=0.01). Además, las dos ramas de segundo nivel que llevan al mismo resultado "objetivo" (ej. las dos ramas que terminan en B, necesarias para el teorema de probabilidad total / Bayes) comparten el mismo color de acento (verde azulado), mientras que las ramas hacia el resultado complementario se atenúan a gris. En `baseline`, todas las ramas son líneas rectas en escuadra, negras, de grosor uniforme — sin importar si la probabilidad es 0.01 o 0.99.

**Peirce:** la línea-rama del árbol es un **índice**: no representa "A" por semejanza sino que *apunta* direccionalmente hacia una consecuencia, marcando una secuencia causal/temporal (¿ocurrió A? → entonces ¿ocurrió B?). El grosor variable añade una segunda capa icónica sobre ese índice: el grosor *se parece* a la magnitud (más grueso = más probable), lo cual es un ícono de cantidad superpuesto sobre un índice de dirección.

**Efecto cognitivo esperado (H2):** esta es la aplicación más directa a la pregunta secundaria del DTR ("¿existen sesgos perceptuales que no existen en la fórmula?"). El caso q09 (test de enfermedad, tasa base 1%) es el ejemplo de manual de la falacia de tasa base: la fórmula no comunica visualmente que la rama "Sano" domina; el árbol optimizado sí, porque la rama Sano se dibuja mucho más gruesa que Enfermedad *antes* de que el participante multiplique nada. La hipótesis es que esto **ayuda** a la intuición bayesiana correcta (la rama gruesa "atrae" la atención hacia el hecho de que la mayoría de positivos vienen de ahí) — o alternativamente podría anclar al participante en la rama gruesa y sesgar la lectura. Esta ambigüedad es intencional y es precisamente lo que H2 debe resolver empíricamente; documentarla aquí deja trazabilidad para el análisis post-hoc si q09 muestra un patrón de error atípico.

## 5. Qué NO lleva el estímulo (y por qué)

Por diseño experimental (DTR sección 5: "Condición B ... exclusivamente con los diagramas visuales, sin fórmulas"):

- Ningún diagrama incluye la fórmula LaTeX ni el enunciado de la pregunta.
- No se incluye título ni texto explicativo fuera de las etiquetas de región/rama.
- Los nombres de eventos usan notación matemática (`A`, `¬A`, `P(...)`) en vez de nombres largos, salvo en q09 donde el propio `diagram_spec` ya usa `enfermedad`/`sano`/`pos`/`neg` como claves — se abrevian a "Enf.", "Sano", "Pos.", "Neg." para no saturar el nodo, siguiendo la misma convención simbólica que el resto.

## 6. Ambigüedades encontradas en `diagram_spec` (para registro)

Ninguna bloqueó la generación, pero quedan documentadas para quien mantenga el script:

1. **Convenciones de nombres de clave inconsistentes entre preguntas.** El campo de complemento en el nivel raíz usa `not_a` (con guion bajo) pero el mismo concepto en el segundo nivel usa `nota` (sin guion bajo) — ej. `root.p_not_a` vs `branch_not_a.p_b_given_nota`. De igual modo, `notb` (segundo nivel) no lleva guion bajo mientras que a nivel de nombre de rama sería esperable `not_b`. El generador resuelve esto con un diccionario de traducción de tokens (`TOKEN_LABELS`) que cubre ambas variantes observadas, en vez de asumir un patrón regular único.
2. **Los valores de probabilidad conjunta ya vienen precalculados en el spec para q08/q09/q10** (`p_a_and_b`, `p_enfermedad_and_pos`, etc.) pero **no** para q05/q06/q07. El script no depende de estos campos opcionales: siempre recalcula el producto rama-raíz × rama-condicional para las cuatro hojas, garantizando consistencia entre preguntas y evitando una ruta de código que dependa de la presencia/ausencia de una clave opcional.
3. **`p_union` (q02) y `p_a`/`p_b` marginales (q01, q02, q04)** están presentes en el spec pero son redundantes con `set_a_only + intersection` etc. El script no los usa para dibujar (dibuja directamente `set_a_only`, `set_b_only`, `intersection`, `outside`, que son los únicos valores que matplotlib-venn necesita para el área proporcional); quedan disponibles en el JSON por si una futura versión quiere mostrarlos como anotación adicional.
4. **El campo `note` de cada `diagram_spec`** es una instrucción en prosa dirigida a un diseñador humano/agente (ej. "la rama ¬A puede mostrarse atenuada pero debe estar presente"). El script no lo parsea — se usó como guía de diseño al escribir el código, no como input programático, porque no tiene una gramática estable entre preguntas.

## 7. Reproducibilidad

El script es determinista (sin `random`) e idempotente (recorre las 10 preguntas y sobrescribe los 20 PNG en cada corrida). Dependencias: `matplotlib` (ya en `requirements.txt`) y `matplotlib-venn` (agregada — ver nota de instalación en el propio script/README si falta). Ejecutar:

```
python src/diagrams/generate_diagrams.py
```
