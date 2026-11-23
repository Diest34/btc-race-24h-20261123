# btc-race-24h-20261123

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/Diest34/btc-race-24h-20261123/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/Diest34/btc-race-24h-20261123/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A paper-money cbBTC trading bot for make.fun's 24-hour BTC race. It buys 0.8% dips below the 60-minute high in an uptrend (EMA 12 above EMA 48) on an uptick, exits at +1.2% take-profit or -0.8% stop-loss, and falls back to half-size 1.2% dip-buys when the trend is down so it keeps trading in a falling market. Local dev-window replay: net PnL +$28.17 on $1,000, 6 trades, max drawdown 0.79%.

## Run it

```sh
PYTHONHASHSEED=0 python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=nn10gehx&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
