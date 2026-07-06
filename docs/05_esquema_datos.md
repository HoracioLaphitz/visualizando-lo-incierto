# Esquema de Datos — Visualizando lo Incierto

**Versión:** 1.0
**Fecha:** 2026-07-06
**Relacionado:** `src/data/storage.py`, `src/data/export.py`, `docs/02_protocolo_investigacion.md` (sección 4), `docs/02b_operacionalizacion.md`.

---

## 1. Diagrama del esquema

```
participants                          responses
--------------------------------      -----------------------------------------
participant_id  PK  ──────────┐       response_id      PK
age_range           NOT NULL  │       participant_id   FK ──> participants
education_profile   NOT NULL  └────── question_id      NOT NULL
probability_familiarity NOT NULL      condition        CHECK IN ('A','B')
created_at          NOT NULL          block            CHECK IN (1,2)
finalized_at        NULL hasta        position         NOT NULL
                    completar         answer_index     NOT NULL
                    ambos bloques     correct          BOOLEAN NOT NULL
                                      latency_seconds  REAL CHECK (> 0)
                                      created_at       NOT NULL
                                      UNIQUE(participant_id, question_id, block)
```

La restricción `UNIQUE(participant_id, question_id, block)` impide duplicados por doble submit (doble click / rerun de Streamlit).

## 2. Diccionario de campos

### participants

| Campo | Tipo | Descripción |
|---|---|---|
| `participant_id` | entero, PK autoincremental | ID correlativo; su paridad define el orden de bloques (contrabalanceo) |
| `age_range` | texto | `18-24`, `25-34`, `35-44`, `45-54`, `55+` |
| `education_profile` | texto | `Humanístico`, `Técnico`, `Mixto` |
| `probability_familiarity` | entero | Likert 1–5 |
| `created_at` | timestamp UTC | Momento de inscripción |
| `finalized_at` | timestamp UTC, nullable | NULL hasta completar los dos bloques; se usa para excluir sesiones incompletas |

### responses

| Campo | Tipo | Descripción |
|---|---|---|
| `response_id` | entero, PK | — |
| `participant_id` | entero, FK | Referencia a `participants` |
| `question_id` | texto | ID de la pregunta en `data/questions.json` |
| `condition` | texto | `A` (fórmula) o `B` (diagrama) |
| `block` | entero | `1` o `2` |
| `position` | entero | Posición (base 0) dentro del bloque |
| `answer_index` | entero | Índice de la opción elegida |
| `correct` | booleano | 1 correcto / 0 incorrecto |
| `latency_seconds` | real | Latencia render→submit; debe ser > 0. El filtro 2–300 s se aplica en el export, no acá (el registro crudo se conserva para auditoría) |
| `created_at` | timestamp UTC | Momento del submit |

## 3. El problema de la efimeridad y la solución Supabase

Streamlit Community Cloud tiene **filesystem efímero**: cada reinicio del contenedor (redeploy, inactividad, actualización de la plataforma) **borra el archivo SQLite local**. Con SQLite en producción, perderíamos todos los datos del experimento sin aviso.

**Solución:** doble backend en `src/data/storage.py`:

- **SQLite** (`data/results/responses.db`): desarrollo local y fallback.
- **Supabase** (Postgres gestionado): producción. Los datos viven fuera del contenedor y sobreviven cualquier reinicio.

La selección es automática: si existen `SUPABASE_URL` y `SUPABASE_KEY` (en `st.secrets` o variables de entorno), se usa Supabase; si no, SQLite con un warning en el log. La API pública (`new_participant`, `save_response`, `finalize_session`) es idéntica en ambos backends — `streamlit_app.py` no cambia.

## 4. SQL para crear las tablas en Supabase

Ejecutar una sola vez en el **SQL Editor** del dashboard de Supabase:

```sql
create table participants (
    participant_id bigint generated always as identity primary key,
    age_range text not null,
    education_profile text not null,
    probability_familiarity integer not null,
    created_at timestamptz not null default now(),
    finalized_at timestamptz
);

create table responses (
    response_id bigint generated always as identity primary key,
    participant_id bigint not null references participants (participant_id),
    question_id text not null,
    condition text not null check (condition in ('A', 'B')),
    block integer not null check (block in (1, 2)),
    position integer not null,
    answer_index integer not null,
    correct boolean not null,
    latency_seconds real not null check (latency_seconds > 0),
    created_at timestamptz not null default now(),
    unique (participant_id, question_id, block)
);

-- La app escribe con la service role key (no expuesta al navegador),
-- así que bloqueamos el acceso anónimo por completo:
alter table participants enable row level security;
alter table responses enable row level security;
```

Con RLS habilitado y sin policies, solo la **service role key** puede leer/escribir. No usar la clave `anon` en la app.

## 5. Configurar los secrets en Streamlit Cloud

En el dashboard de Streamlit Cloud: **App → Settings → Secrets**, pegar:

```toml
SUPABASE_URL = "https://<tu-proyecto>.supabase.co"
SUPABASE_KEY = "<service-role-key>"
```

Para desarrollo local contra Supabase (opcional), crear `.streamlit/secrets.toml` con el mismo contenido. **Nunca commitear ese archivo** (agregarlo a `.gitignore`). Sin secrets, la app usa SQLite local automáticamente.

Los valores se obtienen en Supabase: **Project Settings → API** (`Project URL` y `service_role` key).

## 6. Export a CSV

```bash
python -m src.data.export
```

Genera en `data/results/`:

- `export_raw.csv` — todas las respuestas + demografía, sin filtros (auditoría).
- `export_clean.csv` — con criterios de exclusión aplicados (protocolo, sección 4): filas con `latency_seconds` < 2 o > 300, participantes sin `finalized_at`, y participantes con menos de 20 respuestas. El log reporta cuántas filas se excluyeron y por qué.

El export lee el SQLite local. Para datos de producción, descargar las tablas desde el dashboard de Supabase (Table Editor → Export CSV) o apuntar `--db` a una copia local.
