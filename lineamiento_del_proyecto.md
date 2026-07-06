\*\*DOCUMENTO TÉCNICO DE REQUERIMIENTOS (DTR)\*\*



\*\*Proyecto:\*\* Visualizando lo Incierto: Semiótica y Cognición de la Probabilidad en la Era Algorítmica.

\*\*Versión:\*\* 1.0

\*\*Fecha:\*\* 24 de Mayo de 2024

\*\*Estado:\*\* En desarrollo (Fase de Diseño Experimental)



\---



\### 1. HIPÓTESIS

El proyecto parte de dos hipótesis de trabajo interconectadas:

\*   \*\*H1 (Semántica Visual):\*\* Los diagramas de probabilidad (Venn, Árbol) no son meras ilustraciones, sino traductores semióticos que convierten el lenguaje analítico-abstracto (fórmulas) en un lenguaje topológico-espacial, reduciendo la barrera de entrada cognitiva.

\*   \*\*H2 (Percepción y Carga Cognitiva):\*\* La aplicación de leyes de la Gestalt (específicamente semejanza por color y cerramiento) en las infografías de probabilidad disminuye significativamente la carga cognitiva en comparación con la lectura de fórmulas puras, permitiendo una comprensión más rápida de eventos condicionales (ej. Teorema de Bayes).



\### 2. FORMULACIÓN DE PREGUNTAS

\*   \*\*Pregunta Principal:\*\* ¿Cómo modifica la transición del signo matemático simbólico al signo visual diagramático la comprensión cognitiva de la probabilidad?

\*   \*\*Preguntas Secundarias:\*\*

&#x20;   \*   ¿Qué elementos visuales específicos (color, forma, flechas) actúan como índices o íconos que reemplazan a operadores matemáticos (+, \*, | )?

&#x20;   \*   ¿El diagrama de árbol impone una comprensión temporal/secuencial que la fórmula no explicita?

&#x20;   \*   ¿Existen sesgos perceptuales generados por la imagen que no existen en la fórmula matemática?



\### 3. MARCO TEÓRICO

\*   \*\*Semiótica de Charles Sanders Peirce:\*\* Clasificación de la infografía en Íconos (Venn como semejanza espacial de los conjuntos), Índices (flechas direccionales en árboles) y Símbolos (tipografía de variables $P(A)$).

\*   \*\*Psicología de la Gestalt:\*\* Análisis de la ley de cierre en intersecciones de Venn y la ley de buena continuidad en las ramificaciones de los árboles de probabilidad.

\*   \*\*Teoría de la Imagen Técnica (Vilém Flusser):\*\* Conceptualización de la infografía como una imagen calculada y programada que busca codificar la incertidumbre.

\*   \*\*Teoría de la Carga Cognitiva (John Sweller):\*\* Marco psicológico para medir cuánto esfuerzo mental requiere procesar la fórmula versus la imagen.



\### 4. ÁREAS DEL CONOCIMIENTO A APLICAR

1\.  \*\*Semiótica y Teoría de la Imagen:\*\* Para la deconstrucción analítica del objeto visual.

2\.  \*\*Psicología Cognitiva:\*\* Para entender los procesos de atención, percepción y memoria de trabajo ante estímulos visuales vs. textuales.

3\.  \*\*Estadística y Matemáticas:\*\* Como el "contenido de verdad" subyacente que la imagen intenta transmitir (asegurando que el análisis visual no se separe de la exactitud matemática).

4\.  \*\*Diseño de Información / Data Visualization:\*\* Como disciplina aplicada para proponer mejoras en la sintaxis visual.



\### 5. EXPERIMENTACIÓN

\*\*Diseño:\*\* Cuasi-experimental, cuantitativo y cualitativo. Diseño de medidas repetidas (sujetos se someten a las dos condiciones).

\*   \*\*Muestra:\*\* 30 participantes (mezcla de perfiles humanísticos y técnicos).

\*   \*\*Material:\*\*

&#x20;   \*   \*Grupo de Control (Condición A):\* 10 preguntas de probabilidad presentadas exclusivamente con fórmulas algebraicas.

&#x20;   \*   \*Grupo Experimental (Condición B):\* Mismas 10 preguntas presentadas exclusivamente con los diagramas visuales (Venn/Árbol) sin fórmulas.

\*   \*\*Métricas a capturar:\*\*

&#x20;   \*   \*Tiempo de latencia:\* Segundos transcurridos hasta dar una respuesta.

&#x20;   \*   \*Tasa de exactitud:\* Porcentaje de respuestas correctas.

&#x20;   \*   \*Rastreo Ocular (Eye-tracking):\* Mapas de calor y secuencias de fijación (si se dispone del hardware, o grabación de pantalla con cursor).

&#x20;   \*   \*Protocolo de Pensar en Voz Alta:\* Grabación de audio de los participantes explicando su razonamiento mientras resuelven el problema.



\### 6. TÉCNICAS DE ANÁLISIS DE DATOS

