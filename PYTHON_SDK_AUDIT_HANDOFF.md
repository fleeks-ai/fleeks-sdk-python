# Python SDK — Audit handoff from the TypeScript SDK team

**Date:** 2026-05-13
**TS SDK release that fixed all of this:** `@fleeks-ai/sdk@0.9.1`
**Backend dependency:** `fleeks-backend-services` ≥ `2026.05.13` (commit `a14ad71`)

We just finished a full end-to-end audit of the TypeScript SDK against the
live API at `https://api.fleeks.ai`. We found ~13 distinct bugs split between
the SDK and backend, coordinated fixes with the backend team, and shipped
`v0.9.1`. **Every one of these issues is also latent in the Python SDK** —
the wire-level contracts are the same. This document is a complete playbook
so you can reproduce the audit, fix the same classes of issues, and ship a
matching Python release.

---

## TL;DR — what the Python SDK almost certainly has wrong

If your Python SDK was authored from the same internal spec as ours, these
bugs are present (in priority order):

| # | Severity | Area | Symptom | Fix |
|---|----------|------|---------|-----|
| 1 | **P0** | `embeds` | All embed calls 404 | Prefix is `/api/v1/sdk/embeds`, **not** `/api/v1/embeds` |
| 2 | **P0** | `files.update` | 422 Unprocessable Entity | Send `path` as **query string**, body must be `{content, encoding}` only |
| 3 | **P0** | `voice` | 404 on getConfig/getSessions/getStats/health | Voice routes live at `/api/v1/voice/*`, **not** under `/sdk/` |
| 4 | **P0** | Trailing slashes | 404 on POST/GET to `workspaces`, `schedules`, `channels`, `automations`, `agents` | Backend mounts these with `redirect_slashes=False`. URL **must** end in `/` for collection routes |
| 5 | **P1** | `workspaces.list` | Empty results / parse error | Backend returns `{workspaces: [...]}`, not `{results: [...]}` |
| 6 | **P1** | `schedules.list` | Empty results / parse error | Backend emits both `{items: [...]}` and `{schedules: [...]}`; accept either |
| 7 | **P1** | `getApiKeyInfo` / `getUsageStats` | 404 | New endpoints: `/sdk/auth/key-info` and `/sdk/usage/stats`. Fall back to `/api/v1/auth/me` and `/api/v1/billing/usage` for older backends |
| 8 | **P2** | Packaging (TS-specific, double-check Python) | `require()` resolution mismatch | We had `dist/index.js` declared but tsup emitted `dist/index.mjs`. Python equivalent: verify your `pyproject.toml` `[tool.setuptools]` / `[tool.poetry]` package paths match real wheel contents |

Everything from #1–#7 is a **wire-level** issue, so it does not matter what
language the client is. The exact mitigations applied to the TS SDK map
1-to-1 to Python.

---

## 1. Reproduce the audit

### 1.1 Get credentials

You will need:

- An active API key on `https://api.fleeks.ai` (format: `fleeks_live_*`)
- Network access to `https://api.fleeks.ai`

The TS team used a live key throughout — the test suite is **idempotent**
(creates and tears down its own workspaces, schedules, embeds, etc.) so it
is safe against a production tenant.

### 1.2 Smoke test surface

Before writing a full suite, exercise each manager once. We learned the most
from a 16-phase live runner. The phases were:

1. `client.getApiKeyInfo()` / `client.getUsageStats()`
2. `workspaces.create` / `list` / `get` / `delete`
3. `files.upload` / `list` / `read` / `update` / `delete`
4. `terminal.execute` (with a created workspace)
5. `containers.getInfo` / `getStats` / `getProcesses`
6. `agents.list` (skip `execute` — it burns quota)
7. `schedules.create` / `list` / `delete` (use trailing-slash form)
8. `embeds.create` / `list` / `get`
9. `channels.list`
10. `automations.list`
11. `previews.*` (sanity-check the new live-preview route ordering)
12. `voice.health` / `getConfig` / `getStats` / `getSessions`
13. `aiKeys.list`
14. `deploy.startBackgroundJob` / `listJobs`
15. Error matrix: 401 with bad key, 404 on unknown resource, 422 on bad body
16. Cleanup

