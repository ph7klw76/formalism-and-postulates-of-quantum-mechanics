# Formalism and Postulates of Quantum Mechanics

**From a ket to a prediction:** a 12-minute undergraduate foundation with original formative H5P questions, a model-based simulator and an executable quantum laboratory.

Watch the [lecture](https://youtu.be/s9l7TZSY0-k), use the [interactive course](https://ph7klw76.github.io/formalism-and-postulates-of-quantum-mechanics/), or launch the [Python laboratory](https://ph7klw76.github.io/formalism-and-postulates-of-quantum-mechanics/lab/lab/index.html?path=Quantum_Formalism_Lab.ipynb). Publication is verified separately from preparation: see [verification scopes and results](docs/verification.md) and the workflow runs for the current revision.

## Learn and investigate

- Distinguish spin states, bases and Hilbert-space dimension.
- Use Hermitian observables, spectral projectors, the Born rule and conditional updates.
- Interpret ensemble means, synthetic sampling and uncertainty.
- Predict effects of measurement order and relative dynamical phase.
- Compare independent matrix, spectral, analytic and ODE calculations.
- Investigate an unfamiliar three-level degenerate outcome and defend the ideal model.

The design is informed by [Marshman and Singh, PRPER 15, 020128 (2019)](https://doi.org/10.1103/PhysRevPhysEducRes.15.020128). These newly authored formative questions are **not the QMFPS survey**, have no claimed psychometric validation and must not be compared with its survey norms. See [learning design, scientific scope and references](docs/learning-design.md).

## Source map

| Location | Purpose |
|---|---|
| `course/physics.py` | Canonical finite-dimensional model and physical units |
| `course/lesson.py`, `course/visuals.py` | Original narration, equations and learning sequence |
| `course/assessment.py` | Original questions, misconception feedback and Summary |
| `narration/` | Voice configuration, model pins, canonical captions and measured timing |
| `video/scenes.py` | Seven original, model-derived Manim animations |
| `remotion/` | Editable React/TypeScript production, sample, stills and full-render cache |
| `course/publication_events.json` | One measured frame clock for all publication events |
| `h5p/`, `webtools/` | Real native package, Lumi exporter and browser tests |
| `lab/` | Self-contained desktop/Pyodide notebook with transfer investigation |
| `website/dist/` | Responsive source site with one Watch & Question player |
| `.github/workflows/` | Feature checks and separately gated Pages deployment |

## Build and test

Use Python 3.12, Node 24 and pnpm 11.25.0. Website/science dependencies are isolated from the neural-speech environment.

```sh
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -r requirements-ci.txt
pnpm --dir webtools install --frozen-lockfile
pnpm --dir remotion install --frozen-lockfile
python -m unittest discover -s tests -v
python scripts/check_course.py
pnpm --dir remotion typecheck
pnpm --dir remotion test
python scripts/build_pages.py
node scripts/check-site.cjs
pnpm --dir webtools exec playwright install chromium
node webtools/test-course.cjs
python scripts/serve.py --directory outputs/pages --base-path /formalism-and-postulates-of-quantum-mechanics/
```

Open `http://127.0.0.1:8765/formalism-and-postulates-of-quantum-mechanics/`. Browser tests use their own local ports and stop their servers. First-use JupyterLite downloads Pyodide/packages; choose Python (Pyodide) if prompted and download work to keep it. Static practice is not a gradebook.

[Production instructions](docs/production.md) cover Chatterbox/Kokoro, model caches, Manim, Remotion, synchronization, WAV/MP4 mastering and full decoding. [Publication instructions](docs/publication.md) cover the actual YouTube upload, native H5P rebuild, PR, Pages settings, live verification and rollback.

## Licenses and limits

Original code: [MIT](LICENSE). Original lesson text, questions, visuals and generated thumbnail: [CC BY 4.0](CONTENT_LICENSE.md). Libraries, speech models, fonts, H5P/Lumi and Remotion retain their own licenses. See `docs/tts-licenses/`, `docs/remotion-licenses/` and [H5P notices](h5p/THIRD_PARTY.md).

Remotion 4.0.540 is source-available under conditional terms. Individual eligibility was confirmed for this production; organizations must assess their own eligibility. No paid API or subscription is required by this build. Source books/PDFs, model weights, environments, caches and media masters are excluded from publication. Rebuild commands generate local media; YouTube hosts the public lecture.
