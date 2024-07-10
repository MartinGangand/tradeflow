import os

import numpy as np

from tradeflow.constants import FitMethodAR

current_directory = os.path.abspath(os.path.dirname(__file__))


class Namespace:
    pass


class ResultsAR:
    """
    Results are from statsmodels.
    """

    @staticmethod
    def parameters_order_6(method: str) -> Namespace:
        obj = Namespace()
        match method:
            case FitMethodAR.YULE_WALKER.value:
                obj.constant_parameter = 0
                obj.parameters = [0.20793670441358317, 0.15625334330632215, 0.08328570101676176, 0.10762268507210443, 0.12228963258158163, 0.07896963026086244]
            case FitMethodAR.OLS_WITH_CST.value:
                obj.constant_parameter = 0.06400645100573674
                obj.parameters = [0.2091518029574414, 0.15836060267986327, 0.0834257462768201, 0.10653755478818688, 0.12165411140031872, 0.07969039271249247]

        return obj

    @staticmethod
    def simulated_signs(fit_method: str) -> Namespace:
        obj = Namespace()
        match fit_method:
            case FitMethodAR.YULE_WALKER.value:
                obj.simulation = np.loadtxt(fname=os.path.join(current_directory, 'simulated_signs_yule_walker.csv'), dtype=float, delimiter=",")
            case FitMethodAR.OLS_WITH_CST.value:
                obj.simulation = np.loadtxt(fname=os.path.join(current_directory, 'simulated_signs_ols_with_cst.csv'), dtype=float, delimiter=",")

        return obj
