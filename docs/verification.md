# Verification and evidence

The original lecture was rendered locally and fully decoded. Its SHA-256, continuous narration hash and measured event-manifest hash are preserved in `reports/video-verification.json`. The local masters are deliberately excluded from GitHub.

| Check | Observed result |
|---|---|
| Scientific model and timing | 16 Python tests; independent spectral/Bloch/ODE/degenerate-projector checks |
| Presentation source | TypeScript check and two measured-manifest Node tests |
| Final local MP4 | 21,600 frames, 720.0 s, 1920×1080, 30 fps, H.264/AAC, limited BT.709/yuv420p |
| Audio | One narration track; −16.22 LUFS, −1.41 dBTP; three master correlations above 0.99999 |
| Captions and chapters | 183 extracted caption cues and seven embedded chapters compared with the canonical timeline |
| Local native-MP4 H5P | All seven pauses, wrong feedback, review/reset/retry and five-statement Summary passed at desktop and phone widths |
| Real uploaded YouTube | Metadata and actual streaming are separate checks; the structured learning reports record actual observed pauses and scores |
| Notebook | Ten code cells executed in desktop Python and browser Pyodide; four plots and a changed-parameter calculation |
| Website | 1440/820/390 px layouts, controls, subpath navigation and seven standalone genuine H5P activities |

The seven measured question times are **01:13, 02:53, 04:30, 06:12, 07:54, 09:39 and 11:27**. Each prediction scene includes 6.5 seconds of reasoning silence. This is a new course with no prior lecture baseline; no historical timing delta is asserted.

`reports/prepublication.json` records the tests available before merge. GitHub feature CI repeats science, notebook, presentation and browser checks. Its YouTube test is explicitly startup-only. Separate real streaming tests exercise chapters, each wrong/review/retry/correct path, fullscreen return and Summary continuation. Public deployment is established only by the exact revision's Pages workflow and subsequent public resource/hash, streaming and notebook checks. Final public evidence is retained locally under `outputs/` and linked in the delivery report.

Perceptual voice preference is not established by ASR. Three comparison samples were produced; the licensed warm Chatterbox profile was reused with topic-specific pronunciation and local alignment. All examples and synthetic samples are original; the formative questions are not a validated survey. Static Pages does not supply LMS authentication or persistent grades.

## Phone fullscreen regression

H5P automatically enters fullscreen when starting its minimal phone player. The browser test now observes that state and waits for both the child player and outer document to finish exiting before entering fullscreen again or using chapter controls. The parent iframe also preserves its normal layout height during fullscreen instead of measuring the fullscreen viewport. `webtools/test-fullscreen.cjs` checks automatic and explicit fullscreen return and actual chapter-button hit testing in CI without claiming advancing streaming. The complete separate phone streaming test checks all seven learning paths after return. This presentation-only correction changes no media, captions, chapters or quiz timestamps.
