"""Finite-dimensional, pure-state quantum mechanics; ideal projective measurements.

Pauli observables have dimensionless outcomes +/-1. Physical spin is hbar*sigma/2.
Evolution takes K=H/hbar in rad/s and t in s; no hidden SI conversion is required.
"""
import numpy as np

HBAR=6.62607015e-34/(2*np.pi)  # SI definition of h, J s; derived hbar
I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1,-1]).astype(complex)
Z_PLUS=np.array([1,0],complex)
X_PLUS=np.array([1,1],complex)/np.sqrt(2)

def normalize(vector):
    v=np.asarray(vector,dtype=complex)
    if v.ndim!=1 or v.size<2 or not np.all(np.isfinite(v)):raise ValueError('Use a finite state vector with at least two entries.')
    norm=np.linalg.norm(v)
    if norm<1e-14:raise ValueError('The zero vector is not a quantum state.')
    return v/norm

def state(theta=np.arccos(.2),phi=np.pi/3):
    if not np.isfinite(theta) or not np.isfinite(phi) or not 0<=theta<=np.pi:raise ValueError('theta must be in [0, pi]; angles are radians.')
    return np.array([np.cos(theta/2),np.exp(1j*phi)*np.sin(theta/2)])

def hermitian(matrix):
    a=np.asarray(matrix,dtype=complex)
    if a.ndim!=2 or a.shape[0]!=a.shape[1] or not np.all(np.isfinite(a)) or not np.allclose(a,a.conj().T,atol=1e-12,rtol=0):raise ValueError('Use a finite Hermitian matrix.')
    return a

def observable(axis):
    n=np.asarray(axis,dtype=float)
    if n.shape!=(3,) or not np.all(np.isfinite(n)) or np.linalg.norm(n)<1e-14:raise ValueError('Use a nonzero finite 3-vector axis.')
    n=n/np.linalg.norm(n)
    return n[0]*X+n[1]*Y+n[2]*Z

def spectral_projectors(operator):
    """Group numerically equal eigenvalues; do not resolve degeneracies arbitrarily."""
    a=hermitian(operator);values,vectors=np.linalg.eigh(a);groups=[]
    for j,value in enumerate(values):
        p=np.outer(vectors[:,j],vectors[:,j].conj())
        if groups and np.isclose(value,groups[-1][0],atol=1e-10,rtol=0):groups[-1]=(groups[-1][0],groups[-1][1]+p)
        else:groups.append((float(value),p))
    return groups

def probabilities(psi,operator):
    v=normalize(psi);a=hermitian(operator)
    if a.shape!=(v.size,v.size):raise ValueError('State and operator dimensions differ.')
    return [(value,float(np.real(np.vdot(v,p@v)))) for value,p in spectral_projectors(a)]

def expectation(psi,operator):
    v=normalize(psi);a=hermitian(operator)
    if a.shape!=(v.size,v.size):raise ValueError('State and operator dimensions differ.')
    return float(np.real(np.vdot(v,a@v)))

def project(psi,projector):
    """Conditional Lüders update; impossible outcomes have no conditional state."""
    v=normalize(psi);p=hermitian(projector)
    if p.shape!=(v.size,v.size) or not np.allclose(p@p,p,atol=1e-12):raise ValueError('Use a matching orthogonal projector.')
    out=p@v;chance=float(np.real(np.vdot(out,out)))
    return chance,(out/np.sqrt(chance) if chance>1e-14 else None)

def dephase(psi,operator):
    v=normalize(psi);rho=np.outer(v,v.conj())
    return sum(p@rho@p for _,p in spectral_projectors(operator))

def evolve(psi,K,t):
    v=normalize(psi);a=hermitian(K)
    if a.shape!=(v.size,v.size) or not np.isfinite(t):raise ValueError('Use a matching generator and finite time.')
    e,u=np.linalg.eigh(a)
    return u@(np.exp(-1j*e*t)*(u.conj().T@v))

def bloch(psi):
    v=normalize(psi)
    if v.size!=2:raise ValueError('The Bloch vector is for a two-level state.')
    return np.array([expectation(v,a) for a in [X,Y,Z]])

def fixtures():
    v=state();pplus=lambda a:(1+expectation(v,a))/2
    return dict(default_state=[[float(x.real),float(x.imag)] for x in v],bloch=bloch(v).tolist(),
                p_z_plus=pplus(Z),p_x_plus=pplus(X),p_y_plus=pplus(Y),spin_z_over_hbar=expectation(v,Z)/2,
                sequential_z_x_z_plus=float(np.real(np.trace(dephase(Z_PLUS,X)@((I+Z)/2)))),
                pi_rotation_x_plus=(1+expectation(evolve(X_PLUS,Z/2,np.pi),X))/2)
