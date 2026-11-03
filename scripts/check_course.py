"""Scientific cross-runtime fixtures and actual desktop notebook execution."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from course.physics import state,observable,expectation,fixtures
def main():
    p=argparse.ArgumentParser();p.add_argument('--skip-notebook',action='store_true');a=p.parse_args()
    rows=[]
    for pop,phi,alpha,beta in [(.6,60,0,0),(.6,60,90,0),(.6,60,90,90),(.2,130,42,77),(1,0,90,0),(0,270,0,0),(.5,0,90,0),(.5,180,90,0)]:
        theta=np.arccos(2*pop-1);phi,alpha,beta=np.deg2rad([phi,alpha,beta]);n=[np.sin(alpha)*np.cos(beta),np.sin(alpha)*np.sin(beta),np.cos(alpha)];e=expectation(state(theta,phi),observable(n));rows.append(dict(population=pop,phase=phi,polar=alpha,azimuth=beta,plus=(1+e)/2,spinOverHbar=e/2))
    out=ROOT/'outputs';out.mkdir(exist_ok=True);(out/'physics-fixtures.json').write_text(json.dumps(rows,indent=2)+'\n')
    executed=None
    if not a.skip_notebook:
        import nbformat
        from nbclient import NotebookClient
        n=nbformat.read(ROOT/'lab/Quantum_Formalism_Lab.ipynb',4)
        NotebookClient(n,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute();nbformat.write(n,out/'Quantum_Formalism_Lab_executed.ipynb');executed=sum(c.cell_type=='code' for c in n.cells)
        assert not any(o.get('output_type')=='error' for c in n.cells if c.cell_type=='code' for o in c.outputs)
    report=dict(status='PASS',physics=fixtures(),javascript_cases=len(rows),desktop_code_cells=executed)
    (out/'course-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
