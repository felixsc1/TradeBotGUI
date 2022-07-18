import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_backtest_file(filename):
    df = pd.read_csv(filename, index_col=[0])
    df.dropna(inplace=True)
    return df


def find_zero_crossings(df):
    # step 1: Show the price at the next timepoint where z-score changes sign.

    import numpy as np
    df['ZscoreSwapped'] = np.sign(df['Zscore']).diff().ne(0)
    df['NextPrice_sym1'] = np.nan
    df.loc[df['ZscoreSwapped'].shift(-1) == True,
           'NextPrice_sym1'] = df[df.columns[0]].shift(-1)
    df['NextPrice_sym1'].bfill(axis='rows', inplace=True)

    df['NextPrice_sym2'] = np.nan
    df.loc[df['ZscoreSwapped'].shift(-1) == True,
           'NextPrice_sym2'] = df[df.columns[1]].shift(-1)
    df['NextPrice_sym2'].bfill(axis='rows', inplace=True)

    df.dropna(inplace=True)  # some NaNs are created at the end
    df.reset_index(drop=True, inplace=True)
    return df


def find_triggers(data, threshold):
    """
    Find timepoints where z-score is above threshold.
    -only when there was a closing time point after the last trigger.

    Also finds for each trigger corresponding next time index where z-score crosses zero (=NextClose)

    Note: first timepoint won't be considered!
    """
    data['Trigger'] = False
    data['NextClose'] = 0
    last_trigger_index = 0
    for i in range(1, len(data)):
        if abs(data['Zscore'].iloc[i]) >= threshold:
            #    if abs(data['Zscore'].iloc[i-1]) <= threshold:
            # finds the first data point (starting from the open position time point) where Z Score crosses zero
            _list = data['ZscoreSwapped'][i+1:]
            try:
                close_position_index = i + _list.tolist().index(True) + 1
                if data['NextClose'].iloc[last_trigger_index] < i:
                    data['Trigger'].iloc[i] = True
                    data['NextClose'].iloc[i] = close_position_index
                    last_trigger_index = i
            except:
                # for the last few data points there might be not exit point available - don't create triggers then.
                # command "_list.tolist().index(True)" throws exception
                continue

    return data


def calculate_orders(data, long_coin):
    """
    We specify for which coin (0 or 1) we go long when z-score is positive.
    Whenever there is a trigger, and positive z-score go long at the current price of that coin.
    Whenever there is a trigger, and negative z-score go short at the current price of that coin.
    The opposite happens for the other coin at the same time.
    """
    data['LongAt_sym1'] = 0
    data['ShortAt_sym1'] = 0
    data['LongAt_sym2'] = 0
    data['ShortAt_sym2'] = 0
    data['LongCoin'] = np.nan

    for i in range(1, len(data)):
        if long_coin == 0 and data['Trigger'].iloc[i]:
            if data['Zscore'].iloc[i] > 0:
                # columns 0 and 1 are the price data for the two coins
                data['LongAt_sym1'].iloc[i] = data.iloc[i, 0]
                data['LongCoin'].iloc[i] = 0
                data['ShortAt_sym2'].iloc[i] = data.iloc[i, 1]
            if data['Zscore'].iloc[i] < 0:
                data['LongAt_sym2'].iloc[i] = data.iloc[i, 1]
                data['LongCoin'].iloc[i] = 1
                data['ShortAt_sym1'].iloc[i] = data.iloc[i, 0]

        if long_coin == 1 and data['Trigger'].iloc[i]:
            if data['Zscore'].iloc[i] > 0:
                # columns 0 and 1 are the price data for the two coins
                data['LongAt_sym2'].iloc[i] = data.iloc[i, 1]
                data['LongCoin'].iloc[i] = 1
                data['ShortAt_sym1'].iloc[i] = data.iloc[i, 0]
            if data['Zscore'].iloc[i] < 0:
                data['LongAt_sym1'].iloc[i] = data.iloc[i, 0]
                data['LongCoin'].iloc[i] = 0
                data['ShortAt_sym2'].iloc[i] = data.iloc[i, 1]

    return data


def calculate_returns(data):
    """
    Given a certain starting capital calculates the resulting end capital 
    if we followed the strategy for the given data time period.

    Assumptions: 
    - All limit orders get filled every time (usually not the case)
    - Every time there is a trigger we put exactly half of the remaining capital in short/long
    - slippage / rebates not considered
    """
    data['Capital'] = 1000
    data['profit_sym1'] = 500
    data['profit_sym2'] = 500

    # first, calculate percentage return for each trade
    capital = data['Capital'].iloc[0]
    profit_sym1 = data['profit_sym1'].iloc[0]
    profit_sym2 = data['profit_sym2'].iloc[0]
    for i in range(1, len(data)):
        return_long = 1
        return_short = 1
        if data['LongCoin'].iloc[i] == 0:
            return_long = data['NextPrice_sym1'].iloc[i] / \
                data['LongAt_sym1'].iloc[i]
            return_short = data['ShortAt_sym2'].iloc[i] / \
                data['NextPrice_sym2'].iloc[i]
            profit_sym1 = profit_sym1 * return_long
            profit_sym2 = profit_sym2 * return_short

        if data['LongCoin'].iloc[i] == 1:
            return_long = data['NextPrice_sym2'].iloc[i] / \
                data['LongAt_sym2'].iloc[i]
            return_short = data['ShortAt_sym1'].iloc[i] / \
                data['NextPrice_sym1'].iloc[i]
            profit_sym1 = profit_sym1 * return_short
            profit_sym2 = profit_sym2 * return_long

        capital = (capital / 2) * return_long + (capital / 2) * return_short
        data['Capital'].iloc[i] = capital
        data['profit_sym1'].iloc[i] = profit_sym1
        data['profit_sym2'].iloc[i] = profit_sym2

    return data


