"""
Defines the model classes.

"""
import numpy as np
from scipy import linalg, optimize

from traits.api import (Array, Bool, cached_property, Dict, Float,
                        HasPrivateTraits, Property, Str)

import wrapped_symbolics


class Model(HasPrivateTraits):
    """Base class representing the model of Pugh-Schaefer-Seabright."""

    _bound_constraints = Property

    _equality_constraints = Property

    _female_alleles_constraint = Property

    _initial_guess = Array

    _male_alleles_constraint = Property

    eigenvalues = Property

    initial_guess = Property(Array)

    isstable = Property(Bool)

    params = Dict(Str, Float)

    solver_kwargs = Dict(Str, Float)

    steady_state = Property(depends_on=['_initial_guess, params'])

    def _get__bound_constraints(self):
        """Population shares must be in [0,1]."""
        eps = 1e-15
        return [(eps, 1 - eps) for i in range(8)]

    def _get__equality_constraints(self):
        """Population shares of male and female alleles must sum to one."""
        return [self._male_alleles_constraint, self._female_alleles_constraint]

    def _get__female_alleles_constraint(self):
        """Female allele population shares must sum to one."""
        cons = lambda X: 1 - np.sum(X[4:])
        return {'type': 'eq', 'fun': cons}

    def _get__male_alleles_constraint(self):
        """Male allele population shares must sum to one."""
        cons = lambda X: 1 - np.sum(X[:4])
        return {'type': 'eq', 'fun': cons}

    def _get_eigenvalues(self):
        """Return the eigenvalues of the Jacobian evaluated at equilibrium."""
        evaluated_jac = self.F_jacobian(self.steady_state.x)
        eigen_vals, eigen_vecs = linalg.eig(evaluated_jac)
        return eigen_vals

    def _get_initial_guess(self):
        """Return initial guess of the equilibrium population shares."""
        return self._initial_guess

    def _get_isstable(self):
        """Return True if the steady state of the model is stable."""
        return np.all(np.less(np.abs(self.eigenvalues), 1.0))

    @cached_property
    def _get_steady_state(self):
        """Compute the steady state for the model."""
        result = optimize.minimize(self._objective,
                                   x0=self._initial_guess,
                                   method='SLSQP',
                                   jac=self._jacobian,
                                   bounds=self._bound_constraints,
                                   constraints=self._equality_constraints,
                                   **self.solver_kwargs)

        return result

    def _set_initial_guess(self, value):
        """Specify the initial guess of the equilibrium population shares."""
        self._initial_guess = value

    def _jacobian(self, X):
        """Jacobian of the objective function."""
        jac = np.sum(self._residual(X) * self._residual_jacobian(X), axis=0)
        return jac

    def _objective(self, X):
        """Objective function used to solve for the model steady state."""
        obj = 0.5 * np.sum(self._residual(X)**2)
        return obj

    def _residual(self, X):
        """Model steady state is a root of this non-linear system."""
        resid = wrapped_symbolics.residual(*X, **self.params)
        return np.array(resid)

    def _residual_jacobian(self, X):
        """Returns the Jacobian of the model residual."""
        jac = wrapped_symbolics.residual_jacobian(*X, **self.params)
        return np.array(jac)

    def F(self, X):
        """Equation of motion for population allele shares."""
        out = wrapped_symbolics.model_system(*X, **self.params)
        return np.array(out).flatten()

    def F_jacobian(self, X):
        """Jacobian for equation of motion."""
        jac = wrapped_symbolics.model_jacobian(*X, **self.params)
        return np.array(jac)

    def simulate(self, initial_condition, T=10):
        """Simulates a run of the model given some initial_condition."""

        # set up the trajectory array
        traj = np.empty((8, T))
        traj[:, 0] = initial_condition

        # run the simulation
        for t in range(1, T):
            traj[:, t] = self.F(traj[:, t-1])

        return traj
