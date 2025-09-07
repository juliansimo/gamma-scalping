import math
import numpy as np
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, rho
from py_vollib.black_scholes import implied_volatility

m = 1
S, K, r, ttm, vol = 100000 * m, 100000 * m, 0.04, 1/12, 0.6

ttm_array = np.linspace(30/365, 1/365, 30)
rng = np.random.default_rng(94)
rng = np.random.default_rng()
return_array = rng.normal(loc=0.0, scale = vol * math.sqrt(1/365), size=30)

oPnL = 0
sPnL = 0
tPnL = 0
last_total_delta=0
delta_hedge_notional = 0
delta_hedge_adjustment = 0
S0 = S * math.exp(return_array[0])

for ttm, ret in zip(ttm_array, return_array):

    # simulate new price
    S = S * math.exp(ret)

    # calculate options price
    call_price = bs('c', S, K, ttm, r, vol)
    put_price = bs('p', S, K, ttm, r, vol)
    oPnL = call_price + put_price

    # calculate options and total portfolio delta
    call_delta = delta('c', S, K, ttm, r, vol)
    put_delta = delta('p', S, K, ttm, r, vol)
    total_delta = call_delta + put_delta

    # hedges against total delta variation
    delta_hedge_adjustment = total_delta - last_total_delta

    # delta hedge adjustment realized pnl
    if abs(total_delta) < abs(last_total_delta) and last_total_delta != 0:
        sPnL = sPnL + delta_hedge_adjustment * (S - S0) * m

    tPnL = oPnL + sPnL

    out = ""
    out = out + f"S($) = {S:12,.2f} | "
    out = out + f"o($) = {oPnL:12,.2f} | "
    out = out + f"Δ = {total_delta:8,.2f} | "
    out = out + f"sPnL = {sPnL:12,.2f} | "
    out = out + f"tPnL = {tPnL:12,.2f}"

    print(out)

    # last but not least, update simulation state
    last_total_delta = total_delta
    S0 = S
