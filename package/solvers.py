import numpy as np
from scipy import optimize
import sympy as sym


class Solver(object):
    """Base class for steady state solvers."""

    _modules = [{'ImmutableMatrix': np.array}, "numpy"]

    def __init__(self, family):
        """
        Create an instance of the Solver class.

        Parameters
        ----------
        family : families.family
            Instance of the families.Family class defining a family unit.

        """
        self.family = family

    @property
    def _numeric_jacobian(self):
        """
        Vectorized function for numerically evaluating the Jacobian matrix.

        :getter: Return the current function.
        :type: function

        """
        if self.__numeric_jacobian is None:
            tmp_args = (self.family._symbolic_vars +
                        list(self.family.params.keys()))
            self.__numeric_jacobian = sym.lambdify(tmp_args,
                                                   self._symbolic_jacobian,
                                                   self._modules)
        return self.__numeric_jacobian

    @property
    def _numeric_residual(self):
        """
        Vectorized function for numerically evaluating the model residual.

        :getter: Return the current function.
        :type: function

        """
        if self.__numeric_residual is None:
            tmp_args = (self.family._symbolic_vars +
                        list(self.family.params.keys()))
            self.__numeric_residual = sym.lambdify(tmp_args,
                                                   self._symbolic_residual,
                                                   self._modules)
        return self.__numeric_residual

    @property
    def _symbolic_residual(self):
        """
        Symbolic representation of the model residual.

        :getter: Return the model residual.
        :type: sympy.Matrix

        """
        return self.family._symbolic_system - self.family._symbolic_vars

    @property
    def _symbolic_jacobian(self):
        """
        Symbolic representation of the Jacobian matrix of partial derivatives.

        :getter: Return Jacobian matrix of partial derivatives.
        :type: sympy.Matrix

        """
        return self._symbolic_residual.jacobian(self.family._symbolic_vars)

    @property
    def initial_guess(self):
        """
        Initial guess for the solver.

        :getter: Return the current initial guess.
        :setter: Set a new initial guess.
        :type: numpy.ndarray

        """
        return self._initial_guess

    @initial_guess.setter
    def initial_guess(self, value):
        self._initial_guess = value

    def jacobian(self, X):
        """
        Jacobian matrix of partial derivatives for the system of non-linear
        equations defining the steady state.

        Parameters
        ----------
        X : numpy.ndarray

        Returns
        -------
        jac : numpy.ndarray
            Jacobian matrix of partial derivatives.

        """
        jac = self._numeric_jacobian(X[:4], X[4:], **self.family.params)
        return jac

    def residual(self, X):
        """
        System of non-linear equations defining the model steady state.

        Parameters
        ----------
        X : numpy.ndarray

        Returns
        -------
        residual : numpy.ndarray
            Value of the model residual given current values of endogenous
            variables and parameters.

        """
        residual = self._numeric_system(X[:4], X[4:], **self.family.params)
        return residual.ravel()

    def solve(self, *args, **kwargs):
        raise NotImplementedError


class LeastSquaresSolver(Solver):
    """Solve a system of non-linear equations by minimization."""


class RootFinder(Solver):
    """Solve a system of non-linear equations by root finding."""

    def solve(self, method, with_jacobian=False, **kwargs):
        """
        Solve the system of non-linear equations describing the equilibrium.

        Parameters
        ----------
        method : str
        with_jacobian : boolean (default=False)

        Returns
        -------
        result :

        """
        if with_jacobian:
            kwargs['jac'] = self.jacobian
        else:
            kwargs['jac'] = False

        result = optimize.root(self.residual,
                               x0=self.initial_guess,
                               method=method,
                               **kwargs
                               )
        return result