Each phase prints `PASS` / `FAIL` / `SKIP`. Target: **>90% pass before any
fixes, 100% pass after**. The TS suite landed at 45 PASS / 0 FAIL / 3 SKIP.

### 1.3 Sniff the wire

The cheapest diagnostic for "is the SDK wrong or is the backend wrong?" is
to repro the failing call with `curl` (or `httpx`):

```bash
# Will 404 because of redirect_slashes=False
curl -i -X POST https://api.fleeks.ai/api/v1/sdk/schedules \
  -H "Authorization: Bearer $FLEEKS_API_KEY"

# Will 200
curl -i -X POST https://api.fleeks.ai/api/v1/sdk/schedules/ \
  -H "Authorization: Bearer $FLEEKS_API_KEY"
```

Always pull `https://api.fleeks.ai/openapi.json` and cross-check the route
the SDK is hitting against the backend's actual schema. The OpenAPI doc is
the source of truth for request bodies — that is how we discovered #2
(`files.update`).

---

## 2. Issue catalogue — detailed

### Issue 1 — Embeds prefix (P0)

**Symptom:** every embeds call returns 404.

**Root cause:** the embeds router is **mounted under the SDK router**, so
it lives at `/api/v1/sdk/embeds`. We had a constant `EMBED_PREFIX = "api/v1"`
that bypassed `/sdk`.

**Fix:** change the prefix constant to `api/v1/sdk` (or, simpler: do not
override the prefix at all and let it inherit the default SDK prefix).

**TS reference change:**
```ts
// before
const EMBED_PREFIX = 'api/v1';
// after
const EMBED_PREFIX = 'api/v1/sdk';
```

### Issue 2 — `files.update` request shape (P0)

**Symptom:** `files.update(project_id, path=..., content=...)` returns 422
`Unprocessable Entity`.

**Root cause:** the backend schema `FileUpdateRequest` only accepts
`{content: str, encoding: str}`. The `path` is a **query parameter**, not a
body field, on `PUT /sdk/files/{project_id}/content?path=...`.

**Fix:**
```python
# wrong
self._request("PUT", f"/sdk/files/{project_id}/content",
              json={"path": path, "content": content, "encoding": encoding})

# right
self._request("PUT", f"/sdk/files/{project_id}/content",
              params={"path": path},
              json={"content": content, "encoding": encoding})
```

### Issue 3 — Voice routes outside the SDK prefix (P0)

**Symptom:** every voice manager call 404s.

**Root cause:** voice is **not** registered under `/api/v1/sdk/*`. Its routes
are at `/api/v1/voice/health`, `/api/v1/voice/config`, `/api/v1/voice/sessions`,
`/api/v1/voice/stats`.

**Fix:** for these four methods, override the prefix from `api/v1/sdk` to
`api/v1`. In Python this is typically a `prefix=` or `base_path=` kwarg on
your internal request method.

### Issue 4 — Trailing slashes on collection routes (P0)

**Symptom:** `POST https://api.fleeks.ai/api/v1/sdk/schedules` → 404 Not Found,
but `POST .../schedules/` → 200.

**Root cause:** the backend's FastAPI app has `redirect_slashes=False`. The
following routers are affected for their **collection endpoints** (list +
create):
- `/sdk/workspaces/`
- `/sdk/schedules/`
- `/sdk/channels/`
- `/sdk/automations/`
- `/sdk/agents/`
- `/sdk/tasks/`

The backend team did add **empty-path aliases** for these in `a14ad71`, so on
backends ≥ `2026.05.13` you can hit either form. **But** we still recommend
the SDK normalize to trailing-slash — it works on older deployments too.

**Fix (TS approach, port to Python):**
1. In your URL builder, **preserve** a trailing slash if the caller passes
   one. Most URL-joiner libs strip it — yours probably does too.
