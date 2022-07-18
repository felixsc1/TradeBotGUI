import re

# with open('scripts/Strategy/config_strategy_api.py', 'w+') as file:
#     filedata = file.read()
#     filedata = filedata.replace('timeframe = \w+', '60')
#     file.write(filedata)
#     # file.replace('timeframe = \w+', '60')


def replace_timeframe(timeframe):
    # modifies the config_strategy_api file
    # for availabe intervals, see: https://bybit-exchange.github.io/docs/linear/?python--pybit#tp-sl-mode-tp_sl_mode

    with open('scripts/Strategy/config_strategy_api.py', 'r') as file:
        filelines = file.readlines()
        for i, line in enumerate(filelines):
            if bool(re.search("timeframe =", line)):
                print(i, line)
                filelines[i] = f"timeframe = {timeframe}\n"

    with open('scripts/Strategy/config_strategy_api.py', 'w') as file:
        file.writelines(filelines)
