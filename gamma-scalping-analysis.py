import math
import numpy as np
import statistics as stats
import matplotlib
import matplotlib.pyplot as plt
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, rho
from py_vollib.black_scholes import implied_volatility

def calc_stradle(S, K, ttm, base, r, vol):

    call_price = bs('c', S, K, ttm/base, r, vol)
    put_price = bs('p', S, K, ttm/base, r, vol)
    o_price = call_price + put_price

    call_delta = delta('c', S, K, ttm/base, r, vol)
    put_delta = delta('p', S, K, ttm/base, r, vol)
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

def print_basic_stats(dados):

    arr = np.array(dados)

    ans = {
        "n            ": len(arr),
        "média        ": np.mean(arr),
        "mediana      ": np.median(arr),
        "desvio_padrão": np.std(arr, ddof=1), # amostral
        "mínimo       ": np.min(arr),
        "máximo       ": np.max(arr)
        }
    
    for k, v in ans.items():
        print(f"{k} : {v:,.2f}")

def run_simulation(S, K, r, ttm, base, vol, contract_multiplier, print_sim_out):

    # generate simulated returns
    ttm_array = np.linspace(ttm, 1, ttm)
    rng = np.random.default_rng(94) # rng = np.random.default_rng(94)
    return_array = rng.normal(loc=0.0, scale = vol * math.sqrt(1/base), size=30)
    # return_array = [-0.01 for n in range(30)]
    # return_array = [0.01*(-1)**n for n in range(30)]

    # simulation state variables
    stradle_pnl = 0                         # options pnl
    sPnL = 0                                # scalping (i.e., dinamical delta adjust) pnl
    tPnL = 0                                # total pnl
    dPnL = 0
    last_stradle_delta = 0
    delta_hedge_adjustment = 0
    S0 = S * math.exp(return_array[0])
    stradle_cost, _ = calc_stradle(S, K, ttm, base, r, vol)

    if print_sim_out:
        print(f"starting simulation...")
        print(f"spot price S = {S:,.2f} | strike price K = {K:,.2f} | strade cost = {stradle_cost:,.2f}")

    for ttm, ret in zip(ttm_array, return_array):

        # simulate new price
        S = S * math.exp(ret)

        # calculate options pnl (i.,e, option liquidation price) and delta
        stradle_pnl, stradle_delta = calc_stradle(S, K, ttm, base, r, vol)

        # hedges against total delta variation
        delta_hedge_adjustment = stradle_delta - last_stradle_delta

        # delta hedge adjustment realized pnl
        if last_stradle_delta != 0:
            sPnL = sPnL + delta_hedge_adjustment * (S - S0) * contract_multiplier

        # accumulate total portfolio PnL
        tPnL = -stradle_cost + stradle_pnl + sPnL

        # print simulation output
        if print_sim_out:
            sim_out = get_formatted_ouput(S, stradle_pnl, stradle_delta, sPnL, tPnL)
            print(sim_out)

        # update simulation state
        last_stradle_delta = stradle_delta
        S0 = S

    return tPnL

# run simulation

if __name__ == "__main__":

    # set simulation paramaters
    vols = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    for vol in vols:
        contract_multiplier = 1
        S = 100000 * contract_multiplier
        K = 100000 * contract_multiplier
        r = 0.04
        ttm = 30
        base = 365

        sim_pnl=[]
        for i in range(1000):
            sim_pnl.append(run_simulation(S, K, r, ttm, base, vol, contract_multiplier, print_sim_out=False))
        print_basic_stats(sim_pnl)
        # run_simulation(S, K, r, ttm, base, vol, contract_multiplier, print_sim_out=True)

        matplotlib.use("TkAgg")
        plt.hist(sim_pnl, bins=15, edgecolor="black", alpha=0.7)
        plt.title("Histograma dos Dados")
        plt.xlabel("Valores")
        plt.ylabel("Frequência")
        plt.show()