2. In each affected manager, use the trailing-slash form for `create` and
   `list`:
   ```python
   # workspaces.create
   self._request("POST", "workspaces/", json=payload)  # note the slash
   # workspaces.list
   self._request("GET", "workspaces/")
   ```
   Item-level routes (`workspaces/{id}`, `schedules/{id}/cancel`, etc.) do
   **not** need the trailing slash and should not have one.

If you use `httpx`, watch out: `httpx.URL.join` strips trailing slashes in
some versions. Test it explicitly:
```python
import httpx
print(httpx.URL("https://api.fleeks.ai/api/v1/sdk/").join("schedules/"))
# Must end in '/'
```

### Issue 5 — `workspaces.list` parser (P1)

**Symptom:** `client.workspaces.list()` returns an empty list even though
workspaces exist.

**Root cause:** the backend returns `{"workspaces": [...]}`. The SDK was
looking for `{"results": [...]}` or `{"items": [...]}`.

**Fix:** accept any of `workspaces`, `items`, `results`, falling through in
that order. Same defensive parsing for `total` / `count`.

### Issue 6 — `schedules.list` dual emission (P1)

**Symptom:** `client.schedules.list()` returns empty / parse error.

**Root cause:** the backend emits **both** `items` and `schedules` keys with
identical content. The SDK was checking only `schedules`, or only `items`,
depending on version.

**Fix:** prefer `items` if present, else `schedules`, else `results`.

### Issue 7 — `getApiKeyInfo` / `getUsageStats` endpoints (P1)

**Symptom:** these helpers 404.

**Root cause:** the original SDK called `/api/v1/auth/key-info` and
`/api/v1/usage/stats` which never existed. The backend in `a14ad71` added
first-class `/sdk/auth/key-info` and `/sdk/usage/stats` routes.

**Fix:** call the new SDK endpoints, with a try/except fallback to
`/api/v1/auth/me` and `/api/v1/billing/usage` for backwards compatibility:

```python
def get_api_key_info(self) -> ApiKeyInfo:
    try:
        return self._request("GET", "auth/key-info")  # /api/v1/sdk/auth/key-info
    except NotFoundError:
        # Older backend — fall back
        return self._request("GET", "auth/me", prefix="api/v1")
```

### Issue 8 — Packaging (verify; TS-specific symptom)

We had `package.json` declaring `dist/index.cjs` but tsup was emitting
`dist/index.js`. The package "worked" through bundlers but broke for plain
Node `require()` consumers.

**Python check:** open your built wheel (`pip wheel .` or `python -m build`)
and confirm:
- `RECORD` lists the modules you declared in `pyproject.toml`
- `fleeks/__init__.py` and `fleeks/_version.py` (or wherever your version
  constant lives) are inside the wheel
- The version constant matches `pyproject.toml` exactly
- `py.typed` marker is present if you ship type hints (most consumers want
  this)

---

## 3. How to structure your fix

The TS release that fixed all this was a single commit with the following
shape (you should match this):

1. **Version bump** — patch level (`0.x.y` → `0.x.(y+1)`). Do **not** bump
   minor unless you also add new surface.
2. **CHANGELOG entry** — list every fix with severity. Consumers will read
   it.
3. **Update version constant** (`__version__` in `fleeks/__init__.py` or
   wherever) in **lockstep** with the package metadata. Your User-Agent
   header reads this, and we caught a stale-version regression in our
   integration suite this way.
4. **Run the live audit** until 100% green (skip 2-3 calls that burn quota
   or require pre-existing state).
5. **Tag** `vX.Y.Z`, push to PyPI.
6. **Backend pin**: add a note in your README/CHANGELOG that the new
   `getApiKeyInfo` / `getUsageStats` endpoints require backend
   `2026.05.13+` and fall back transparently otherwise.

---

## 4. Backend dependency

The Python SDK should test against backend commit `a14ad71` or newer
(version `2026.05.13`). That commit landed:

