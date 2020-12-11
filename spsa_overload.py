import numpy as np
import logging
from typing import Optional
from qiskit.aqua.components.optimizers.spsa import SPSA
from qiskit.aqua.components.optimizers.optimizer import Optimizer

logger = logging.getLogger(__name__)

C0 = 2 * np.pi * 0.1

class MySPSA(SPSA, Optimizer):
    def __init__(self,
                 maxiter: int = 1000,
                 save_steps: int = 1,
                 last_avg: int = 1,
                 c0: float = C0,
                 c1: float = 0.1,
                 c2: float = 0.602,
                 c3: float = 0.101,
                 c4: float = 0,
                 skip_calibration: bool = False,
                 max_trials: Optional[int] = None):

        SPSA.__init__(self, maxiter=maxiter,
                 save_steps= save_steps,
                 last_avg=last_avg,
                 c0=C0,
                 c1=c1,
                 c2=c2,
                 c3=c3,
                 c4=c4,
                 skip_calibration=skip_calibration,
                 max_trials=max_trials)
        
    def optimize(self,
             num_vars, objective_function,
             gradient_function=None,
             variable_bounds=None,
             initial_point=None):

        Optimizer.optimize(self, num_vars, objective_function, gradient_function,
                         variable_bounds, initial_point)
        
        if not isinstance(initial_point, np.ndarray):
            initial_point = np.asarray(initial_point)

        logger.debug('Parameters: %s', self._parameters)
        if not self._skip_calibration:
            # at least one calibration, at most 25 calibrations
            num_steps_calibration = min(25, max(1, self._maxiter // 5))
            self._calibration(objective_function, initial_point, num_steps_calibration)
        else:
            logger.debug('Skipping calibration, parameters used as provided.')

        opt, sol, _, _, theta_plus, theta_minus = self._optimization(objective_function,
                                                  initial_point,
                                                  maxiter=self._maxiter,
                                                  **self._options)
        
        theta = []
        for i, tp in enumerate(theta_plus):
            theta.append((tp + theta_minus[i])/2)

        return sol, opt, theta