\*   \*\*Estadística Descriptiva:\*\* Cálculo de medias y desviaciones estándar para tiempos de respuesta y tasas de acierto por condición (A vs B).

\*   \*\*Estadística Inferencial (Prueba T de Student para muestras pareadas):\*\* Para determinar si la diferencia de tiempos y exactitud entre ver la fórmula y ver la imagen es estadísticamente significativa ($p < 0.05$).

\*   \*\*Análisis de Sentimiento y Codificación Cualitativa:\*\* Transcripción de los audios "pensar en voz alta", codificando frases que denoten "confusión", "eureka moment", o "identificación de patrones espaciales".

\*   \*\*Análisis de Dispersión Ocular (Gaze Plot Analysis):\*\* Identificación de puntos de fijación ciegos (partes de la imagen que el ojo ignora pero que son matemáticamente relevantes).



\### 7. ANÁLISIS DE RESULTADOS (Esperado)

Se realizará una matriz de correlación cruzando:

\*   \*Elemento Visual\* (Ej: Color de intersección) vs. \*Comprensión del Concepto\* (Ej: Intersección de eventos).

Se espera demostrar que las áreas de superposición cromática actúan como "atajos cognitivos" que eluden la lectura secuencial de la fórmula de intersección $P(A \\cap B) = P(A) \\times P(B|A)$.



\### 8. CONCLUSIÓN (Marco de entrega)

El proyecto culminará en la validación o refutación de las hipótesis, estableciendo unas \*\*"Reglas de Sintaxis Visual para la Probabilidad"\*\*, un documento normativo que dictamine qué elementos visuales son óptimos y cuáles generan ruido cognitivo al representar matemáticas estadísticas.



\---



\### 9. ARQUITECTURA DE AGENTES Y SUBAGENTES DE IA

Para ejecutar este proyecto de manera automatizada y escalable, se diseña la siguiente red de agentes basados en LLMs y modelos de visión:



\#### \*\*AGENTE MAESTRO: "Orquestador de Investigación Visual" (Omni-Agent)\*\*

\*   \*\*Rol:\*\* Distribuye tareas, valida la coherencia entre la teoría semiótica y los datos matemáticos, y redacta el informe final.

\*   \*\*Subagente 1.1 "Router":\*\* Clasifica los inputs del usuario y envía la información al agente especializado correspondiente.



\#### \*\*AGENTE 1: "Semiotista Visual" (Vision-Language Agent)\*\*

\*   \*\*Rol:\*\* Se encarga del Marco Teórico y la deconstrucción de la imagen.

\*   \*\*Subagente 1.1 "Clasificador Peirceano":\*\* Toma un gráfico de entrada y lo escanea etiquetando cada píxel/forma como Ícono, Índice o Símbolo.

\*   \*\*Subagente 1.2 "Analista Gestáltico":\*\* Evalúa la composición (peso visual, contraste, Leyes de Gestalt) y predice teóricamente dónde ocurrirá la primera fijación del ojo humano.



\#### \*\*AGENTE 2: "Diseñador Experimental" (Logic \& Prompt Agent)\*\*

\*   \*\*Rol:\*\* Crea el material para los sujetos de prueba.

\*   \*\*Subagente 2.1 "Traductor Matemático-Visual":\*\* Recibe una fórmula (ej. Teorema de Bayes) y genera el código (ej. Python/Matplotlib o D3.js) para crear su equivalente en diagrama de Venn o Árbol, aislando variables.

\*   \*\*Subagente 2.2 "Generador de Tests A/B":\*\* Redacta las 10 preguntas de probabilidad y sus respectivas distractores, asegurando que midan comprensión y no solo cálculo aritmético.



\#### \*\*AGENTE 3: "Científico de Datos Cognitivos" (Data Processing Agent)\*\*

\*   \*\*Rol:\*\* Procesa los resultados brutos del experimento.

\*   \*\*Subagente 3.1 "Estadístico Inferencial":\*\* Un agente provisto de un intérprete de código (como Advanced Data Analysis). Recibe los CSVs de tiempos y aciertos, ejecuta las Pruebas T de Student y devuelve los valores \*p\* y la significancia.

\*   \*\*Subagente 3.2 "Etiquetador Cualitativo (NLP)":\*\* Procesa las transcripciones de audio de los usuarios, categorizando los fragmentos de texto en "Carga Cognitiva Alta", "Reconocimiento de Patrones", o "Frustración".



\#### \*\*AGENTE 4: "Generador de Insights" (Generative Agent)\*\*

\*   \*\*Rol:\*\* Sintetiza los hallazgos.

\*   \*\*Subagente 4.1 "Creador de Informes":\*\* Toma la salida del Agente 1 (teoría), el Agente 2 (metodología) y el Agente 3 (datos) y redacta el documento técnico final en formato académico (APA).

\*   \*\*Subagente 4.2 "Diseñador de Alternativas":\*\* Si el Agente 3 detecta que un diagrama de Venn generó mucha confusión (alto tiempo de latencia), este subagente propone 3 variaciones de diseño alternativas basadas en principios de la Gestalt para una segunda iteración del experimento.

