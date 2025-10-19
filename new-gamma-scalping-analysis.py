import math
import numpy as np
import pandas as pd
from loguru import logger
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
        _ = _ + f"Spot: {self.S:2,.2f}" + "\n"
        _ = _ + f"Strike: {self.K}" + "\n"
        _ = _ + f"Vol: {self.vol * 100:2,.2f}" + "\n"
        _ = _ + f"TTM (days): {self.ttm:.2f}" + "\n"
        _ = _ + f"Price: {self.price:2,.2f}" + "\n"
        _ = _ + f"Delta: {self.delta * 100:2,.2f}%"

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

        logfile = "logs/log.app"
        logger.add(logfile, rotation="1 MB")

        self.call = call
        self.put = put
        self.trigger = trigger
        self.option_price = call.price + put.price
        self.option_delta = call.delta + put.delta
        self.perp_delta = 0
        self.total_delta = self.option_delta + self.perp_delta
        self.pnl = 0

        self.__delta_adjust(old_spot=self.call.S, 
                            new_spot=self.call.S,
                            old_delta=self.option_delta,
                            new_delta=self.total_delta)


    def __str__(self) -> str:

        _ = ""
        _ = _ + "===============================================================" + "\n"
        _ = _ + "Portfolio details" + "\n"
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"{call}" + "\n" 
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"{put}" + "\n" 
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"Oprtion price: {self.option_price:2,.2f}" + "\n" 
        _ = _ + f"Option delta: {self.option_delta*100:2,.2f}%" + "\n" 
        _ = _ + f"Perp delta: {self.perp_delta*100:2,.2f}%" + "\n" 
        _ = _ + f"Total delta: {self.total_delta*100:2,.2f}%" + "\n" 
        _ = _ + f"P&L: {self.pnl:2,.2f}" + "\n" 
        _ = _ + "===============================================================" + "\n"

        return _

    def reval(self, new_spot:float, new_ttm:float) -> None:
        
        logger.remove()

        old_spot = self.call.S
        old_total_delta = self.total_delta
        
        logger.info(f"Old spot = {self.call.S:.2f}")
        logger.info(f"New spot = {new_spot:.2f}")

        self.call.S = new_spot
        self.call.ttm = new_ttm

        self.put.S = new_spot
        self.put.ttm = new_ttm

        logger.info(f"Old option price = {self.option_price:.2f}")
        new_option_price = self.call.price + self.put.price
        logger.info(f"New oprtion = {new_option_price:.2f}")

        logger.info(f"Old P&L = {self.pnl:.2f}")
        self.pnl = self.pnl + (new_option_price - self.option_price)
        self.option_price = new_option_price
        logger.info(f"New P&L = {self.pnl:.2f}")

        logger.info(f"Old option delta = {self.option_delta * 100:.2f}%")
        logger.info(f"Old perp delta = {self.perp_delta * 100:.2f}%")
        logger.info(f"Old total delta = {self.total_delta * 100:.2f}%")

        self.option_delta = self.call.delta + self.put.delta
        self.total_delta = self.option_delta + self.perp_delta
        self.__delta_adjust(old_spot=old_spot, new_spot=new_spot, old_delta=old_total_delta, new_delta=self.option_delta)

        logger.info(f"New option delta = {self.option_delta * 100:.2f}%")
        logger.info(f"New perp delta = {self.perp_delta * 100:.2f}%")
        logger.info(f"New total delta = {self.total_delta * 100:.2f}%")


    def __delta_adjust(self, old_spot:float, new_spot:float, old_delta:float, new_delta:float) -> None:

        logger.remove()

        logger.info("Portfolio.__delta_adjust()")
        logger.info(f"Accumulated P&L: {self.pnl:.2f}")
        logger.info(f"Option delta before adjustment = {self.option_delta * 100:.2f}%")
        logger.info(f"Perp delta before adjustment = {self.perp_delta * 100:.2f}%")
        logger.info(f"Total delta before adjustment = {self.total_delta * 100:.2f}%")
        logger.info(f"New spot - old spot: {new_spot:.2f} - {old_spot:.2f} = {new_spot - old_spot:.2f}")

        if abs(new_delta) >= self.trigger:

            logger.info(f"New delta trigger: [{abs(new_delta)*100:.2f}% > {self.trigger*100:.2f}%]")
            logger.info(f"Variation of P&L due to delta adjustment: {(new_spot - old_spot) * self.perp_delta:.2f}")
            
            self.pnl = self.pnl + (new_spot - old_spot) * self.perp_delta
            self.perp_delta = -new_delta
            self.total_delta = self.option_delta + self.perp_delta

            logger.info(f"New accumulated P&L: {self.pnl:.2f}")
            logger.info(f"Option delta after adjustment = {self.option_delta * 100:.2f}%")
            logger.info(f"Perp delta after adjustment = {self.perp_delta * 100:.2f}%")
            logger.info(f"Total delta after adjustment = {self.total_delta * 100:.2f}%")


