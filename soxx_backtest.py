import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 売買シグナルの日付を保存するグローバル変数
buy_dates = []
sell_dates = []

# 現在の日付から5年前の日付を計算
end_date = datetime.now()
start_date = end_date - timedelta(days=10*365)

def get_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    
    # MultiIndexの場合は単一レベルのカラム名に変換
    if isinstance(data.columns, pd.MultiIndex):
        # 最初のレベルのカラム名だけを使用
        data.columns = data.columns.get_level_values(0)
    
    return data

# SOXXのバックテスト戦略
class SOXXStrategy(Strategy):
    
    # パラメータ
    dc_upper_period = 120  # 上バンド判定用の期間
    dc_lower_period = 60   # 下バンド判定用の期間
    
    def donchian_upper(self, period):
        """期間内の最高値を計算（上バンド）"""
        return pd.Series(
            [max(self.data.High[max(0, i - period + 1):i + 1]) 
             for i in range(len(self.data.High))]
        )
    
    def donchian_lower(self, period):
        """期間内の最安値を計算（下バンド）"""
        return pd.Series(
            [min(self.data.Low[max(0, i - period + 1):i + 1]) 
             for i in range(len(self.data.Low))]
        )
    
    def init(self):
        # Donchian Channelをインジケーターとして登録
        self.dc_upper = self.I(self.donchian_upper, self.dc_upper_period, 
                              name=f'DC Upper ({self.dc_upper_period})', 
                              overlay=True, color='green')
        
        self.dc_lower = self.I(self.donchian_lower, self.dc_lower_period, 
                              name=f'DC Lower ({self.dc_lower_period})', 
                              overlay=True, color='red')
        
        # ポジション状態（1: ロング, 0: なし）
        self.position_state = 0
    
    def next(self):
        
        # 初期ウォームアップ期間が終わるまで待機
        if np.isnan(self.dc_upper[-1]) or np.isnan(self.dc_lower[-1]):
            return
        
        # 条件1: 120日Donchian Channelの上バンドを上回ったら、ロングポジション

        if self.data.High[-1] >= self.dc_upper[-1] and self.position_state != 1:
            current_date = self.data.index[-1].date()
            
            # 売買シグナルの日付を保存
            buy_dates.append(current_date)
            
            # 全額で購入
            self.buy()
            self.position_state = 1
            return
        
        # 条件2: 60日Donchian Channelの下バンドを下回ったら、ポジションクローズ
        if self.data.Low[-1] <= self.dc_lower[-1] and self.position_state != 0:
            current_date = self.data.index[-1].date()
            
            # 売買シグナルの日付を保存
            sell_dates.append(current_date)
            
            self.position.close()
            self.position_state = 0
            return

# メイン関数
def main():
    # グローバル変数をクリア
    global buy_dates, sell_dates
    buy_dates = []
    sell_dates = []
    
    # soxx_data = get_data("SOXX", start_date, end_date)
    # soxx_data = get_data("SPY", start_date, end_date)
    soxx_data = get_data("QQQ", start_date, end_date)
    
    print(f"バックテスト期間: {soxx_data.index[0].date()} から {soxx_data.index[-1].date()}")
    print(f"データポイント数: {len(soxx_data)}")
    
    # バックテスト実行
    bt = Backtest(soxx_data, SOXXStrategy, cash=10000, commission=.002, trade_on_close=True, exclusive_orders=True)
    stats = bt.run()
    
    print("\nバックテスト結果:")
    print(stats)

    bt.plot(filename="soxx_backtest_result.png")

    # 他の戦略で使うために購入日と、売却日を返す
    return buy_dates, sell_dates

if __name__ == "__main__":
    main()
