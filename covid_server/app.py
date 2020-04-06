import json
import numpy as np

import c19.basic_models as cbm
from scipy.integrate import odeint
from scipy.interpolate import interp1d
from c19.types import SIR, SEIR


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    data = json.loads(event['body'])
    #data = event

    model = data['model']

    result = ''

    if model == 'SIR':
        result = wrapper_sir(data['params'])
    if model == 'SEIR':
        result = wrapper_seir(data['params'])
    if model == 'beds':
        result = wrapper_beds(data['params'])


    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
            },
        'body': result
    }


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def wrapper_sir(params):
    R0   = float(params['R0'  ])
    T    = float(params['T'   ])
    Tm   = int  (params['Tm'  ])
    days = int  (params['days'])
    Q    = float(params['Q'   ])
    N    = int  (params['N'  ])
    absolute = bool(params['absolute'])

    sir_result = compute_basic_sir_model(R0, T, Tm, Q, days, N, absolute)

    t = sir_result.t.tolist()
    S = sir_result.S.tolist()
    I = sir_result.I.tolist()
    R = sir_result.R.tolist()

    result = json.dumps({'t':  t,
                         'S' : S,
                         'I' : I,
                         'R' : R}, cls=NpEncoder)

    return result


def wrapper_seir(params):
    R0   = float(params['R0'  ])
    T    = float(params['T'   ])
    Ti = float(params['Ti' ])
    Tm   = int  (params['Tm'  ])
    days = int  (params['days'])
    Q    = float(params['Q'   ])
    N    = int  (params['N'  ])
    absolute = bool(params['absolute'])

    seir_result = compute_basic_seir_model(R0, T, Ti, Tm, Q, days, N, absolute)

    t = seir_result.t.tolist()
    S = seir_result.S.tolist()
    E = seir_result.E.tolist()
    I = seir_result.I.tolist()
    R = seir_result.R.tolist()

    result = json.dumps({'t':  t,
                         'S' : S,
                         'E' : E,
                         'I' : I,
                         'R' : R}, cls=NpEncoder)

    return result


def wrapper_beds(params):
    R0 = float(params['R0'])
    T  = float(params['T' ])
    Ti = float(params['Ti' ])
    days = int(params['days'])
    Tm = int(params['Tm'])
    M = float(params['M'])

    seir_result = compute_beds_seir_model(R0, T, Ti, days, tm=Tm, mitigation=M)
    IC, RC = get_I_and_R_CAA(poblacion[1], seir_result.N, seir_result.I, seir_result.R, norm=False)
    Iur06 = uci_cases(IC, f_uci = 0.05)
    ub = uci_beds(poblacion[1])

    t = seir_result.t.tolist()
    results = {'t' : t}

    for i, comunidad in enumerate(poblacion[0]):
        results[comunidad] = {'capacity' : ub[i],
                              'camas' : Iur06[i].tolist()}

    result = json.dumps(results, cls=NpEncoder)

    return result


def compute_basic_sir_model(R0, T, tm, Q, days, N, absolute):
    i0 = 1e-5
    s0 = 1 - i0
    r0 = 0
    y0 = (s0, i0, r0)

    t_start = 0.0
    t_end   = days
    t_inc   = 1
    t_range = np.arange(t_start, t_end+t_inc, t_inc)

    Gamma = 1/T
    Beta  = Gamma * R0
    #ts =[(0, tm)]
    ts = [(0, tm), (tm, days)]
    ms = [1, 1 - Q/100]

    M = cbm.mitigation_function(t_range, ts, ms)
    ret = odeint(cbm.sir_deriv, y0, t_range, args=(M, Beta, Gamma))
    S, I, R = ret.T

    if absolute:
        S = S * N
        I = I * N
        R = R * N

    sir = SIR(N = N, S=S, I=I,  R=R,
              beta=Beta, R0=R0, gamma=Gamma, t=t_range)

    return sir


def compute_basic_seir_model(R0, T, Ti, Tm, Q, days, N, absolute):
    # Initial number of infected and recovered individuals, I0 and R0.
    i0 = 1e-4
    e0 = 1e-4
    s0 = 1 - i0 - e0
    y0 = (s0, e0, i0)

    t_start = 0.0
    t_end   = days
    t_inc   = 1
    t_range = np.arange(t_start, t_end+t_inc, t_inc)

    Gamma = 1./T
    Sigma = 1./Ti
    Beta  = Gamma * R0
    ts = [(0, Tm), (Tm, days)]
    ms = [1, 1 - Q/100]

    M = cbm.mitigation_function(t_range, ts, ms)
    ret = odeint(cbm.seir_deriv_time, y0, t_range, args=(M, Beta, Gamma, Sigma))
    S, E, I = ret.T
    R = 1 - S - E - I

    if absolute:
        S = S * N
        E = E * N
        I = I * N
        R = R * N

    seir = SEIR(N=N, S=S, I=I, E=E, R=R,
                beta=Beta, R0=R0, gamma=Gamma, sigma = Sigma, t= t_range)

    return seir


poblacion = (
    ['Andalucía', 'Aragón', 'Asturias', 'Baleares', 'Canarias', 'Cantabria', 'Cas-León', 'Cas-Mancha', 'Cataluña', 'Valencia', 'Extremadura', 'Galicia', 'Madrid', 'Murcia', 'Navarra', 'Euskadi', 'Rioja', 'Ceuta', 'Melilla'],
    [8414240,1319291,1022800,1149460,2153389,581078,2399548,2032863,7675217,5003769,1067710,2699499,6663394,1493898,654214,2207776,316798,84777,86487]
)


def compute_beds_seir_model(R0, T, Ti, days, tm, mitigation, n=1000):
    # Initial number of infected and recovered individuals, I0 and R0.
    t_start = 0.0
    t_end   = days
    t_inc   = 1

    t_range = np.arange(t_start, t_end+t_inc, t_inc)
    Gamma   = 1. / T
    Sigma   = 1. / Ti
    Beta    = Gamma * R0
    I0, E0  = 1E-4, 1E-4
    S0      = 1 - I0 - E0
    Y0      = (S0, E0, I0)

    ts = [(0, tm), (tm, days)]
    ms = [1, mitigation]
    M = cbm.mitigation_function(t_range, ts, ms)

    RES = odeint(cbm.seir_deriv_time, Y0, t_range, args=(M, Beta, Gamma, Sigma))
    S, E, I = RES.T
    R = 1 - S - E - I
    #seir_result = SEIR(N=n, S=S, I=I, E=E, R=R, beta=Beta, R0=R0, gamma=Gamma, sigma = Sigma, t= t_range)
    seir_result = SEIR(N=n, S=S, I=I, E=E, R=R, beta=Beta, R0=R0, gamma=Gamma, sigma = Sigma, t= t_range)

    return seir_result

def get_I_and_R_CAA(dca, N, I, R, norm=True):
    """Get the I and R vectors from the DF of CCAA"""
    In = I/N
    Rn = R/N
    if norm== False:
        In = I
        Rn = R
    Icaa = [In * p for p in dca]
    Rcaa = [Rn * p for p in dca]
    return Icaa, Rcaa


def uci_cases(IC, f_uci = 0.05):
    """Fraction of infected in UCI"""
    return [I * f_uci for I in IC]


def uci_beds(dca, t_beds = 4404):
    """Available UCI beds in Spain (proportional calculation)"""
    tot = np.sum(dca)
    beds_capita = t_beds / tot
    beds = [beds_capita * p for p in dca]
    return beds