class Simulation:

    DAYS_IN_YEAR = 365
    MINUTES_IN_DAY = 24 * 60
    MINUTES_IN_YEAR = MINUTES_IN_DAY * 365

    def __init__(self, portfolio:Portfolio, spot_vol:float, ttm_days:float, polling_minutes:int) -> None:

        self.__portfolio = portfolio
        self.__polling_minutes = polling_minutes
        self.__ttm_days = ttm_days
        self.__estimated_number_of_points = int((self.__ttm_days * self.MINUTES_IN_DAY) / polling_minutes)
        self.__spot_vol = spot_vol
        self.__pnl_path = None
        self.__initial_cost = self.__portfolio.option_price

        logfile = "logs/log.app"
        logger.add(logfile, rotation="1 MB")

    def __str__(self) -> str:

        _ = ""
        _ = _ + f"Simulation details" + "\n"
        _ = _ + f"TTM days: {self.__ttm_days}"  + "\n"
        _ = _ + f"Estimated number of simulated data points: {self.__estimated_number_of_points}"

        return _

    def run(self, spot:float, only_first_datapoints:int|None) -> None:
       
        ttm_decrement = self.__ttm_days / self.__estimated_number_of_points
        nvol = self.__spot_vol * math.sqrt(self.__polling_minutes/self.MINUTES_IN_YEAR)
        local_ttm = self.__ttm_days

        if only_first_datapoints is None:
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=self.__estimated_number_of_points)
        else:
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=only_first_datapoints)
        
        print("Simulation result")
        print(f"Time-window adjusted vol = {nvol*100:2,.4f}%")
        print(f"Estimated number of points = {self.__estimated_number_of_points}")
        print(f"ttm decrement = {ttm_decrement:.4f}")

        pnl_path = []
        for i, lr in enumerate(log_rets):
            spot = spot * math.exp(lr)
            local_ttm = local_ttm - ttm_decrement
            self.__portfolio.reval(new_spot=spot, new_ttm=local_ttm)
            pnl_path.append(self.__portfolio.pnl)
            # print(f"simulation interation #{i}")
            # print(f"S = {spot:.2f}")
            # print(f"ttm = {local_ttm:.6f}")
        self.__pnl_path = pnl_path

    def summarize(self) -> None:
        df = pd.DataFrame(self.__pnl_path, columns=["P&L"])
        df["%"] = df["P&L"] / self.__initial_cost * 100
        print("Simulation statistics")
        print(f"Initial cost = {self.__initial_cost:.2f}")
        print(f"Final P&L = {self.__portfolio.pnl:.2f}")
        print(f"ROE = {(self.__portfolio.pnl / self.__initial_cost)*100:.2f}%")
        print(df.describe())

if __name__ == "__main__":

    call = Option('c', S=200.0, K=200.0, vol=0.92, ttm=30, r=0.04)
    put  = Option('p', S=200.0, K=200.0, vol=0.92, ttm=30, r=0.04)

    p = Portfolio(call=call, put=put, trigger=0.02)

    s = Simulation(portfolio=p, spot_vol=1.20, ttm_days=30, polling_minutes=5)

    s.run(spot=200, only_first_datapoints=None)
    print(p)

    s.summarize()