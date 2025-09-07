import math
import numpy as np
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, rho
from py_vollib.black_scholes import implied_volatility


def calc_stradle(S, K, ttm, r, vol):

    call_price = bs('c', S, K, ttm, r, vol)
    put_price = bs('p', S, K, ttm, r, vol)
    o_price = call_price + put_price

    call_delta = delta('c', S, K, ttm, r, vol)
    put_delta = delta('p', S, K, ttm, r, vol)
    o_delta = call_delta + put_delta

    return [o_price, o_delta]

def get_formatted_ouput (S, stradle_pnl, stradle_delta, sPnL, tPnL):

    out = ""
    out = out + f"S($) = {S:12,.2f} | "
    out = out + f"o($) = {stradle_pnl:12,.2f} | "
    out = out + f"Δ = {stradle_delta:5,.2f} | "
    out = out + f"sPnL = {sPnL:12,.2f} | "
    out = out + f"tPnL = {tPnL:12,.2f}"

    return out

def run_simulation(S, K, r, ttm, vol, contract_multiplier):

    # generate simulated returns
    ttm_array = np.linspace(30/365, 1/365, 30)
    rng = np.random.default_rng() # rng = np.random.default_rng(94)
    return_array = rng.normal(loc=0.0, scale = vol * math.sqrt(1/365), size=30)

    # simulation state variables
    stradle_pnl = 0                         # options pnl
    sPnL = 0                                # scalping (i.e., dinamical delta adjust) pnl
    tPnL = 0                                # total pnl
    last_stradle_delta = 0
    delta_hedge_adjustment = 0
    S0 = S * math.exp(return_array[0])

    for ttm, ret in zip(ttm_array, return_array):

        # simulate new price
        S = S * math.exp(ret)

        # calculate options pnl (i.,e, option liquidation price) and delta
        stradle_pnl, stradle_delta = calc_stradle(S, K, ttm, r, vol)

        # hedges against total delta variation
        delta_hedge_adjustment = stradle_delta - last_stradle_delta

        # delta hedge adjustment realized pnl
        if abs(stradle_delta) < abs(last_stradle_delta) and last_stradle_delta != 0:
            sPnL = sPnL + delta_hedge_adjustment * (S - S0) * contract_multiplier

        # accumulate total portfolio PnL
        tPnL = stradle_pnl + sPnL

        # print simulation output
        sim_out = get_formatted_ouput(S, stradle_pnl, stradle_delta, sPnL, tPnL)
        print(sim_out)

        # update simulation state
        last_stradle_delta = stradle_delta
        S0 = S

# set simulation paramaters
contract_multiplier = 1
S = 100000 * contract_multiplier
K = 100000 * contract_multiplier
r = 0.04
ttm = 1/12
vol =0.6

run_simulation(S, K, r, ttm, vol, contract_multiplier)