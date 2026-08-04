# Local HTTP contract (developer preview)

`zer0dex serve` binds a simple JSON API to `127.0.0.1:<port>` (default
`18420`). There is no authentication because it is deliberately loopback-only;
do not expose the port through a proxy without adding an appropriate boundary.
All responses are JSON with `Content-Type: application/json`.

## Endpoints

| Method | Path | Request | Success response |
| --- | --- | --- | --- |
| `GET` | `/health` | none | `{"status":"ok","count":N}` |
| `POST` | `/query` | `{"text":"...","limit":5,"min_score":0.3}` | `{"memories":[{"text":"...","score":0.812}]}` |
| `POST` | `/add` | `{"text":"..."}` | `{"count":N,"memories":["..."]}` |

`limit` is optional and must be a positive integer. `min_score` is optional
and must be a JSON number; results must score strictly above it (the default
is `0.3`). Query text shorter than three non-whitespace characters is valid
and returns `{"memories":[]}` without querying the store. `add` requires a
non-empty string.

Malformed JSON, a JSON value other than an object, or an invalid request field
returns HTTP 400 and `{"error":"..."}`. Unknown paths return HTTP 404 with
`{"error":"not found"}`. The preview does not promise stable ordering beyond
the order returned by the local memory backend.

Example:

```bash
curl http://127.0.0.1:18420/health
curl -X POST http://127.0.0.1:18420/query \
  -H 'Content-Type: application/json' \
  -d '{"text":"preferred reply style","limit":5}'
curl -X POST http://127.0.0.1:18420/add \
  -H 'Content-Type: application/json' \
  -d '{"text":"Use concise factual replies."}'
```
