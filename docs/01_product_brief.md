# Product Brief — Visualizando lo Incierto

**Versión:** 1.0
**Fecha:** 2026-07-06
**Fuente de verdad:** `lineamiento_del_proyecto.md` (DTR v1.0). Este brief traduce el DTR a decisiones de producto; no lo reemplaza. Ante conflicto, gana el DTR.

---

## 1. Objetivo de investigación / negocio

El DTR plantea dos hipótesis (H1 semántica visual, H2 percepción y carga cognitiva) que son, en esencia, no falsables sin un instrumento de medición. El producto **es** el instrumento: sin plataforma no hay datos, sin datos no hay validación de H1/H2, sin validación no hay documento normativo.

Por eso el objetivo de producto se define en dos entregables concretos, no en una intención vaga de "investigar":

1. **Plataforma de experimento pública** (Streamlit) que administra Condición A (fórmulas) y Condición B (diagramas) a 30 participantes, captura latencia y exactitud, y sobrevive como pieza de portfolio del investigador (enlazada desde Vercel).
2. **"Reglas de Sintaxis Visual para la Probabilidad"** — documento normativo (sección 8 del DTR) que traduce los resultados estadísticos en guía de diseño: qué combinaciones de color/forma en Venn y árbol reducen carga cognitiva y cuáles la aumentan.

Sin (1) no existe (2). El roadmap de este brief prioriza (1) como bloqueante de todo lo demás.

## 2. Usuarios / stakeholders

| Rol | Necesidad | No-objetivo |
|---|---|---|
| **Participante del experimento** (30, perfiles humanísticos + técnicos) | Interfaz que no requiera instrucción previa, sesión completable en una sentada, sin fricción de login | No es un usuario recurrente; una sola sesión, un solo propósito |
| **Investigador (dueño del proyecto)** | Panel/export de datos crudos (CSV) para correr t-test pareado; control de qué preguntas se muestran en qué orden | No necesita panel de administración multiusuario ni roles |
| **Visitante del portfolio (Vercel)** | Entender en 30 segundos qué es el experimento y, opcionalmente, poder correrlo/verlo en modo demo | No es sujeto experimental — sus interacciones no deben contaminar la muestra de n=30 |

Implicación de diseño: la plataforma necesita un **modo demo/portfolio separado del modo experimento real** (o al menos un flag que excluya sesiones de visitantes del dataset de análisis). Esto no está en el DTR y es una decisión de producto que hay que congelar antes de escribir código.

## 3. Métricas de éxito

**Investigación (obligatorias, del DTR sección 5):**
- n = 30 sesiones completas (medidas repetidas, ambas condiciones por sujeto).
- Latencia (segundos) y exactitud (%) capturadas por pregunta, por condición, sin datos faltantes que invaliden el pareo.
- Dataset exportable en formato apto para t-test pareado (CSV limpio, sin intervención manual).

**Producto (condición de éxito de despliegue):**
- Plataforma desplegada en Streamlit Community Cloud, URL estable.
- Enlazada desde el portfolio en Vercel con contexto (qué es, por qué, cómo correrlo).
- Repo público en GitHub (`HoracioLaphitz`) con README que explique el diseño experimental sin exponer datos de participantes.

**Métrica de fracaso explícita:** si al cierre de la ventana de recolección hay menos de 30 sesiones completas pareadas, el análisis inferencial (t-test) pierde potencia estadística y el documento normativo se degrada a "observaciones preliminares". Definir de antemano el mínimo aceptable (ej. n≥20) para no descubrirlo tarde.

## 4. Alcance MVP vs. futuro

**MVP (lo que bloquea la primera corrida del experimento):**
- Plataforma Streamlit con flujo secuencial: consentimiento → 10 preguntas Condición A → 10 preguntas Condición B (o contrabalanceado) → fin.
- Generación/embebido de los diagramas Venn/árbol para las 10 preguntas (estáticos alcanza para MVP; no requiere generación dinámica).
- Captura de latencia (timestamp por pregunta) y exactitud (respuesta vs. clave) a un almacenamiento persistente (CSV/SQLite/Supabase — decisión de Data Engineer, no de este brief).
- Script de análisis estadístico (descriptivos + t-test pareado) reproducible sobre el export.
- Despliegue público + enlace desde portfolio.