def plot_results(df):
    import matplotlib
    # this allows plot window to appear when run from streamlit
    matplotlib.use('TkAgg')
    """
    Will plot two subgraphs:
    - price curves (in percent change) for the two symbols
        - red markers: opening short order
        - green markers: opening long order
        - black markers: closing all positions
    - profit over time (total, and for each of the symbols)
    """
    sym1_perc = df.iloc[:, 0] / df.iloc[0, 0]
    sym2_perc = df.iloc[:, 1] / df.iloc[0, 1]

    fig, axs = plt.subplots(2, figsize=(10, 6))

    axs[0].plot(sym1_perc)
    axs[0].plot(sym2_perc)
    axs[0].set_ylabel("price [%]")

    axs[1].plot(df['profit_sym1'] - 500)
    axs[1].plot(df['profit_sym2'] - 500)
    axs[1].plot(df['Capital'] - 1000)
    axs[1].set_ylabel("Profit [USDT]")

    long_sym1 = df[df['LongAt_sym1'] > 0].index
    short_sym1 = df[df['ShortAt_sym1'] > 0].index
    long_sym2 = df[df['LongAt_sym2'] > 0].index
    short_sym2 = df[df['ShortAt_sym2'] > 0].index

    close_points = df[df['NextClose'] > 0]['NextClose'].tolist()

    axs[0].scatter(close_points, sym1_perc[close_points], s=30, c='black',
                   linewidth=0)
    axs[0].scatter(close_points, sym2_perc[close_points], s=30, c='black',
                   linewidth=0)

    for i in long_sym1:
        axs[0].scatter(i, sym1_perc[i], s=30, c='green',
                       linewidth=0)
    for i in short_sym1:
        axs[0].scatter(i, sym1_perc[i], s=30, c='red',
                       linewidth=0)

    for i in long_sym2:
        axs[0].scatter(i, sym2_perc[i], s=30, c='green',
                       linewidth=0)
    for i in short_sym2:
        axs[0].scatter(i, sym2_perc[i], s=30, c='red',
                       linewidth=0)

    plt.show()
    return fig


# def run_backtest(threshold, filename="3_backtest_file.csv"):
#     df = load_backtest_file(filename)
#     df = find_zero_crossings(df)
#     df = find_triggers(df, threshold)

#     # find long coin for positive z-score:
#     df_0 = calculate_orders(df, 0)
#     df_1 = calculate_orders(df, 1)
#     df_0 = calculate_returns(df_0)
#     df_1 = calculate_returns(df_1)
#     if df_0['Capital'].iloc[-1] > df_1['Capital'].iloc[-1]:
#         df = df_0
#     else:
#         df = df_1

#     fig = plot_results(df)

#     return fig, df


def run_backtest(threshold, filename="3_backtest_file.csv", find_best=True):
    df = load_backtest_file(filename)
    df = find_zero_crossings(df)
    df = find_triggers(df, threshold)

    # find long coin for positive z-score:
    df_0 = calculate_orders(df, 0)
    df_1 = calculate_orders(df, 1)
    df_0 = calculate_returns(df_0)
    df_1 = calculate_returns(df_1)
    if df_0['Capital'].iloc[-1] > df_1['Capital'].iloc[-1]:
        df = df_0
        long_sym = 0
    else:
        df = df_1
        long_sym = 1

    fig = plot_results(df)

    # Find optimal threshold within certain range
    best_threshold = np.nan
    if find_best:
        threshold_dict = {1: 0, 1.1: 0, 1.2: 0, 1.3: 0,
                          1.4: 0, 1.5: 0, 1.6: 0, 1.7: 0, 1.8: 0, 1.9: 0}

        for threshold in threshold_dict.keys():
            df = find_triggers(df, threshold)
            df = calculate_orders(df, long_sym)
            df = calculate_returns(df)
            threshold_dict[threshold] = df['Capital'].iloc[-1]

        print(threshold_dict)
        best_threshold = max(threshold_dict, key=threshold_dict.get)
        print(best_threshold)

    return fig, df, best_threshold


# run_backtest(1.1, filename="3_backtest_file.csv", find_best=True)
