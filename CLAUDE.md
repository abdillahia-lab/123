# BAHB - Autonomous Drone Inspection System

## Project Overview

BAHB (Building And Hardware Baseline) is an enterprise-grade autonomous inspection system for data centers and substations. It runs on DJI Manifold 3 (NVIDIA Orin NX) mounted on DJI Matrice 400 with DJI H30T multi-sensor camera (thermal + wide + zoom + laser rangefinder).

## Architecture

```
H30T Sensors → Preprocessing → Detection Models → VLM Analysis → Output
```

**AI Pipeline:** YOLOv12 (~2ms) + RF-DETR (~15ms) + SAM3 Nano (~8ms) → Qwen2.5-VL-3B-AWQ fusion → Alerts/Reports/3D Map/Telemetry/Cloud

## Project Structure

```
bahb/
├── core/           # Engine, config, types
├── camera/         # DJI H30T interface, frame sync
├── models/         # AI models: yolov12, rf_detr, sam3, qwen_vl, pipeline
├── thermal/        # Thermal analysis + palette
├── alerts/         # Alert manager
├── reporting/      # Report generation + templates
├── streaming/      # WebRTC + recorder
└── main.py         # Entry point
configs/            # production.yaml
scripts/            # download_models.sh, setup_manifold3.sh
```

## Key Commands

```bash
# Install
pip install -r requirements.txt
./scripts/download_models.sh

# Run
python -m bahb.main --config configs/production.yaml
python -m bahb.main --profile substation --output /data/inspections
python -m bahb.main --dev --visualize

# Dev tools
ruff check .                    # Lint
black --check .                 # Format check
mypy bahb/                      # Type check
pytest tests/ -v --tb=short     # Tests
```

## Code Style

- Python 3.10+, line length 100
- Black formatter, Ruff linter (E, F, W, I, UP, B rules)
- Pydantic for config/settings, loguru for logging
- Async where applicable (aiohttp, pytest-asyncio)

## Dependencies

Core: torch, torchvision, opencv-python, ultralytics, transformers, accelerate, pydantic, loguru, click
Optional: onnxruntime-gpu, tensorrt, open3d, aiortc, segment-anything-2

---

## Autoresearch Protocol (Karpathy Loop)

_Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) — autonomous experimentation where an AI agent modifies code, tests, evaluates, keeps or discards, and repeats indefinitely._

### How It Works

The autoresearch loop applies Karpathy's pattern to this codebase: instead of optimizing val_bpb on a training run, we optimize for **test pass rate, inference speed, detection accuracy, and code quality** across the BAHB inspection pipeline.

### The Loop

```
LOOP FOREVER:
1. Read current state — git status, recent changes, test results
2. Propose one atomic change — a single focused improvement
3. Implement the change
4. Verify mechanically — run tests, lint, type check
5. If improved → keep (commit with experiment: prefix)
6. If equal or worse → discard (git reset)
7. Log result to results.tsv
8. NEVER STOP — think harder if stuck, try new angles
```

### Rules

1. **One atomic change per iteration** — never bundle unrelated changes
2. **Read before writing** — understand context fully before modifying
3. **Mechanical verification only** — tests, lints, benchmarks, not vibes
4. **Automatic rollback on failure** — if verification fails, revert completely
5. **Simplicity wins** — equal results + less code = keep the simpler version
6. **Git as memory** — every experiment committed, results.tsv tracks progress
7. **When stuck, think harder** — re-read code, try combining near-misses, try radical changes
8. **NEVER STOP** — the human may be asleep; keep iterating until manually interrupted

### Results Tracking

Log experiments to `results.tsv` (tab-separated):

```
commit	metric	status	description
a1b2c3d	tests:42/42	keep	baseline
b2c3d4e	tests:42/42	keep	optimize frame sync buffer allocation
c3d4e5f	tests:40/42	discard	refactor thermal palette — broke edge case
d4e5f6g	tests:0/42	crash	attempted async pipeline rewrite (import error)
```

### What You CAN Modify

- Any file under `bahb/` — models, pipeline, thermal analysis, alerts, streaming, reporting
- `configs/production.yaml` — configuration tuning
- Test files under `tests/`

### What You CANNOT Modify

- `scripts/` — setup scripts are fixed infrastructure
- `pyproject.toml` — do not add/remove dependencies
- `README.md` — documentation is human-maintained

---

## Mode-Specific Instructions

### Chat Mode

Use for: questions, explanations, architecture discussions, code review.

- Explain detection pipeline stages and model interactions
- Review code for bugs, performance issues, security concerns
- Discuss tradeoffs (accuracy vs speed, model size vs capability)
- Reference specific files and line numbers when explaining

### Cowork Mode

Use for: pair programming, watching the human code, offering suggestions.

- Monitor changes for correctness and consistency with existing patterns
- Flag potential issues: thread safety in streaming, memory leaks in model loading, thermal calibration drift
- Suggest improvements only when directly relevant to what the human is doing
- Run verification (tests, lint) after each significant change

### Code Mode (Autonomous / Autoresearch)

Use for: autonomous improvement loops, bug fixes, feature implementation.

- Follow the autoresearch loop protocol above
- Each iteration: one change → verify → keep or discard
- Prioritize: correctness > simplicity > performance > features
- Target areas: model inference optimization, thermal analysis accuracy, alert reliability, streaming stability
- Always run `ruff check .` and `pytest` before keeping any change
