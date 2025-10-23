import math
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

        logfile = "logs/log.app"
        logger.add(logfile, rotation="1 MB")

        _ = bs_price(self.type, 
                     self.S, 
                     self.K, 
                     self.ttm / self.DAYS_IN_YEAR, 
                     self.r, 
                     self.vol)

        logger.info(f"Type = {self.type} | S = {self.S:.2f} | K = {self.K:.2f} | tmm = {self.ttm/self.DAYS_IN_YEAR:.4f} | price = {_:.2f}")
                   
        return _

    @property
    def delta(self) -> float:

        logfile = "logs/log.app"
        logger.add(logfile, rotation="1 MB")

        _ = bs_delta(self.type, 
                     self.S, 
                     self.K, 
                     self.ttm / self.DAYS_IN_YEAR, 
                     self.r, 
                     self.vol)

        logger.info(f"Type = {self.type} | S = {self.S:.2f} | K = {self.K:.2f} | tmm = {self.ttm/self.DAYS_IN_YEAR:.4f} | delta = {_*100:.2f}%")

        return _
    
class Portfolio:

    DAYS_IN_YEAR = 365
    MINUTES_IN_DAY = 24 * 60

    def __init__(self, call_s:Option, call_b:Option, put_s:Option, put_b:Option, trigger:float) -> None:

        logfile = "logs/log.app"
        logger.add(logfile, rotation="1 MB")

        self.call_s = call_s
        self.put_s = put_s
        self.call_b = call_b
        self.put_b = put_b
        self.trigger = trigger
        self.option_price = -call_s.price + call_b.price - put_s.price + put_b.price
        self.option_delta = -call_s.delta - put_s.delta + call_b.delta + put_b.delta
        self.perp_delta = 0
        self.total_delta = self.option_delta + self.perp_delta
        self.pnl = 0

        self.__delta_adjust(old_spot=self.call_s.S, 
                            new_spot=self.call_s.S,
                            old_delta=self.option_delta,
                            new_delta=self.total_delta)


    def __str__(self) -> str:

        _ = ""
        _ = _ + "===============================================================" + "\n"
        _ = _ + "Portfolio details" + "\n"
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"{call_s}" + "\n" 
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"{call_b}" + "\n" 
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"{put_s}" + "\n" 
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"{put_b}" + "\n" 
        _ = _ + "---------------------------------------------------------------" + "\n"
        _ = _ + f"Oprtion price: {self.option_price:2,.2f}" + "\n" 
        _ = _ + f"Option delta: {self.option_delta*100:2,.2f}%" + "\n"
        _ = _ + f"  Sold call delta: {-self.call_s.delta*100:2,.2f}%" + "\n"
        _ = _ + f"  Bought call delta: {self.call_b.delta*100:2,.2f}%" + "\n"
        _ = _ + f"  Sold put delta: {-self.put_s.delta*100:2,.2f}%" + "\n"
        _ = _ + f"  Bought call delta: {self.put_b.delta*100:2,.2f}%" + "\n"
        _ = _ + f"Perp delta: {self.perp_delta*100:2,.2f}%" + "\n" 
        _ = _ + f"Total delta: {self.total_delta*100:2,.2f}%" + "\n" 
        _ = _ + f"P&L: {self.pnl:2,.2f}" + "\n" 
        _ = _ + "===============================================================" + "\n"

        return _

    def reval(self, new_spot:float, new_ttm:float) -> None:
        
        # logger.remove()

        old_spot = self.call_s.S
        old_total_delta = self.total_delta
        
        logger.info(f"Old spot = {self.call_s.S:.2f}")
        logger.info(f"New spot = {new_spot:.2f}")

        self.call_s.S = new_spot
        self.call_b.S = new_spot

        self.call_s.ttm = new_ttm
        self.call_b.ttm = new_ttm

        self.put_s.S = new_spot
        self.put_b.S = new_spot

        self.put_s.ttm = new_ttm
        self.put_b.ttm = new_ttm

        logger.info(f"Old option price = {self.option_price:.2f}")
        new_option_price = -call_s.price + call_b.price - put_s.price + put_b.price
        logger.info(f"New option price = {new_option_price:.2f}")

        logger.info(f"Old P&L = {self.pnl:.2f}")
        self.pnl = self.pnl + (new_option_price - self.option_price)
        self.option_price = new_option_price
        logger.info(f"New P&L = {self.pnl:.2f}")

        logger.info(f"Old option delta = {self.option_delta * 100:.2f}%")
        logger.info(f"Old perp delta = {self.perp_delta * 100:.2f}%")
        logger.info(f"Old total delta = {self.total_delta * 100:.2f}%")

        self.option_delta = -call_s.delta - put_s.delta + call_b.delta + put_b.delta
        self.total_delta = self.option_delta + self.perp_delta
        self.__delta_adjust(old_spot=old_spot, new_spot=new_spot, old_delta=old_total_delta, new_delta=self.option_delta)

        logger.info(f"New option delta = {self.option_delta * 100:.2f}%")
        logger.info(f"New perp delta = {self.perp_delta * 100:.2f}%")
        logger.info(f"New total delta = {self.total_delta * 100:.2f}%")


    def __delta_adjust(self, old_spot:float, new_spot:float, old_delta:float, new_delta:float) -> None:

        # logger.remove()

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

        self.__original_portfolio = copy.deepcopy(portfolio)
        self.__polling_minutes = polling_minutes
        self.__ttm_days = ttm_days
        self.__estimated_number_of_points = int((self.__ttm_days * self.MINUTES_IN_DAY) / polling_minutes)
        self.__spot_vol = spot_vol
        self.__initial_cost = self.__original_portfolio.option_price
        self.__simulated_pnl = None
        self.__simulated_roi = None

    def __str__(self) -> str:

        _ = ""
        _ = _ + f"Simulation details" + "\n"
        _ = _ + f"TTM days: {self.__ttm_days}"  + "\n"
        _ = _ + f"Estimated number of simulated data points: {self.__estimated_number_of_points}"

        return _

    def run_once(self, spot:float, only_first_datapoints:int|None) -> None:
       
        ttm_decrement = self.__ttm_days / self.__estimated_number_of_points
        nvol = self.__spot_vol * math.sqrt(self.__polling_minutes/self.MINUTES_IN_YEAR)
        local_ttm = self.__ttm_days
        portfolio = copy.deepcopy(self.__original_portfolio)

        if only_first_datapoints is None:
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=self.__estimated_number_of_points)
        else:
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=only_first_datapoints)
        
        for lr in log_rets:
            spot = spot * math.exp(lr)
            local_ttm = local_ttm - ttm_decrement
            portfolio.reval(new_spot=spot, new_ttm=local_ttm)

        print("=================================================================")
        print("Simulation information")
        print(f"  - Time-window adjusted vol = {nvol*100:2,.4f}%")
        print(f"  - Estimated number of points = {self.__estimated_number_of_points}")
        print(f"  - ttm decrement = {ttm_decrement:.4f}")
        print("-----------------------------------------------------------------")
        print("Simulation statistics")
        print(f"  - Initial cost = {self.__initial_cost:.2f}")
        print(f"  - Final P&L = {portfolio.pnl:.2f}")
        print(f"  - ROI = {(portfolio.pnl / self.__initial_cost)*100:.2f}%")
        print("-----------------------------------------------------------------")

    def run(self, spot:float, repeat:int, display:bool) -> None:

        print("=================================================================")
        print("Simulation started")
        
        ttm_decrement = self.__ttm_days / self.__estimated_number_of_points
        nvol = self.__spot_vol * math.sqrt(self.__polling_minutes/self.MINUTES_IN_YEAR)

        simulated_pnl = []
        simulated_roi = []
        dot_count = 0       
        for _ in range(repeat):

            print(".", end='', flush=True)
            dot_count += 1
            if dot_count == 10:
                dot_count = 0
                print("\n", end='', flush=True)

            portfolio = copy.deepcopy(self.__original_portfolio)
            local_ttm = self.__ttm_days
            local_spot = spot
            log_rets = np.random.normal(loc=0.0, scale=nvol, size=self.__estimated_number_of_points)
        
            for lr in log_rets:
                local_spot = local_spot * math.exp(lr)
                local_ttm = local_ttm - ttm_decrement
                portfolio.reval(new_spot=local_spot, new_ttm=local_ttm)

            simulated_pnl.append(portfolio.pnl)
            simulated_roi.append(portfolio.pnl / self.__initial_cost)
            
            if display:
                print(f"Iteration #{_}: P&L = {portfolio.pnl:.2f} | ROI = {simulated_roi[_]:.2f}")

        self.__simulated_pnl = simulated_pnl
        self.__simulated_roi = simulated_roi

    def summarize_roi(self) -> None:
        df = pd.DataFrame({"P&L":self.__simulated_pnl, "ROI %": self.__simulated_roi})
        df["ROI %"] = df["ROI %"] * 100
        print("-----------------------------------------------------------------")
        print("Simulation summary")
        print("-----------------------------------------------------------------")
        print(df.describe())
        print("-----------------------------------------------------------------")
        plt.hist(df['ROI %'], bins=15, edgecolor='black')
        plt.title('Histograma de Retornos')
        plt.xlabel('Retorno')
        plt.ylabel('Frequência')
        plt.show()

if __name__ == "__main__":

    call_s = Option('c', S=3800.0, K=3800.0, vol=0.60, ttm=30, r=0.04)
    call_b = Option('c', S=3800.0, K=4500.0, vol=0.60, ttm=30, r=0.04)
    put_s  = Option('p', S=3800.0, K=3800.0, vol=0.60, ttm=30, r=0.04)
    put_b  = Option('p', S=3800.0, K=3100.0, vol=0.60, ttm=30, r=0.04)

    p = Portfolio(call_s=call_s, call_b=call_b, put_s=put_s, put_b=put_b, trigger=0.02)
    # print(p)
    p.reval(new_spot=3000, new_ttm=1)
    # print(p)

    # s = Simulation(portfolio=p, spot_vol=0.9, ttm_days=30, polling_minutes=5)
    # print(s)
    # s.run_once(spot=2500, only_first_datapoints=10)
    # s.run(spot = 3800, repeat=5, display=True)
    # s.summarize_roi()
