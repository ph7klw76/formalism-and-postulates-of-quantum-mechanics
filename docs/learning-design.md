# Learning design and scientific scope

This is an original 12-minute undergraduate introduction and extended computational investigation, not a replacement for a semester of quantum mechanics. Prerequisites are complex numbers, vectors, inner products and basic eigenvalue algebra. Differential-equation experience supports the optional independent evolution solver.

The design is informed by Emily Marshman and Chandralekha Singh, “Validation and administration of a conceptual survey on the formalism and postulates of quantum mechanics,” *Physical Review Physics Education Research* **15**, 020128 (2019), [DOI](https://doi.org/10.1103/PhysRevPhysEducRes.15.020128), CC BY 4.0. The paper identifies conceptual domains and discusses the QMFPS survey. Our seven formative items are newly authored, are not QMFPS items, and have no claimed psychometric validation. Their scores must not be compared with the paper's survey norms or treated as proof of instructional effectiveness.

| Outcome | Lecture / checkpoint | Laboratory evidence |
|---|---|---|
| Distinguish a state from its coordinates and spin-space dimension | States and bases / Q1 | Compare basis transformations and global versus relative phase |
| Identify Hermitian observables and their spectra, with spin units | Observables and outcomes / Q2 | Spectral decomposition, orthogonality and completeness checks |
| Apply the Born rule and conditional projection update | Measurement / Q3 | Complex inner products; repeated and changed-basis measurements |
| Interpret expectation and finite-sample uncertainty | Ensembles / Q4 | Independent spectral/matrix means and synthetic binomial sampling |
| Predict order effects and distinguish discarded from absent measurements | Compatibility / Q5 | Conditional-branch average and density-matrix dephasing |
| Distinguish global from relative dynamical phase | Evolution / Q6 | Eigenvalue evolution, closed-form rotation and independent ODE convergence |
| Evaluate what observations do and do not determine | Inference / Q7 | Phase identifiability and unfamiliar three-level degenerate measurement |

## Scientific model

`course/physics.py` treats finite-dimensional pure states and ideal projective measurements. It also constructs density matrices for an unrecorded measurement. It does not model realistic detector dynamics, general POVMs, open-system evolution or arbitrary entangled subsystems. Those are extensions, not invalidations of the explicitly stated ideal model.

Pauli matrices have dimensionless outcomes ±1. Physical spin is S_n = ħσ_n/2, so its outcomes are ±ħ/2 and its expectation has angular-momentum units. Code evolution accepts K = H/ħ in rad/s and time in seconds; θ = ωt is dimensionless. The Planck constant uses the exact SI value h = 6.62607015×10⁻³⁴ J s and ħ = h/(2π), with floating-point evaluation.

Projectors for degenerate eigenvalues are grouped before a conditional Lüders update. This is the ideal minimally disturbing projective-measurement assumption; an outcome alone does not imply an arbitrary collapse onto one eigenvector inside a degenerate space.

No detector plot in this course is measured evidence. Synthetic samples are labelled with their random seed, trial count and sampling assumptions. Bloch arrows represent states and are not particle paths or classical spinning balls.

## Scientific references

- Barton Zwiebach, MIT OpenCourseWare 8.05 *Quantum Physics II*, Fall 2013: [spin, bras/kets and operators](https://ocw.mit.edu/courses/8-05-quantum-physics-ii-fall-2013/resources/lecture-notes-2/), [compatibility](https://ocw.mit.edu/courses/8-05-quantum-physics-ii-fall-2013/resources/lecture-notes-5/) and [quantum dynamics](https://ocw.mit.edu/courses/8-05-quantum-physics-ii-fall-2013/resources/lecture-notes-6/). These are linked references; their text, figures and PDFs are not redistributed here.
- [NIST fundamental physical constants](https://physics.nist.gov/cuu/Constants/) for SI conventions and the Planck constant.

All course narration, figures and questions are original educational material. Research-informed alignment is distinct from demonstrated learning gains.
