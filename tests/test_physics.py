import unittest
import numpy as np
from scipy.linalg import expm
from scipy.integrate import solve_ivp
from course import physics as q

class QuantumTests(unittest.TestCase):
    def test_born_against_independent_bloch_formula(self):
        for theta in np.linspace(0,np.pi,7):
            for phi in np.linspace(-np.pi,np.pi,9):
                psi=q.state(theta,phi)
                r=np.array([np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)])
                for n in [[0,0,1],[1,0,0],[0,1,0],[1,2,-3]]:
                    n=np.array(n)/np.linalg.norm(n);p=q.probabilities(psi,q.observable(n))
                    self.assertAlmostEqual(p[-1][1],(1+r@n)/2,12)
                    self.assertAlmostEqual(sum(chance for _,chance in p),1,12)
    def test_projectors_and_spectral_reconstruction(self):
        a=np.array([[2,1+2j],[1-2j,-1]])
        parts=q.spectral_projectors(a)
        np.testing.assert_allclose(sum(p for _,p in parts),q.I,atol=1e-12)
        np.testing.assert_allclose(sum(e*p for e,p in parts),a,atol=1e-12)
        for _,p in parts:
            np.testing.assert_allclose(p@p,p,atol=1e-12)
            np.testing.assert_allclose(p,p.conj().T,atol=1e-12)
    def test_complex_bra_and_global_vs_relative_phase(self):
        v=q.state()
        for a in [q.X,q.Y,q.Z]:self.assertAlmostEqual(q.expectation(v,a),q.expectation(np.exp(.73j)*v,a),12)
        self.assertAlmostEqual(dict(q.probabilities(q.X_PLUS,q.X))[1.],1)
        self.assertAlmostEqual(dict(q.probabilities(np.array([1,-1])/np.sqrt(2),q.X))[1.],0)
        self.assertAlmostEqual(q.expectation(v,q.Y),np.sqrt(.96)*np.sin(np.pi/3))
    def test_update_repeat_and_impossible_outcome(self):
        chance,post=q.project(q.state(),(q.I+q.X)/2)
        self.assertAlmostEqual(chance,q.fixtures()['p_x_plus'])
        self.assertAlmostEqual(q.project(post,(q.I+q.X)/2)[0],1)
        self.assertAlmostEqual(q.project(post,(q.I+q.Z)/2)[0],.5)
        chance,post=q.project(q.Z_PLUS,(q.I-q.Z)/2)
        self.assertEqual(chance,0);self.assertIsNone(post)
    def test_degenerate_luders_retains_coherence(self):
        a=np.diag([1,1,-1]);v=np.array([1,1j,1])/np.sqrt(3)
        groups=q.spectral_projectors(a);self.assertEqual(len(groups),2)
        pplus=groups[1][1];chance,post=q.project(v,pplus)
        self.assertAlmostEqual(chance,2/3)
        np.testing.assert_allclose(post,np.array([1,1j,0])/np.sqrt(2),atol=1e-12)
    def test_ensemble_expectation_spectral_sum(self):
        for a in [q.X,q.Y,q.Z,(q.X+q.Z)/np.sqrt(2)]:
            self.assertAlmostEqual(q.expectation(q.state(),a),sum(e*p for e,p in q.probabilities(q.state(),a)),12)
        self.assertAlmostEqual(q.expectation(q.state(),q.HBAR*q.Z/2)/q.HBAR,.1)
    def test_unrecorded_measurement_and_order(self):
        rho=q.dephase(q.Z_PLUS,q.X)
        np.testing.assert_allclose(rho,q.I/2,atol=1e-12)
        self.assertAlmostEqual(np.trace(rho).real,1)
        self.assertTrue(np.all(np.linalg.eigvalsh(rho)>=-1e-12))
        # Independently average the two recorded branches.
        branch=0
        for _,p in q.spectral_projectors(q.X):
            chance,post=q.project(q.Z_PLUS,p);branch+=chance*q.project(post,(q.I+q.Z)/2)[0]
        self.assertAlmostEqual(branch,.5)
    def test_zero_commutator_expectation_is_not_compatibility(self):
        c=q.X@q.Z-q.Z@q.X
        self.assertGreater(np.linalg.norm(c),1)
        self.assertAlmostEqual(abs(np.vdot(q.Z_PLUS,c@q.Z_PLUS)),0)
        np.testing.assert_allclose(q.X@q.Y-q.Y@q.X,2j*q.Z,atol=1e-12)
    def test_evolution_against_exponential_and_ode(self):
        k=q.observable([1,2,3])/2;v=q.state();t=2.3
        expected=expm(-1j*k*t)@v
        np.testing.assert_allclose(q.evolve(v,k,t),expected,atol=1e-12)
        errors=[]
        for tol in [1e-4,1e-7,1e-10]:
            numerical=solve_ivp(lambda t,y:-1j*k@y,(0,t),v,rtol=tol,atol=tol*.01,method='DOP853').y[:,-1]
            errors.append(np.linalg.norm(numerical-expected))
        self.assertLess(errors[-1],errors[0]);self.assertLess(errors[-1],1e-9)
    def test_evolution_norm_energy_and_pi_rotation(self):
        for t in np.linspace(0,10,13):
            v=q.evolve(q.state(),q.Z/2,t)
            self.assertAlmostEqual(np.linalg.norm(v),1,12)
            self.assertAlmostEqual(q.expectation(v,q.Z),.2,12)
        self.assertAlmostEqual(q.fixtures()['pi_rotation_x_plus'],0,12)
        np.testing.assert_allclose(q.evolve(q.Z_PLUS,q.Z/2,2),np.exp(-1j)*q.Z_PLUS,atol=1e-12)
    def test_invalid_inputs(self):
        for v in [[0,0],[np.nan,1],[1],[[1,0]]]:
            with self.assertRaises(ValueError):q.normalize(v)
        with self.assertRaises(ValueError):q.observable([0,0,0])
        with self.assertRaises(ValueError):q.state(-1,0)
        with self.assertRaises(ValueError):q.hermitian([[0,1j],[1j,0]])
        with self.assertRaises(ValueError):q.project([1,0],np.diag([1,.5]))

if __name__=='__main__':unittest.main()
