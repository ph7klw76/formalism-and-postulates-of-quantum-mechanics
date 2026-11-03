# Local scientific video production

The editable pipeline is `Python model + lesson → Manim → measured local narration → Remotion → verified MP4/WAV/SRT/VTT → actual uploaded video → H5P and site`. Do not substitute an estimated speaking rate for measured timing or copy another lecture's quiz timestamps.

## Dependencies and voices

Install `requirements-production.txt` in the scientific/render environment. Manim also needs its documented system Cairo/Pango/FFmpeg dependencies for the target platform. The complete local production was exercised on Windows; Linux users must validate a sample on their own fonts/rendering stack. CI executes science and browser notebooks but does not claim a full media render without the large local inputs.

Create an isolated Python 3.12 `.venv-tts`. Install an appropriate official PyTorch/torchaudio build for the machine (the tested GPU setup used torch/torchaudio 2.6.0 with CUDA 12.4), then `pip install -r requirements-neural.txt`. Install the official spaCy English model required by Kokoro (`en_core_web_sm` 3.8.0 in the tested environment). `requirements-neural-lock.txt` records the complete tested speech environment; hardware-specific wheels may need the appropriate official index.

```sh
python scripts/neural_narration.py fetch
python scripts/neural_narration.py samples
python scripts/neural_narration.py render
```

Run these with the speech-environment interpreter. Set `NEURAL_PYTHON` for `build.py` if it is elsewhere. `fetch` resolves pinned Hugging Face models and preserves notices. Inference and local ASR use an offline network guard. `PHYSICS_ASSET_ROOT` can point to another local project root containing the same pinned `tools/neural-cache` assets, avoiding duplicate model downloads; it is an optional local cache override, not a public URL or credential.

Three comparison WAVs use a topic-specific script covering Dirac, bra/ket, Hermitian, Pauli, Schrödinger and h-bar. The selected warm Chatterbox profile reuses a licensed synthetic Kokoro Heart reference, not a named lecturer. Kokoro-82M is the fallback. Comparison levels are matched. ASR screens intelligibility and alignment, not subjective human naturalness; listen to the supplied files for perceptual comparison.

## Timing and media

The original script has 28 scenes grouped by seven conceptual outcomes. Real chunk durations, local ASR words and canonical captions determine the schedule. The 720-second target is met by adjusting visual holds without speeding up speech or removing the 6.5-second prediction holds. The builder refuses a budget that would require truncating speech or reducing required reasoning time.

`scripts/sync_course.py` creates `course/publication_events.json`, the Remotion copy, captions, quiz JSON/CSV/Markdown, chapters and description. It checks exact canonical text, frame bounds and question-before-reveal ordering. The new course has no previous lecture baseline: draft times must not be reported as measured ones. `outputs/timing-report.json` distinguishes timeline verification from final-render verification.

```sh
python scripts/render_manim.py
python scripts/sync_course.py
pnpm --dir remotion typecheck
pnpm --dir remotion test
pnpm --dir remotion preview
pnpm --dir remotion stills
pnpm --dir remotion render:sample
python scripts/verify_video.py --sample --video outputs/Quantum_Formalism_Sample.mp4
pnpm --dir remotion render:full
python scripts/verify_video.py
```

`build.py` provides `samples`, `audio`, `manim`, `sync`, `lab`, `h5p`, `site`, `sample`, `stills`, `video`, `verify`, `test` and `all` stages. Activate the scientific environment when invoking it. Set `NODE_BINARY` if Node is not on PATH. `PYTHON`, `FFMPEG_BINARY`, `REMOTION_BROWSER_EXECUTABLE` and `REMOTION_CONCURRENCY` configure renderer executables/concurrency. On Windows, the tested headless browser comes from the pinned webtools Playwright install; override its path when different. Set `PHYSICS_ASSET_ROOT` only when sharing existing local models.

The full renderer caches successful video-only chapters by source/CSS/events/lockfile, media hashes and renderer code. Partial chunks are not accepted. Preview, still and full bundles are separate. The original continuous 48 kHz/24-bit mono narration master is encoded once during the final mux; Manim audio is muted. Upsampling from the 24 kHz neural output does not create extra source detail.

Delivery is 1920×1080, 30 fps H.264/AAC with limited-range BT.709/yuv420p. Verification decodes the entire file, checks actual metadata and channel count, extracts/compares embedded captions, checks chapter names/times, measures loudness/true peak and correlates beginning/middle/end audio with the master. Inspect actual frames and equations; numerical checks alone do not establish readability.

## H5P and browser laboratory

Restore H5P assets with `python scripts/fetch_h5p.py`, then `node webtools/h5p-build.cjs --libraries-only`. The published native package preserves exact libraries for later clean rebuilds; the bootstrap uses pinned official upstream core/editor/video sources. Do not silently accept changed Hub archives against a committed checksum.

`python scripts/author_h5p.py` and `node webtools/h5p-build.cjs` generate genuine activities. With no confirmed public video URL, only independent practice is public-ready. The interactive lecture package waits for activation. Native Summary is an explicitly timed final interaction after closing speech, using the runtime's tip strings and feedback arrays. Official H5P.Video 1.6.81 is retained from the tested upstream fix, with revision/checksum evidence.

For local-media QA, after the full MP4 is verified:

```sh
python scripts/author_h5p.py --preview-url http://127.0.0.1:8778/formalism-and-postulates-of-quantum-mechanics/media/lecture.mp4
node webtools/h5p-build.cjs --preview
```

Copy the finished MP4 to `outputs/h5p-preview/media/lecture.mp4`; run `H5P_PREVIEW=true node webtools/test-learning.cjs`, then also with `H5P_PHONE=true`. PowerShell uses `$env:H5P_PREVIEW='true'` instead of the shell prefix. This ignored preview does not change the public/native URL or claim external hosting.

`webtools/test-course.cjs` checks responsive layouts, scientific controls, genuine standalone H5P feedback/retry and real Pyodide execution including a parameter change. `webtools/test-learning.cjs` checks every real timed pause, wrong feedback, review jump, reset/retry, correct score and the final Summary. It supports local MP4, actual YouTube, phone and embedded contexts. Specific native-MP4 aborted-play rejections are recorded separately with bounded counts; other errors and all functional assertions remain failures. YouTube startup-only CI evidence is separate from real streaming evidence.

The notebook embeds `course/physics.py` verbatim with a model hash. Regenerate it with `python scripts/build_lab.py` after changing the canonical model, then execute all worked examples again. Independent transfer prompts intentionally require student work and are not answered merely by running the scaffold.
