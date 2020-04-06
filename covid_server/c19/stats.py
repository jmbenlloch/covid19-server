import numpy as np
from   typing  import Tuple, List
from numpy import sqrt

NN = np.nan
from . types  import Number, Array, Str, Range



def relative_error_ratio(a : float, sigma_a: float, b :float, sigma_b : float) ->float:
    return sqrt((sigma_a / a)**2 + (sigma_b / b)**2)


def mean_and_std(x : np.array, range_ : Tuple[Number, Number])->Tuple[Number, Number]:
    """Computes mean and std for an array within a range: takes into account nans"""

    mu = NN
    std = NN

    if np.count_nonzero(np.isnan(x)) == len(x):  # all elements are nan
        mu  = NN
        std  = NN
    elif np.count_nonzero(np.isnan(x)) > 0:
        mu = np.nanmean(x)
        std = np.nanstd(x)
    else:
        x = np.array(x)
        sel = (x >= range_[0]) & ( x <= range_[1])
        if len(x) > 0:
            y = x[sel]
            if len(y) == 0:
                print(f'warning, empty slice of x = {x} in range = {range_}')
                print(f'returning mean and std of x = {x}')
                y = x
            mu = np.mean(y)
            std = np.std(y)

    return mu, std


def gaussian_experiment(nevt : Number = 1e+3,
                        mean : float  = 100,
                        std  : float  = 10)->np.array:

    Nevt  = int(nevt)
    e  = np.random.normal(mean, std, Nevt)
    return e


def gaussian_experiments(mexperiments : Number   = 1000,
                         nsample      : Number   = 1000,
                         mean         : float    = 1e+4,
                         std          : float    = 100)->List[np.array]:

    return [gaussian_experiment(nsample, mean, std) for i in range(mexperiments)]


def gaussian_experiments_variable_mean_and_std(mexperiments : Number   = 1000,
                                               nsample      : Number   = 100,
                                               mean_range   : Range    =(100, 1000),
                                               std_range    : Range    =(1, 50))->List[np.array]:
    Nevt   = int(mexperiments)
    sample = int(nsample)
    stds   = np.random.uniform(low=std_range[0], high=std_range[1], size=sample)
    means  = np.random.uniform(low=mean_range[0], high=mean_range[1], size=sample)
    exps   = [gaussian_experiment(Nevt, mean, std) for mean in means for std in stds]
    return means, stds, exps



def smear_e(e : np.array, std : float)->np.array:
    return np.array([np.random.normal(x, std) for x in e])
