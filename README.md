# 🚀 OTEL FastAPI

##### A sample FastAPI application instrumented with OpenTelemetry for logs, tracing and metrics collection.

---

### 🧾 Requirements:

- Python 3.14+
- uv
- just (see the top-level `justfile` for available commands)
- marp-cli (Optional, for rendering markdown as slides)
- Docker (docker & docker-compose / Docker Compose v2)

---

### ▶️ Run:

1. Install dependencies using `uv`:

```bash
uv sync
```

2. Start the application using `just`:

```bash
just up
just run-fast-api
```

---

### ⏹️ Stop:

To stop the application and all related services, run:

```bash
just down
```
