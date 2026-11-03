"""Self-contained desktop/Pyodide notebook, embedding the canonical model verbatim."""
from pathlib import Path
import sys,hashlib,shutil
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
    cells=[]
    def md(text):cells.append(nb.v4.new_markdown_cell(text))
    def code(text):cells.append(nb.v4.new_code_cell(text))
    md('''# Quantum Formalism Laboratory
**Predict → calculate → test → explain → revise.**

This is an original research-informed investigation, not the QMFPS survey. Prerequisites: complex vectors, inner products and eigenvalues. Model: pure finite-dimensional states, ideal projective measurements, isolated unitary evolution; density matrices describe discarded outcomes. A Bloch arrow is a state representation, not a particle trajectory.

Choose **Python (Pyodide)** if asked and let the kernel initialize. Use **Run → Run All Cells**. First launch needs network access for the runtime/packages. Download your completed notebook; browser storage is not a course gradebook or a promise of permanent storage.

Change the preparation/axis parameters, predict the change, then rerun the cells. Record assumptions and uncertainty. Physical spin is **Sₙ = ħσₙ/2**; Pauli outcomes ±1 are dimensionless.

| Video checkpoint | Investigate |
|---|---|
| Q1 | Why changing basis does not change spin-space dimension |
| Q2 | Spectrum versus a single detector result |
| Q3 | Conditional state update and changed-basis measurement |
| Q4 | Ensemble expectation and finite-sample uncertainty |
| Q5 | Measurement order; discarded versus absent outcomes |
| Q6 | Unitary dynamics, relative phase and independent solvers |
| Q7 | What one basis leaves unidentified; independent transfer |
''')
    code('''import sys
if sys.platform == 'emscripten':
    import piplite
    await piplite.install(['numpy','scipy','matplotlib'])
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from scipy.integrate import solve_ivp
print('Python ready:', sys.platform)''')
    model=(ROOT/'course/physics.py').read_text(encoding='utf-8');code(model)
    md('''## 1 / Prepare a state; choose a question
Predict whether changing relative phase can alter z probabilities. Predict whether it can alter x or y probabilities. Is a common phase physically different? Write your prediction and confidence before running the sweeps.

The two-state basis is |z+⟩, |z−⟩. Our preparation is √p |z+⟩ + exp(iφ)√(1−p)|z−⟩. Angles below are degrees at this input interface and radians inside the model.''')
    code('''p_z_plus = 0.60  # change this in [0,1]
phase_deg = 60.0  # change this; predict before rerunning
axis_polar_deg = 0.0
axis_azimuth_deg = 0.0
assert 0 <= p_z_plus <= 1
theta = np.arccos(2*p_z_plus-1)
phi = np.deg2rad(phase_deg)
alpha,beta = np.deg2rad([axis_polar_deg,axis_azimuth_deg])
axis = [np.sin(alpha)*np.cos(beta),np.sin(alpha)*np.sin(beta),np.cos(alpha)]
psi = state(theta,phi);A = observable(axis)
print('State:',psi)
print('Norm:',np.vdot(psi,psi).real)
print('Pauli outcome probabilities:',probabilities(psi,A))
print('Physical spin expectation / hbar:',expectation(psi,A)/2)
assert abs(np.vdot(psi,psi)-1)<1e-12''')
    code('''eigenvalues, eigenvectors = np.linalg.eigh(A)
spectral_mean = sum(value*chance for value,chance in probabilities(psi,A))
matrix_mean = expectation(psi,A)
np.testing.assert_allclose(spectral_mean,matrix_mean,atol=1e-12)
projectors = spectral_projectors(A)
np.testing.assert_allclose(sum(P for _,P in projectors),I,atol=1e-12)
for _,P in projectors:
    np.testing.assert_allclose(P@P,P,atol=1e-12)
print('Eigenvalues:',eigenvalues)
print('Independent spectral and matrix means:',spectral_mean,matrix_mean)''')
    code('''fig,ax=plt.subplots(1,2,figsize=(10,4))
for i,label in enumerate(['c+','c-']):
    ax[0].arrow(0,0,psi[i].real,psi[i].imag,width=.008,length_includes_head=True,label=label)
ax[0].set(xlabel='Real amplitude',ylabel='Imaginary amplitude',xlim=(-1,1),ylim=(-1,1),title='Complex coefficients');ax[0].grid();ax[0].legend()
chance=[(1+expectation(psi,M))/2 for M in [X,Y,Z]]
ax[1].bar(['x+','y+','z+'],chance);ax[1].set(ylim=(0,1),ylabel='Probability',title='Same state; different observables')
plt.tight_layout();plt.show()''')
    md('''## 2 / Phase information and identifiability
Global phase changes the coordinates without changing probabilities. Relative phase can be measurable. Find two phases with the same z **and x** statistics but different y statistics. Explain what the cosine ambiguity means for state inference.''')
    code('''phases=np.linspace(-np.pi,np.pi,201)
curves={name:np.array([(1+expectation(state(theta,f),M))/2 for f in phases]) for name,M in [('x+',X),('y+',Y),('z+',Z)]}
for name,curve in curves.items():plt.plot(np.rad2deg(phases),curve,label=name)
plt.ylim(0,1);plt.xlabel('Relative phase (degrees)');plt.ylabel('Outcome probability');plt.legend();plt.show()
for M in [X,Y,Z]:np.testing.assert_allclose(expectation(np.exp(.73j)*psi,M),expectation(psi,M),atol=1e-12)
print('Global-phase invariance checked. Change relative phase and compare x/y.')''')
    md('''## 3 / Recorded and discarded measurements
Before executing: condition on x+, then predict z+. Compare that with preparing z+, inserting x and discarding its record, then measuring z. Explain why ignoring the record does not remove the measurement.''')
    code('''first_chance,conditional = project(psi,(I+X)/2)
print('P(first x+):',first_chance)
if conditional is not None:
    print('P(z+ | recorded x+):',project(conditional,(I+Z)/2)[0])
    print('Repeat x+ probability:',project(conditional,(I+X)/2)[0])
rho=dephase(Z_PLUS,X)
density_probability=np.trace(rho@((I+Z)/2)).real
branch_probability=0
for _,P in spectral_projectors(X):
    chance,post=project(Z_PLUS,P)
    branch_probability+=chance*project(post,(I+Z)/2)[0]
np.testing.assert_allclose(branch_probability,density_probability,atol=1e-12)
print('Discarded x outcome; density/branch routes:',density_probability,branch_probability)
commutator=X@Z-Z@X
print('Commutator norm:',np.linalg.norm(commutator),'expectation in z+:',np.vdot(Z_PLUS,commutator@Z_PLUS))
# Explain why the zero expectation above does not imply compatible operators.''')
    md('''## 4 / Dynamics and an independent solver
Use K=H/ħ in rad/s and t in seconds. The physical Hamiltonian is H=ħωσz/2. Predict x and z probabilities at zero, half a period and a full period. A time-independent operator can still have a time-dependent expectation in a nonstationary state.''')
    code('''frequency_hz=1.0e6
omega=2*np.pi*frequency_hz;K=omega*Z/2
times=np.linspace(0,1/frequency_hz,151)
px=np.array([(1+expectation(evolve(X_PLUS,K,t),X))/2 for t in times])
pz=np.array([(1+expectation(evolve(X_PLUS,K,t),Z))/2 for t in times])
np.testing.assert_allclose(px,np.cos(omega*times/2)**2,atol=1e-12)
plt.plot(times*1e6,px,label='x+');plt.plot(times*1e6,pz,label='z+');plt.xlabel('Time (microseconds)');plt.ylabel('Probability');plt.ylim(-.02,1.02);plt.legend();plt.show()
target=0.37/frequency_hz;reference=expm(-1j*K*target)@X_PLUS
for tolerance in [1e-4,1e-7,1e-10]:
    solved=solve_ivp(lambda t,y:-1j*K@y,(0,target),X_PLUS,method='DOP853',rtol=tolerance,atol=tolerance*.01).y[:,-1]
    print('rtol:',tolerance,'state error:',np.linalg.norm(solved-reference))
np.testing.assert_allclose(evolve(X_PLUS,K,target),reference,atol=1e-12)
np.testing.assert_allclose(solved,reference,atol=1e-9)
print('Evolution cross-check complete')''')
    md('''## 5 / Synthetic sampling and uncertainty
The following draws are simulated independent trials, not measured evidence. Change N and the seed. Compare the observed plus-count deviation with its theoretical standard deviation. Does a more precise estimated mean create a new possible single-shot eigenvalue?''')
    code('''N=1000;seed=2026;prob=(1+expectation(psi,Z))/2
rng=np.random.default_rng(seed)
counts=rng.binomial(N,prob,size=200)
mean=N*prob;sd=np.sqrt(N*prob*(1-prob))
plt.hist(counts,bins=18,alpha=.75,label='Synthetic batches');plt.axvline(mean,color='black',label='Theoretical mean');plt.xlabel('Plus count per batch');plt.ylabel('Number of synthetic batches');plt.legend();plt.show()
print('Expected count / SD:',mean,sd)
print('Synthetic count mean:',counts.mean(),'standard error of mean:',sd/np.sqrt(len(counts)))
print('LAB_COMPLETE; all worked examples executed')''')
    md('''## 6 / Independent transfer: a degenerate three-level observable
A new device has three accessible levels. Let |χ⟩ ∝ (1, i, 1) and B=diag(1,1,−1). Assume an **ideal minimally disturbing projective (Lüders) measurement**; another apparatus could implement extra dynamics within a degenerate eigenspace.

1. Find the distinct outcomes and their spectral projectors. Do not select an arbitrary eigenvector for a degenerate outcome.
2. Compute P(+1) and the conditional post-state. What relative coherence survives inside the +1 eigenspace?
3. Compare spectral-sum and matrix expectation values independently.
4. Design an additional observable that could test the surviving phase. State which observations would challenge the model.
5. Submit original code, a normalization/completeness check, an uncertainty statement and a 250-word evidence argument. Revisit your first prediction and confidence.

This is an independent task. The scaffold below runs but does not supply your solution.''')
    code('''chi=normalize([1,1j,1]);B=np.diag([1,1,-1])
print('Three-level observable eigenvalues:',np.linalg.eigvalsh(B))
# TODO: construct the outcome projectors, predict and calculate, then defend the model.
# Do not replace a degenerate projector with one arbitrarily chosen eigenvector.''')
    md('''## Evidence and attribution
These original activities are informed by the conceptual domains in Marshman & Singh, PRPER **15**, 020128 (2019), https://doi.org/10.1103/PhysRevPhysEducRes.15.020128. They are not the validated QMFPS survey and have no claimed psychometric validation. Scientific references and assessment rubric are in the course source. Code MIT; original lesson content CC BY 4.0.''')
    book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (Pyodide)','language':'python','name':'python'},'language_info':{'name':'python','version':'3.12'},'canonical_model_sha256':hashlib.sha256(model.encode()).hexdigest()})
    nb.validate(book)
    for target in [ROOT/'lab/files/Quantum_Formalism_Lab.ipynb',ROOT/'lab/Quantum_Formalism_Lab.ipynb',ROOT/'website/dist/Quantum_Formalism_Lab.ipynb']:nb.write(book,target)
    (ROOT/'lab/jupyter_lite_config.json').write_text('{"LiteBuildConfig":{"contents":["files"],"ignore_sys_prefix":false}}\n')
    (ROOT/'lab/jupyter-lite.json').write_text('{"jupyter-config-data":{"appName":"Quantum Formalism Lab","enableMemoryStorage":true}}\n')
    print('Notebook generated:',len(cells),'cells;',sum(c.cell_type=='code' for c in cells),'code cells')
if __name__=='__main__':main()