**Explícitamente fuera del MVP (futuro, DTR secciones 5 y 9):**
- Eye-tracking / mapas de calor (requiere hardware o grabación de pantalla — infraestructura no trivial).
- Protocolo "pensar en voz alta" con grabación de audio y codificación cualitativa NLP.
- Red de agentes IA (Semiotista Visual, Diseñador Experimental, Científico de Datos Cognitivos, Generador de Insights) — automatiza el pipeline de investigación, no es necesaria para producir los primeros 30 datos.
- Segunda iteración de diseños alternativos (Subagente 4.2) — depende de tener resultados de la primera iteración.

Regla de corte: si una funcionalidad no es necesaria para llegar a n=30 con datos limpios, no entra al MVP.

## 5. Roadmap por roles (con handoffs)

1. **UX Researcher** → valida las 10 preguntas de probabilidad (Bayes, condicional, intersección/unión) y sus distractores; asegura que midan comprensión y no solo cálculo aritmético (DTR 2.2 subagente "Generador de Tests A/B"). *Handoff:* entrega banco de preguntas + claves + rúbrica de dificultad balanceada entre condiciones.
2. **DX Designer** → aplica semiótica peirceana + Gestalt para producir los diagramas Venn/árbol de Condición B (color = semejanza, cerramiento en intersecciones, continuidad en ramas). *Handoff:* entrega assets (SVG/PNG) + especificación de qué principio de diseño encarna cada elemento, para trazabilidad con H2.
3. **Frontend (Streamlit)** → construye el flujo de sesión, randomización/contrabalanceo de orden, timers de latencia, captura de respuesta. *Handoff:* entrega app funcional + esquema de datos que emite (columnas, tipos) para el Data Engineer.
4. **Data Engineer** → define almacenamiento persistente, pipeline de export limpio, y separa sesiones de portfolio/demo de sesiones experimentales reales. *Handoff:* entrega dataset validado (sin duplicados, sin sesiones incompletas) al Data Scientist.
5. **Data Scientist** → corre estadística descriptiva + t-test pareado; determina significancia (p<0.05) para H1/H2. *Handoff:* entrega resultados cuantitativos + su interpretación estadística (no de diseño) al síntesis.
6. **AI Architect** → (post-MVP) diseña la red de agentes de la sección 9 del DTR para escalar el análisis cualitativo y las iteraciones futuras de diseño; no bloquea la entrega del MVP.
7. **Síntesis (Investigador)** → integra hallazgos de diseño (paso 2) y estadística (paso 5) en "Reglas de Sintaxis Visual para la Probabilidad".

Cada paso depende del anterior; no hay paralelización real antes del paso 4 (el Frontend no puede construir sin preguntas ni diagramas).

## 6. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Reclutamiento insuficiente** (no se llega a n=30) | Pierde potencia estadística, el t-test pareado se vuelve poco confiable | Definir n mínimo aceptable (ej. 20) antes de empezar; sobre-reclutar (35-40 invitados) previendo abandono |
| **Sesgo de muestra** (mezcla desbalanceada de perfiles humanísticos/técnicos) | Los técnicos podrían tener ventaja preexistente leyendo fórmulas, confundiendo la variable independiente | Registrar perfil autodeclarado como covariable; reportar resultados también segmentados por perfil |
| **Efecto de orden / aprendizaje** (medidas repetidas: ver Condición A primero enseña el concepto para B) | Contamina la comparación A vs B | Contrabalancear el orden (mitad de participantes empieza por A, mitad por B) — esto debe ser un requisito explícito del Frontend, no un detalle opcional |
| **Privacidad de datos de participantes** | Dataset público en GitHub podría exponer datos identificables si se sube sin anonimizar | Nunca commitear CSVs crudos con PII; anonimizar con ID de sesión antes de cualquier análisis versionado; excluir `data/raw/` del repo vía `.gitignore` |
| **Confusión entre sesiones de portfolio y sesiones experimentales** | Visitantes del portfolio jugando con la demo contaminan el n=30 | Flag de modo demo separado (ver sección 2) desde el primer commit del Frontend, no como parche posterior |
| **Dependencia de infraestructura gratuita** (Streamlit Community Cloud) | Límites de recursos o caídas durante la ventana de recolección | Tener export de datos incremental (no solo al final de sesión) para no perder datos si el servicio cae a mitad de la ventana |
