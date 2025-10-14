import math
import numpy as np
import statistics as stats
from py_vollib.black_scholes import black_scholes as bs_price
from py_vollib.black_scholes.greeks.analytical import delta as bs_delta


class Option:

    DAYS_IN_YEAR = 365

    def __init__(self, type:str, S:float, K:float, vol:float, ttm:float, r:float):

        if type != 'c' and type != 'p':
            raise TypeError("Option: type must be either 'c' (for call) or 'p' (for put)")
        else:
            self.type = type

        self.S = S
        self.K = K
        self.vol = vol
        self.ttm = ttm
        self.r = r

    def __str__(self):

        _ = ""
        _ = _ + f"Option type: {self.type}" + "\n"
        _ = _ + f"Spot: {self.S}" + "\n"
        _ = _ + f"Strike: {self.K}" + "\n"
        _ = _ + f"Vol: {self.vol * 100:2,.2f}" + "\n"
        _ = _ + f"TTM (days): {self.ttm:.2f}" + "\n"
        _ = _ + f"Price: {self.price:2,.2f}" + "\n"
        _ = _ + f"Delta: {self.delta * 100:2,.2f}%" + "\n"

        return _

    @property
    def price(self) -> float:

        _ = bs_price(self.type, 
                        self.S, 
                        self.K, 
                        self.ttm / self.DAYS_IN_YEAR, 
                        self.r, 
                        self.vol)
            
        return _

    @property
    def delta(self) -> float:

        _ = bs_delta(self.type, 
                     self.S, 
                     self.K, 
                     self.ttm / self.DAYS_IN_YEAR, 
                     self.r, 
                     self.vol)
            
        return _
    
class Portfolio:

    DAYS_IN_YEAR = 365
    MINUTES_IN_DAY = 24 * 60

    def __init__(self, call:Option, put:Option, trigger:float) -> None:

        self.call = call
        self.put = put
        self.trigger = trigger

        self.cost = -(call.price + put.price)
        self.delta = call.delta + put.delta
        self.pnl = 0

    def __str__(self) -> str:

        _ = ""
        _ = _ + f"{call}" + "\n" 
        _ = _ + f"{put}" + "\n" 
        _ = _ + f"Cost: {self.cost:2,.2f}" + "\n" 
        _ = _ + f"Delta: {self.delta*100:2,.2f}%" + "\n" 
        _ = _ + f"P&L: {self.pnl:2,.2f}" + "\n" 

        return _

    def reval(self, new_spot:float, new_ttm:float) -> None:
        
        self.call.S = new_spot
        self.call.ttm = new_ttm

        self.put.S = new_spot
        self.put.ttm = new_ttm

        new_cost = self.call.price + self.put.price
        self.pnl = self.cost + new_cost

        self.delta = self.call.delta + self.put.delta

class Simulation:

    DAYS_IN_YEAR = 365
    MINUTES_IN_DAY = 24 * 60

    def __init__(self, portfolio:Portfolio, spot_vol:float, ttm_days:float, polling_minutes:int) -> None:

        self.__portfolio = portfolio
        self.__polling_minutes = polling_minutes
        self.__ttm_days = ttm_days
        self.__estimated_number_of_points = int((self.__ttm_days * self.MINUTES_IN_DAY) / polling_minutes)
        self.__spot_volt = spot_vol

    def __str__(self) -> str:

        _ = ""
        _ = _ + f"Simulation details" + "\n"
        _ = _ + f"TTM days: {self.__ttm_days}"  + "\n"
        _ = _ + f"Estimated number of simulated data points: {self.__estimated_number_of_points}"  + "\n"

        return _

    def run(self, spot:float, only_first_datapoints:int) -> None:
        
        ttm_decrement = 1.0 / self.__estimated_number_of_points
        nvol = self.__spot_volt * math.sqrt(ttm_decrement/self.DAYS_IN_YEAR)
        local_ttm = self.__ttm_days

        if only_first_datapoints is not None:
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=only_first_datapoints)
        else:
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=self.__estimated_number_of_points)
        
        print("Simulation result")
        print(f"Using time-window adjusted vol = {nvol*100:2,.4f}%")

        for lr in log_rets:
            spot = spot * math.exp(lr)
            local_ttm = local_ttm - ttm_decrement
            self.__portfolio.reval(new_spot=spot, new_ttm=local_ttm)
            print(self.__portfolio)


if __name__ == "__main__":

    call = Option('c', S=197.0, K=200.0, vol=0.92, ttm=17, r=0.04)
    put  = Option('p', S=197.0, K=200.0, vol=0.92, ttm=17, r=0.04)

    p = Portfolio(call=call, put=put, trigger=0.02)
    # print(p)

    p.reval(new_spot=210, new_ttm=17)
    # print(p)

    p.reval(new_spot=170, new_ttm=17)
    # print(p)

    s =Simulation(portfolio=p, spot_vol=0.90, ttm_days=17, polling_minutes=5)
    print(s)
    s.run(spot=200,only_first_datapoints=10)
    # s.run(spot=200, only_first_datapoints=None) 