- **P0 fixes:** `api_keys.py` IntegrityError → 500, `users/me` lazy-load
  crash, `integrations/ai-keys` 500
- **P1 fixes:** trailing-slash empty-path aliases for `schedules`,
  `channels`, `automations`, `tasks`
- **New endpoints:** `/sdk/auth/key-info`, `/sdk/usage/stats`
- **Voice:** added `HEAD` and trailing-slash aliases on `voice/health`
- **Previews:** fixed route ordering so `live_preview` is mounted before
  the catch-all

Verify the backend at the target environment is on this version:

```bash
curl -s https://api.fleeks.ai/openapi.json | python -c "import sys, json; print(json.load(sys.stdin)['info']['version'])"
# Expected: 2026.05.13 or later
```

If the backend is older, your audit will reproduce the original failures
and you'll need the backend team to deploy first.

---

## 5. Test harness suggestion

We wrote a single Node script (`live-suite/run-all.mjs`, ~280 lines, 48
calls). For Python, the equivalent is one of:

- A `pytest` module in `tests/live/test_live_suite.py` gated on a
  `FLEEKS_LIVE_API_KEY` env var (skip otherwise). One test function per
  phase, with `pytest-order` or simple ordering by name.
- A standalone script `scripts/live_audit.py` that prints a PASS/FAIL
  table.

We recommend the pytest approach — easier to integrate into CI later. Make
sure each test cleans up after itself (no orphan workspaces) and that a
single failure does not block subsequent phases.

A skeleton:

```python
import os
import pytest
from fleeks import FleeksClient

API_KEY = os.getenv("FLEEKS_LIVE_API_KEY")
BASE_URL = os.getenv("FLEEKS_BASE_URL", "https://api.fleeks.ai")

pytestmark = pytest.mark.skipif(
    not API_KEY, reason="FLEEKS_LIVE_API_KEY not set"
)

@pytest.fixture(scope="module")
def client():
    return FleeksClient(api_key=API_KEY, base_url=BASE_URL,
                        timeout=90.0)  # match TS — container pool warmup needs ≥60s

@pytest.fixture(scope="module")
def workspace(client):
    # 4-attempt retry for 503 "Container pool is warming up"
    last = None
    for _ in range(4):
        try:
            return client.workspaces.create(
                name="audit-py", template="python")
        except Exception as e:
            last = e
    raise last

def test_01_api_key_info(client):
    info = client.get_api_key_info()
    assert info.key_id

def test_05_files_update(client, workspace):
    client.files.upload(workspace.id, path="a.txt", content="hi")
    client.files.update(workspace.id, path="a.txt", content="bye")
    assert client.files.read(workspace.id, "a.txt").content == "bye"

# ... etc through phase 16
```

The `timeout=90.0` and 4-attempt retry on workspace creation are not
optional — without them you will hit the cold container pool exactly once
and the whole run flaps.

---

## 6. Definition of done

- [ ] Python audit script in repo, runs against `https://api.fleeks.ai`
- [ ] All 8 issue classes above verified fixed by the script
- [ ] All existing unit tests still pass (mock-based ones may need URL
      assertion updates — e.g. our `embeds.test.ts` had to change
      `/api/v1/embeds` → `/api/v1/sdk/embeds`)
- [ ] CHANGELOG entry written matching ours in tone/structure
- [ ] Version bumped in both `pyproject.toml` AND `fleeks/_version.py`
- [ ] PyPI release published
- [ ] README mentions backend `2026.05.13+` dependency

---

## 7. Contact

Ping the TS SDK team / @moise_murhi for:
- Access to the live test runner output (we have it saved as
  `sdk-integration-test/live-suite/run-all.log`)
- The full chronological backend issue summary we sent the backend team
- Any clarifications on the wire-level shapes — every one of the issues
  above is reproducible with `curl` against `api.fleeks.ai` and we can
  walk through them live

Good luck. The bugs are mostly small but very tangled with backend
behaviour — going manager-by-manager with curl + OpenAPI in one window and
SDK source in the other is the fastest path through.
