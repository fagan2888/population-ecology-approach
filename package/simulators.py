import matplotlib.pyplot as plt
import numpy as np


class Simulator(object):
    """Class for simulating the Pugh-Schaffer-Seabright model."""

    def __init__(self, family):
        """
        Create an instance of the Simulator class.

        Parameters
        ----------
        family : families.family
            Instance of the families.Family class defining a family unit.

        """
        self.family = family

    @property
    def initial_condition(self):
        """
        Initial condition for a simulation.

        :getter: Return the current initial condition.
        :setter: Set a new initial condtion.
        :type: numpy.ndarray

        Notes
        -----
        Currently, we assume that the initial condition consists of two
        isolated sub-populations. One group consistst of males and females
        carrying the GA genotype; the other group consists of males and females
        carrying the ga genotype.

        The setter method requires the user to specify a new value for the
        initial share of males carrying the GA genotype in the combined (i.e.,
        mixed) population. The getter method returns an initial condition
        for all eight of endogenous variables.

        """
        return self._initial_condition

    @initial_condition.setter
    def initial_condition(self, mGA):
        """Set a new initial condition."""
        # initial condition for male shares
        mga = 1 - mGA
        initial_male_shares = np.array([mGA, 0.0, 0.0, mga])

        # initial number female children
        fGA0 = self.family.params['c'] * self.family.params['PiAA'] * mGA
        fga0 = self.family.params['c'] * self.family.params['Piaa'] * mga
        initial_number_females = np.array([fGA0, 0.0, 0.0, fga0])

        initial_condition = np.hstack((initial_male_shares,
                                       initial_number_females))

        self._initial_condition = initial_condition

    def _simulate_fixed_trajectory(self, initial_condition, T):
        """Simulates a trajectory of fixed length."""
        # set up the trajectory array
        traj = np.empty((8, T))
        traj[:, 0] = initial_condition

        # run the simulation
        for t in range(1, T):
            current_shares = traj[:, t-1]
            new_shares = self.F(current_shares)
            traj[:, t] = new_shares

        return traj

    def _simulate_variable_trajectory(self, initial_condition, rtol):
        """Simulates a trajectory of variable length."""
        # set up the trajectory array
        traj = initial_condition.reshape((8, 1))

        # initialize delta
        delta = np.ones(8)

        # run the simulation
        while np.any(np.greater(delta, rtol)):
            current_shares = traj[:, -1]
            new_shares = self.F(current_shares)
            delta = np.abs(new_shares - current_shares)

            # update the trajectory
            traj = np.hstack((traj, new_shares[:, np.newaxis]))

        return traj

    def F(self, X):
        """Equation of motion for population allele shares."""
        out = self.family._numeric_system(X[:4], X[4:], **self.family.params)
        return out.ravel()

    def F_jacobian(self, X):
        """Jacobian for equation of motion."""
        jac = self.family._numeric_jacobian(X[:4], X[4:], **self.family.params)
        return jac

    def simulate(self, rtol=None, T=None):
        """
        Simulates the model for either fixed of variable number of time steps.

        Parameters
        ----------
        T : int (default=None)
            The number of time steps to simulate.
        rtol : float (default=None)
            Simulate the model until the relative difference between timesteps
            is sufficiently small.

        Returns
        -------
        traj : numpy.ndarray
            Array representing a simulation of the model.

        """
        if T is not None:
            traj = self._simulate_fixed_trajectory(self.initial_condition, T)
        elif rtol is not None:
            traj = self._simulate_variable_trajectory(self.initial_condition, rtol)
        else:
            raise ValueError("One of 'T' or 'rtol' must be specified.")
        return traj


def plot_isolated_subpopulations_simulation(simulator, mGA0, T=None, rtol=None,
                                            d_A=0.5, d_a=0.5, e_G=0.5, e_g=0.5,
                                            c=1.0, PiaA=7.0, PiAA=5.0, Piaa=3.0, PiAa=2.0):
    """
    Plot a simulated trajectory given an initial condition consistent with the
    isolated sub-populations assumption.

    Parameters
    ----------
    simulator : simulators.Simulator
    mGA0 : float
    T : int (default=None)
        The number of time steps to simulate.
    rtol : float (default=None)
        Simulate the model until the relative difference between timesteps
        is sufficiently small.

    Returns
    -------
    A list containing...

    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))

    tmp_params = {'c': c, 'e_G': e_G, 'e_g': e_g, 'd_A': d_A, 'd_a': d_a,
                  'PiaA': PiaA, 'PiAA': PiAA, 'Piaa': Piaa, 'PiAa': PiAa}
    simulator.family.params = tmp_params
    simulator.initial_condition = mGA0
    tmp_traj = simulator.simulate(rtol, T)

    # male allele trajectories
    m_GA, = axes[0].plot(tmp_traj[0], color='b', linestyle='none', marker='.',
                         markeredgecolor='b', alpha=0.5)
    m_Ga, = axes[0].plot(tmp_traj[1], color='g', linestyle='none', marker='.',
                         markeredgecolor='g', alpha=0.5)
    m_gA, = axes[0].plot(tmp_traj[2], color='r', linestyle='none', marker='.',
                         markeredgecolor='r', alpha=0.5)
    m_ga, = axes[0].plot(tmp_traj[3], color='c', linestyle='none', marker='.',
                         markeredgecolor='c', alpha=0.5)

    # female allele trajectories
    f_GA, = axes[1].plot(tmp_traj[4], color='b', linestyle='none', marker='.',
                         markeredgecolor='b', alpha=0.5, label='$GA$')
    f_Ga, = axes[1].plot(tmp_traj[5], color='g', linestyle='none', marker='.',
                         markeredgecolor='g', alpha=0.5, label='$Ga$')
    f_gA, = axes[1].plot(tmp_traj[6], color='r', linestyle='none', marker='.',
                         markeredgecolor='r', alpha=0.5, label='$gA$')
    f_ga, = axes[1].plot(tmp_traj[7], color='c', linestyle='none', marker='.',
                         markeredgecolor='c', alpha=0.5, label='$ga$')

    # specify plot options
    axes[0].set_xlabel('Time', fontsize=15, family='serif')
    axes[1].set_xlabel('Time', fontsize=15, family='serif')
    axes[0].set_ylim(0, 1)
    axes[0].set_title('Males', family='serif', fontsize=20)
    axes[1].set_title('Females', family='serif', fontsize=20)
    axes[0].grid('on')
    axes[1].grid('on')
    axes[1].legend(loc=0, frameon=False, bbox_to_anchor=(1.25, 1.0))

    fig.suptitle('Number of males and females by genotype', fontsize=25,
                 family='serif')

    return [fig, axes]
