import numpy as np
from scipy.stats import norm

def black_scholes_price(spot, strike, ttm, rate, vol, option_type='call'):
    d1 = (np.log(spot / strike) + (rate + 0.5 * vol ** 2) * ttm) / (vol * np.sqrt(ttm))
    d2 = d1 - vol * np.sqrt(ttm)
    if option_type == 'call':
        price = spot * norm.cdf(d1) - strike * np.exp(-rate * ttm) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = (-spot * norm.pdf(d1) * vol / (2 * np.sqrt(ttm))
                - rate * strike * np.exp(-rate * ttm) * norm.cdf(d2)) / 365
        rho = strike * ttm * np.exp(-rate * ttm) * norm.cdf(d2) / 100
    else:
        price = strike * np.exp(-rate * ttm) * norm.cdf(-d2) - spot * norm.cdf(-d1)
        delta = -norm.cdf(-d1)
        theta = (-spot * norm.pdf(d1) * vol / (2 * np.sqrt(ttm))
                + rate * strike * np.exp(-rate * ttm) * norm.cdf(-d2)) / 365
        rho = -strike * ttm * np.exp(-rate * ttm) * norm.cdf(-d2) / 100
    gamma = norm.pdf(d1) / (spot * vol * np.sqrt(ttm))
    vega = spot * norm.pdf(d1) * np.sqrt(ttm) / 100
    return {'price': price, 'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta, 'rho': rho}
