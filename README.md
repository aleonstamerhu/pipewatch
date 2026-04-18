# pipewatch

A lightweight CLI for monitoring and alerting on ETL pipeline health metrics.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

Monitor a pipeline by pointing pipewatch at your metrics endpoint or log source:

```bash
pipewatch monitor --source postgres://user:pass@host/db --pipeline daily_sales
```

Set alert thresholds and get notified when something goes wrong:

```bash
pipewatch watch \
  --pipeline daily_sales \
  --max-latency 300 \
  --min-rows 1000 \
  --alert-email ops@example.com
```

Check pipeline status at a glance:

```bash
pipewatch status --all
```

```
PIPELINE         STATUS     LAST RUN         ROWS      LATENCY
daily_sales      ✓ OK       2 minutes ago    84,201    12s
user_events      ✗ FAILED   47 minutes ago   —         —
inventory_sync   ✓ OK       5 minutes ago    3,482     8s
```

---

## Configuration

pipewatch can be configured via a `pipewatch.yml` file in your project root. Run the following to generate a starter config:

```bash
pipewatch init
```

---

## License

MIT © 2024 [Your Name](https://github.com/yourname)