import numpy as np
import time
import multiprocessing
from scipy import linalg
import time
from statsmodels.tools.tools import pinv_extended
import os
from modelisation.regression import linear_models

class Process1(multiprocessing.Process):
    def __init__(self, x_pd, y, indices, nb_threads=None): 
        super(Process1, self).__init__()
        self.x_pd = x_pd
        self.y = y
        self.indices = indices
 
        self.res_process = multiprocessing.Queue()
        self.times_process = multiprocessing.Queue()

        if (nb_threads is None):
            remove_thread_env_var()
        else:
            set_thread_env_var(nb_threads)

        self.times = np.array([])

    def run(self):
        for idx_slice in self.indices:
            res, time_loop = self._f_1_loop(idx_slice)
            self.res_process.put(res)
            self.times_process.put(time_loop)
            
    def _f_1_loop(self, idx_slice):
        s_loop = time.perf_counter()
        x_selection = self.x_pd.values[:, slice(idx_slice)]

        ols_model = linear_models.OLS(self.y, x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit()
        
        lags = tuple(j for j in range(1, idx_slice))
        lags = 0 if not lags else lags
        e_loop = time.perf_counter()
        return (lags, res.info_criteria("aic")), e_loop - s_loop



class Process2(multiprocessing.Process):
    def __init__(self, namespace, indices, nb_threads=None):
        super(Process2, self).__init__()
        self.namespace = namespace
        self.indices = indices
 
        self.res_process = multiprocessing.Queue()
        self.times_process = multiprocessing.Queue()

        if (nb_threads is None):
            remove_thread_env_var()
        else:
            set_thread_env_var(nb_threads)

        self.times = np.array([])

    def run(self):
        for idx_slice in self.indices:
            res, time_loop = self._f_1_loop(idx_slice)
            self.res_process.put(res)
            self.times_process.put(time_loop)
            
    def _f_1_loop(self, idx_slice):
        s_loop = time.perf_counter()
        x_selection = self.namespace.x_pd.values[:, slice(idx_slice)]

        ols_model = linear_models.OLS(self.namespace.y, x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit()
        
        lags = tuple(j for j in range(1, idx_slice))
        lags = 0 if not lags else lags
        e_loop = time.perf_counter()
        return (lags, res.info_criteria("aic")), e_loop - s_loop

class ProcessTest(multiprocessing.Process):
    def __init__(self, indices): 
        super(ProcessTest, self).__init__()
        self.indices = indices
 
        self.times_process = multiprocessing.Queue()

        self.times = np.array([])

    def run(self):
        for i in self.indices:
            s = time.perf_counter()
            useless_function(1)
            e = time.perf_counter()
            self.times_process.put(e - s)


def set_thread_env_var(nb_threads=1):
    os.environ["OMP_NUM_THREADS"] = str(nb_threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(nb_threads)
    os.environ["MKL_NUM_THREADS"] = str(nb_threads)
    os.environ["VECLIB_MAXIMUM_THREADS"] = str(nb_threads)
    os.environ["NUMEXPR_NUM_THREADS"] = str(nb_threads)

def remove_thread_env_var():
    os.environ.pop("OMP_NUM_THREADS", None)
    os.environ.pop("OPENBLAS_NUM_THREADS", None)
    os.environ.pop("MKL_NUM_THREADS", None)
    os.environ.pop("VECLIB_MAXIMUM_THREADS", None)
    os.environ.pop("NUMEXPR_NUM_THREADS", None)

def useless_function(a):
    data = [i * i for i in range(1, 28800000)]
# if __name__ == '__main__':
    
def f_1_loop(x_pd, y, idx_slice):
    s_loop = time.perf_counter()
    x_selection = x_pd.values[:, slice(idx_slice)]

    ols_model = linear_models.OLS(y, x_selection)
    ols_model.df_model = x_selection.shape[1] - 1
    ols_model.k_constant = 1

    res = ols_model.fit()
    
    lags = tuple(j for j in range(1, idx_slice))
    lags = 0 if not lags else lags
    e_loop = time.perf_counter()
    return (lags, res.info_criteria("aic")), e_loop - s_loop

def f_1_loop_bis(idx_slice):
    s_loop = time.perf_counter()
    global x_pd
    global y
    x_selection = x_pd.values[:, slice(idx_slice)]

    ols_model = linear_models.OLS(y, x_selection)
    ols_model.df_model = x_selection.shape[1] - 1
    ols_model.k_constant = 1

    res = ols_model.fit()
    
    lags = tuple(j for j in range(1, idx_slice))
    lags = 0 if not lags else lags
    e_loop = time.perf_counter()
    return (lags, res.info_criteria("aic")), e_loop - s_loop

def f_1_loop_empty(*args):
    s_loop = time.perf_counter()
    # global x_pd
    # global y
    # x_selection = x_pd.values[:, slice(idx_slice)]

    # ols_model = linear_models.OLS(y, x_selection)
    # ols_model.df_model = x_selection.shape[1] - 1
    # ols_model.k_constant = 1

    # res = ols_model.fit()
    
    # lags = tuple(j for j in range(1, idx_slice))
    # lags = 0 if not lags else lags
    e_loop = time.perf_counter()
    return ((0, ), 1), e_loop - s_loop
    return (lags, res.info_criteria("aic")), e_loop - s_loop

def init_worker(shared_x, shared_y):
    global x_pd
    global y
    x_pd = shared_x
    y = shared_y