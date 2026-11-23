"""cbBTC dip-buy bot for make.fun's "Race a BTC trading bot live for 24 hours".

Strategy (paper money, $1,000 start, long only, one open position):
- Trend filter: EMA(12) of 1-minute closes above EMA(48).
- Primary entry (uptrend): the close is at least 0.6% below the 60-bar high
  and ticks up from the previous close -> buy with all cash.
- Fallback entry (no uptrend): the close is at least 1.2% below the
  60-bar high and ticks up -> buy with half the cash. This keeps the bot
  trading (the race needs at least 1 trade) in a falling market while
  risking only half size there.
- Exit: take profit at +1.0% or stop loss at -1.0% from the average entry
  price (cost basis). After a stop loss, no new entry for 60 bars.
- Every order names max_slippage_bps 150 (1.5%) against the latest close.

Deterministic: integer fixed-point EMAs, no clock, no network, no files
outside the repository, no randomness. Standard library only, plus the
vendored kit shim in vendor/ (a byte-for-byte copy of the kit's SDK).

Protocol: agent-fun/bars-replay/v1, spoken through vendor/makefun_bars.py.
The grader runs: python3 -P -s /bot/main.py (PYTHONHASHSEED=0).
"""

import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# --- strategy parameters (bps where noted; 10000 bps = 100%) ---
EMA_FAST = 12
EMA_SLOW = 48
HISTORY_BARS = 60          # window for the dip reference high
DIP_BPS = 60               # 0.6% below the 60-bar high (uptrend entry)
DIP_CT_BPS = 120           # 1.2% below the 60-bar high (fallback entry)
TAKE_PROFIT_BPS = 100      # +1.0% from the average entry price
STOP_LOSS_BPS = 100        # -1.0% from the average entry price
COOLDOWN_BARS = 60         # no new entry for this many bars after a stop
MAX_SLIPPAGE_BPS = 150     # 1.5% against the latest close
MIN_HISTORY = EMA_SLOW + 2  # bars of history before the first entry

# Fixed-point scale for the integer EMAs.
_SCALE = 10 ** 6


class Bot:
    """One bot's state across the batches of a single run."""

    def __init__(self):
        self.closes = deque(maxlen=HISTORY_BARS)
        self.prev_close = None
        self.ema_fast = None
        self.ema_slow = None
        self.cool_until = -1
        self.seen = 0

    def _ema_update(self, close):
        # EMA: e = alpha * close + (1 - alpha) * e, alpha = 2 / (N + 1).
        # In fixed point: E = (2 * close * S + (N - 1) * E) // (N + 1).
        if self.ema_fast is None:
            self.ema_fast = close * _SCALE
            self.ema_slow = close * _SCALE
            return
        self.ema_fast = (2 * close * _SCALE + (EMA_FAST - 1) * self.ema_fast) // (EMA_FAST + 1)
        self.ema_slow = (2 * close * _SCALE + (EMA_SLOW - 1) * self.ema_slow) // (EMA_SLOW + 1)

    def entry_price(self, holding):
        # Average entry price (price-scale units) from the cost basis:
        # value(qty, price) = qty * price // 10**7, so price = cost * 10**7 // qty.
        if holding is None or holding.qty <= 0:
            return None
        return holding.cost * 10 ** 7 // holding.qty

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.seen += 1
        self._ema_update(close)
        self.closes.append(close)
        prev_close = self.prev_close
        self.prev_close = close

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0

        if qty > 0:
            entry = self.entry_price(holding)
            if entry is None:
                return []
            if close * 10_000 >= entry * (10_000 + TAKE_PROFIT_BPS):
                return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            if close * 10_000 <= entry * (10_000 - STOP_LOSS_BPS):
                self.cool_until = state.seq + COOLDOWN_BARS
                return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []

        # Flat: entries only with enough history and outside the cooldown.
        if self.seen < MIN_HISTORY or state.seq < self.cool_until:
            return []
        if prev_close is None or len(self.closes) < 2:
            return []
        uptrend = self.ema_fast > self.ema_slow
        high = max(self.closes)
        uptick = close >= prev_close
        if uptrend and uptick and close * 10_000 <= high * (10_000 - DIP_BPS):
            notional = state.cash
            if notional >= 1_000_000:
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": notional,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []
        if (not uptrend) and uptick and close * 10_000 <= high * (10_000 - DIP_CT_BPS):
            notional = state.cash // 2
            if notional >= 1_000_000:
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": notional,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            return []
        return []


def main():
    bot = Bot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
