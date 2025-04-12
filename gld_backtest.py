import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from soxx_backtest import get_data, start_date, end_date, main as soxx_main

# GLDのバックテスト戦略
class GLDStrategy(Strategy):
    
    def init(self):
        # SOXXのバックテストを実行して売買シグナルの日付を取得
        self.buy_dates, self.sell_dates = soxx_main()
        
        # 日付をdatetimeオブジェクトに変換（比較のため）
        self.sell_dates_dt = [pd.Timestamp(date) for date in self.sell_dates]
        self.buy_dates_dt = [pd.Timestamp(date) for date in self.buy_dates]
        
        # ポジション状態（1: ロング, 0: なし）
        self.position_state = 0
    
    def next(self):
        current_date = self.data.index[-1]
        
        # SOXXが売られたタイミング（SOXXの60日Donchian Channelの下バンドを下回った日）でGLDに投資
        if any(sell_date.date() == current_date.date() for sell_date in self.sell_dates_dt) and self.position_state != 1:
            print(f"GLD BUY SIGNAL at {current_date.date()} (SOXXの売却シグナルに基づく)")
            self.buy()
            self.position_state = 1
            return
        
        # SOXXが買われたタイミング（SOXXの120日Donchian Channelの上バンドを上回った日）でGLDを売却
        if any(buy_date.date() == current_date.date() for buy_date in self.buy_dates_dt) and self.position_state != 0:
            print(f"GLD SELL SIGNAL at {current_date.date()} (SOXXの購入シグナルに基づく)")
            self.position.close()
            self.position_state = 0
            return

# メイン関数
def main():
    # GLDのデータを取得
    gld_data = get_data("GLD", start_date, end_date)
    
    print(f"\nGLDバックテスト期間: {gld_data.index[0].date()} から {gld_data.index[-1].date()}")
    print(f"データポイント数: {len(gld_data)}")
    
    # バックテスト実行
    bt = Backtest(gld_data, GLDStrategy, cash=10000, commission=.002, trade_on_close=True, exclusive_orders=True)
    stats = bt.run()
    
    print("\nGLDバックテスト結果:")
    print(stats)

    bt.plot(filename="gld_backtest_result.png")

if __name__ == "__main__":
    main()
