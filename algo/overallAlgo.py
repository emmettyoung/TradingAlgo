from numbers import Number
import yfinance as yf
import pandas as pd
import math
import requests

wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
tables = pd.read_html(wiki_url)
sp500_table = tables[0]  # The first table is the S&P 500 constituents

# Extract the ticker symbols as a list
sp500_companies_real = sp500_table['Symbol'].tolist()
sp500_companies_real = [m.replace('.', '-') for m in sp500_companies_real]
sp500_companies_mock = ['PLTR', 'GEV', 'NRG', 'VST', 'HWM', 'DG', 'AXON', 'APH', 'NFLX', 'STX', 'RL', 'AVGO', 'JBL', 'JCI', 'MOS', 'ULTA', 'PAYC', 'GILD', 'GE', 'TPR', 'SPY']

class Stock:
    """Stock algo class"""

    def __init__(self) -> None:
        #all_data_real = yf.download(
        #    sp500_companies_real + ['SPY'], period="1y", group_by='ticker', auto_adjust=True)
        all_data = yf.download(sp500_companies_mock, period="1y", group_by='ticker', auto_adjust=True)
        self.stocks = all_data
        self.final_list = []
        self.final_dict = {}

    def average_score_weight(self, stock) -> Number:
        """Function that computes a score for a stocks averages overtime"""
        period_list = [15, 20, 30, 50, 100, 200]
        overall_score = 0

        if stock not in self.stocks.columns.levels[0]:
            print(
                f"No data found for {stock}. It may be delisted or data is unavailable.")
            return 0

        for i in period_list:
            try:
                stock_data = self.stocks[stock].tail(i)
                spy_data = self.stocks['SPY'].tail(i)
                if stock_data.empty or spy_data.empty:
                    continue

                stock_ret = (stock_data['Close'].iloc[-1] -
                             stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0]
                spy_ret = (spy_data['Close'].iloc[-1] -
                           spy_data['Close'].iloc[0]) / spy_data['Close'].iloc[0]
                comparison = stock_ret - spy_ret

                if i == 15:
                    overall_score += (20 * (1 + comparison))
                if i == 20:
                    overall_score += (12 * (1 + comparison))
                if i == 30:
                    overall_score += (10 * (1 + comparison))
                if i == 50:
                    overall_score += (12 * (1 + comparison))
                if i == 100:
                    overall_score += (17 * (1 + comparison))
                if i == 200:
                    overall_score += (29 * (1 + comparison))

            except Exception as e:
                print(f"Error processing {stock} for period {i}: {e}")
                continue

        return overall_score

    def compute_rsi(self, stock) -> Number:
        """Computes the rsi of a stock over different periods"""
        period_list = [15, 20, 30, 50, 100, 200]
        rsi = 0

        for i in period_list:
            stock_data = self.stocks[stock].tail(i)
            positive_gain_days = []
            negative_loss_days = []
            if stock_data.empty:
                print(
                    f"No data found for {stock}. It may be delisted or data is unavailable.")
                break

            for j in stock_data['Close'].pct_change().dropna():
                if j > 0:
                    positive_gain_days.append(j)
                else:
                    negative_loss_days.append(j)

            if len(positive_gain_days) > 0:
                avg_pos_gain = sum(positive_gain_days) / \
                    len(positive_gain_days)
            else:
                avg_pos_gain = 0

            if len(negative_loss_days) > 0:
                avg_neg_loss = (sum(negative_loss_days) /
                                len(negative_loss_days)) * (-1)

            else:
                avg_neg_loss = 0

            net = stock_data['Close'].pct_change().iloc[-1]

            if net > 0:
                current_gain = net
                current_loss = 0

            else:
                current_gain = 0
                current_loss = net

            rsi_combined = 100 - (100 / (1 +
                                         (((avg_pos_gain*13) + current_gain) / ((avg_neg_loss*13) + current_loss))))

            if i == 15:
                rsi += rsi_combined*.20
            if i == 20:
                rsi += rsi_combined*.12
            if i == 30:
                rsi += rsi_combined*.10
            if i == 50:
                rsi += rsi_combined*.12
            if i == 100:
                rsi += rsi_combined*.17
            if i == 200:
                rsi += rsi_combined*.29

        return rsi

    def compare_pe_volume_api(self, stock):
        """Function for calculating a stocks avg pe and avg trade volume over last 3 weeks"""
        period = 21
        final_dict = {}
        stock_data_volume = self.stocks[stock].tail(period)
        if stock_data_volume.empty:
            print(
                f"No data found for {stock}. It may be delisted or data is unavailable.")
            return {}
        volume_rate = ((stock_data_volume['Volume'].iloc[-2] -
                stock_data_volume['Volume'].iloc[0]) / stock_data_volume['Volume'].iloc[0]) * 100

        final_dict['volume_rate'] = volume_rate

        pe_list = []
        api_key = 'bfvxsIsQrMUigGwRYj54pKHCNDYKHTIc'

        url = f'https://financialmodelingprep.com/api/v3/income-statement/{stock}?limit=1&apikey={api_key}'
        response = requests.get(url)
        data = response.json()
        try:
            eps = data[0]['eps']
        except (KeyError, IndexError):
            eps = None

        if eps:
            for i in range(1, period+1):
                stock_data_pe = self.stocks[stock].tail(i)
                current_price = stock_data_pe['Close'].iloc[0]
                pe_ratio = current_price / eps
                pe_list.append(pe_ratio)
            pe_rate = ((pe_list[-1] - pe_list[0]) / pe_list[0]) * 100
            final_dict['pe_rate'] = pe_rate

        else:
            final_dict['pe_rate'] = 0
        return final_dict

    def compare_pe_volume_yf(self, stock):
        """Function for calculating a stocks avg pe and avg trade volume over last 3 weeks"""
        period = 21
        final_dict = {}
        stock_data_volume = self.stocks[stock].tail(period)
        if stock_data_volume.empty:
            print(
                f"No data found for {stock}. It may be delisted or data is unavailable.")
            return {}
        volume_rate = ((stock_data_volume['Volume'].iloc[-2] -
                stock_data_volume['Volume'].iloc[0]) / stock_data_volume['Volume'].iloc[0]) * 100

        final_dict['volume_rate'] = volume_rate

        pe_list = []

        eps = yf.Ticker(stock).info.get('trailingEps')
        if eps:
            for i in range(1, period+1):
                stock_data_pe = self.stocks[stock].tail(i)
                current_price = stock_data_pe['Close'].iloc[0]
                pe_ratio = current_price / eps
                pe_list.append(pe_ratio)
            pe_rate = ((pe_list[-1] - pe_list[0]) / pe_list[0]) * 100
            final_dict['pe_rate'] = pe_rate

        else:
            final_dict['pe_rate'] = 0
        return final_dict

    def f(self, x):
        """gets the curve used to weight a pe ratio"""
        return (-.1 * math.log(x)) + .2

    def weight_pe(self, stock):
        """function that accesses the p/e ratio of a company"""
        volume = self.compare_pe_volume_yf(stock)['volume_rate']
        pe = self.compare_pe_volume_yf(stock)['pe_rate']
        comparison = pe / volume
        if comparison >= 0:
            return self.f(comparison) * 100
        if comparison < 0:
            if pe >= 0 and volume < 0:
                return self.f(3) * 100
            if pe < 0 and volume >= 0:
                return self.f(.8) * 100

    def insertion_sort(self, dictionary, stock, final_list):
        """Insertion sort for sorting companies"""
        current = 0
        if len(final_list) == 0:
            return [stock]
        while current < len(final_list):

            if dictionary[stock] >= dictionary[final_list[current]]:
                final_list.insert(current, stock)
                break
            if current >= len(final_list) - 1:
                final_list.append(stock)
                break
            current += 1
        return final_list

    def access_companies(self):
        """Function that begins the access process of each company"""
        for stock in self.stocks.columns.levels[0]:
            if stock == "SPY":
                continue
            individual_stock_score = 0
            individual_stock_score += self.average_score_weight(stock) * .2
            individual_stock_score += self.compute_rsi(stock) * .3
            try:
                individual_stock_score += self.weight_pe(stock)
            except (ValueError):
                print(stock)
            self.final_dict[stock] = individual_stock_score
            self.final_list = self.insertion_sort(
                self.final_dict, stock, self.final_list)

        return self.final_list[:20]


if __name__ == "__main__":
    stock_obj = Stock()
    ranked_list = stock_obj.access_companies()
    print("Top 20 Companies:", ranked_list)
