import yfinance as yf
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Téléchargement des données
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM', 'JNJ', 'V', 
           'PG', 'MA', 'HD', 'DIS', 'PYPL', 'ADBE', 'NFLX', 'CRM', 'BAC', 'INTC']

# Téléchargement des données historiques (2015-2025)
data = yf.download(tickers, start="2015-01-01", end="2025-01-01", interval="1d", group_by='ticker')

def count_candle_streaks(df, n):
    """
    Calcule les probabilités de retournement après n chandelles consécutives dans la même direction
    """
    up_streaks = 0
    up_followed_by_red = 0
    down_streaks = 0
    down_followed_by_green = 0
    
    for ticker in tickers:
        try:
            asset_data = df[ticker].dropna()
            close = asset_data['Close']
            open_ = asset_data['Open']
            
            # Identifier les chandelles vertes (close > open) et rouges (close < open)
            green = close > open_
            red = close < open_
            
            # Calculer les streaks verts
            streak = 0
            for i in range(1, len(green)):
                if green.iloc[i]:
                    streak += 1
                else:
                    if streak >= n:
                        up_streaks += 1
                        if red.iloc[i]:
                            up_followed_by_red += 1
                    streak = 0
            
            # Calculer les streaks rouges
            streak = 0
            for i in range(1, len(red)):
                if red.iloc[i]:
                    streak += 1
                else:
                    if streak >= n:
                        down_streaks += 1
                        if green.iloc[i]:
                            down_followed_by_green += 1
                    streak = 0
                    
        except KeyError:
            continue
    
    # Calculer les fractions
    up_fraction = up_followed_by_red / up_streaks if up_streaks > 0 else 0
    down_fraction = down_followed_by_green / down_streaks if down_streaks > 0 else 0
    
    return up_fraction, down_fraction

# Exemple d'utilisation de la fonction pour n=3
n = 3
up_frac, down_frac = count_candle_streaks(data, n)
print(f"Pour {n} chandelles vertes suivies d'une rouge: {up_frac:.2%}")
print(f"Pour {n} chandelles rouges suivies d'une verte: {down_frac:.2%}")

class ConsecutiveRedGreenStrategy(Strategy):
    """
    Stratégie qui trade dans les deux directions (long et short)
    """
    n = 3  # Nombre de chandelles consécutives
    
    def init(self):
        pass
    
    def next(self):
        # Vérifier si nous avons déjà une position ouverte
        if self.position:
            return
        
        # Vérifier les conditions pour un achat (n chandelles rouges consécutives)
        red_streak = True
        for i in range(1, self.n + 1):
            if self.data.Close[-i] >= self.data.Open[-i]:  # Pas rouge
                red_streak = False
                break
                
        if red_streak:
            self.buy()
            return
        
        # Vérifier les conditions pour une vente (n chandelles vertes consécutives)
        green_streak = True
        for i in range(1, self.n + 1):
            if self.data.Close[-i] <= self.data.Open[-i]:  # Pas verte
                green_streak = False
                break
                
        if green_streak:
            self.sell()
    
    # Fermer la position à la fin de la journée
    def on_day_end(self):
        self.position.close()

class ConsecutiveRedStrategy(Strategy):
    """
    Stratégie long-only (n chandelles rouges consécutives seulement)
    """
    n = 3  # Nombre de chandelles consécutives
    
    def init(self):
        pass
    
    def next(self):
        if self.position:
            return
        
        # Vérifier les conditions pour un achat (n chandelles rouges consécutives)
        red_streak = True
        for i in range(1, self.n + 1):
            if self.data.Close[-i] >= self.data.Open[-i]:  # Pas rouge
                red_streak = False
                break
                
        if red_streak:
            self.buy()
    
    # Fermer la position à la fin de la journée
    def on_day_end(self):
        self.position.close()

# Backtesting pour chaque actif
results = {}
for ticker in tickers:
    try:
        # Préparer les données
        asset_data = data[ticker].dropna()
        asset_data.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
        # Exécuter le backtest
        bt = Backtest(asset_data, ConsecutiveRedStrategy, cash=100000, commission=.0002, exclusive_orders=True)
        stats = bt.run()
        
        results[ticker] = stats['Return [%]']
    except KeyError:
        continue

# Afficher les résultats
print("\nRésultats du backtesting (stratégie long-only):")
for ticker, ret in results.items():
    print(f"{ticker}: {ret:.2f}%")

# Calculer le rendement total et moyen
total_return = sum(results.values())
avg_return = total_return / len(results)
print(f"\nRendement total sur {len(results)} actifs: {total_return:.2f}%")
print(f"Rendement moyen par actif: {avg_return:.2f}%")