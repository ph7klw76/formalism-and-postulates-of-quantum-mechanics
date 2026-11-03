# Publish only the verified edition

## Upload kit

The local `outputs/` folder contains the finished `Quantum_Formalism_Lecture.mp4`, `Quantum_Formalism_Narration.wav`, SRT/VTT, `Quantum_Formalism_Thumbnail.png`, `youtube_description.md` and `chapters.txt`. The seven native YouTube quiz entries are in `quizzes/youtube_quizzes.csv` and `.md`. A final media verification report must say PASS before upload; a prepared timeline does not prove a render exists.

The creator selected manual YouTube upload. In Studio upload the actual MP4, add the supplied title/description and thumbnail, upload the English SRT and enter native quizzes where the channel supports them. Review 1080p processing and viewer-context playback. No automatic channel edit or native YouTube quiz installation is claimed by generating the files.

## Confirm and activate the actual URL

```sh
python scripts/activate_video.py --url ACTUAL_YOUTUBE_URL
python scripts/build_pages.py
node scripts/check-site.cjs
node webtools/test-course.cjs
node webtools/test-learning.cjs
```

The activation script requires a verified full render and real YouTube watch/share URL, checks public oEmbed metadata and regenerates native H5P/HTML. Metadata alone is not playback verification. Run all learning paths on desktop and phone; use `H5P_EMBEDDED=true` to test the parent's chapter controls. `H5P_URL` can select an actual public URL after deployment. Do not use a previous course's upload or label a placeholder as this lecture.

The public native package is `h5p/Quantum_Formalism_Interactive.h5p`; the static export is `website/dist/h5p/formalism.html`. Open the native file in a compatible Lumi Desktop version to preview/edit and export HTML. Actual LMS import and grade reporting need a supported authorized host and are not established by static Pages practice.

## GitHub and Pages

Work on `course-production`, commit the explicit publication allowlist and open a PR. The source-check workflow verifies science, measured timing, TypeScript, actual notebook execution, the complete site, responsive layouts and native H5P practice without deploying. The user authorized merge/deployment after relevant checks and the actual final video are verified, subject to repository/environment approvals.

Set **Settings → Pages → Build and deployment → Source → GitHub Actions** once. The main workflow uses built-in Pages/OIDC permissions, never a saved personal token. Full video rendering is not part of Pages builds. Its publication guard rejects a missing confirmed video URL.

After merge, check build, deployment and HTTPS verification for that exact revision. Compare served configuration/HTML/package hashes with source. Run real public embedded streaming/chapter/pause checks, all phone learning paths and the public JupyterLite notebook. The hosted CI video result is explicitly startup-only; real streaming is verified separately on a network that can receive it.

If a required upload or permission is missing, finish and report all independent deliverables without claiming publication. Preserve the last working URL/package for later editions. Roll back through a reviewed configuration/revert commit and normal deployment, not by deleting media or force-pushing history.
