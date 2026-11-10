"""Anchored-VWAP pullback strategy: PhenLabs' "Anchored VWAP Pullback & Target Zones" indicator
(pvnt_bot/AVPT_PhenLabs_indicator.pine, MPL 2.0) rebuilt as a strategy. Research only. The rules and
every deliberate difference from the indicator are written in research/SPEC_avwap_pullback.md; keep
the two in step. The indicator runs straight through session breaks, as on a chart.

Interface as engine.Strategy: on_bar(bar) -> proposal dict or None, plus check_exit(position, bar) so
the Engine closes a trade at the bar whose opposite signal flips the indicator's plan. All seven
profile engines run in parallel exactly as in the indicator (the anchors are shared and the anchor
rule reads the Balanced profile's counter); only the chosen profile proposes trades. The plan's
lifetime is tracked here as the indicator tracks it, so every leg of the same run proposes the same
entries. This module never places orders.

Settings (optional, from the config dict), all with the indicator's defaults:
  av_profile         0 Balanced (default), 1 Conservative, 2 Aggressive, 3 Shallow Pullback,
                     4 Deep Value Reclaim, 5 Volume Climax, 6 Custom
  av_leg             'tp1' (target 1R, no break-even), 'tp2' or 'tp3' (that target, stop to the entry
                     once price trades a tick through TP1); default 'tp3'
  av_target_mode     'hybrid' (R ladder with the impulse magnet, default) or 'ladder' (1R/2R/3R)
  av_swing_len 10    av_max_pb 2    av_min_impulse_atr 1.4    av_sl_buffer_atr 0.2    av_breakeven true
  av_custom_er 26.0  av_custom_sigma 1.0
  av_session         false = version A, as published; true = version B: proposals only between
                     entry_start and entry_end, plans end at flatten_time
  max_hold_bars      the plan's expiry in bars (60), shared with the Engine's time stop
"""
from collections import deque, Counter
from zoneinfo import ZoneInfo
import math

# id: (name, band sigma, outer sigma, min efficiency %, min quality, stop scale, min risk ATR, min relative volume)
PROFILES = {
    0: ('Balanced', 1.00, 2.00, 26.0, 52.0, 1.00, 0.35, 0.00),
    1: ('Conservative', 0.80, 1.75, 35.0, 60.0, 1.15, 0.35, 0.00),
    2: ('Aggressive', 1.25, 2.30, 18.0, 44.0, 0.85, 0.30, 0.00),
    3: ('Shallow Pullback', 0.65, 1.60, 30.0, 55.0, 0.90, 0.30, 0.00),
    4: ('Deep Value Reclaim', 1.45, 2.50, 22.0, 48.0, 1.25, 0.40, 0.00),
    5: ('Volume Climax', 1.00, 2.00, 24.0, 58.0, 0.95, 0.32, 1.25),
    6: ('Custom', 1.00, 2.00, 26.0, 50.0, 1.00, 0.35, 0.00),
}


def _clamp(v, lo, hi): return min(max(v, lo), hi)
def _round1(x): return math.floor(x * 10 + 0.5) / 10      # Pine math.round(x, 1) for x >= 0


class _Eng:
    """One profile: its thresholds, its pullback zones and its open plan."""
    def __init__(self, name, band, outer, min_er, min_qual, sl_scale, min_risk_atr, min_rel_act):
        self.name, self.band, self.outer, self.min_er, self.min_qual = name, band, outer, min_er, min_qual
        self.sl_scale, self.min_risk_atr, self.min_rel_act = sl_scale, min_risk_atr, min_rel_act
        self.bull_zone = False; self.bull_pb_low = None; self.bull_used = 0
        self.bear_zone = False; self.bear_pb_high = None; self.bear_used = 0
        self.plan = None


class AvwapPullbackStrategy:
    def __init__(self, c):
        self.c = c; self.tick = c['tick_size']; self.tz = ZoneInfo(c['timezone'])
        self.swing = int(c.get('av_swing_len', 10)); self.max_pb = int(c.get('av_max_pb', 2))
        self.min_imp = float(c.get('av_min_impulse_atr', 1.4)); self.sl_buf = float(c.get('av_sl_buffer_atr', 0.2))
        self.use_be = bool(c.get('av_breakeven', True)); self.expire = int(c.get('max_hold_bars', 60))
        self.hybrid = c.get('av_target_mode', 'hybrid') == 'hybrid'
        self.profile = int(c.get('av_profile', 0)); self.leg = c.get('av_leg', 'tp3')
        if self.leg not in ('tp1', 'tp2', 'tp3'): raise ValueError('av_leg must be tp1, tp2 or tp3')
        self.session = bool(c.get('av_session', False))
        sigma = float(c.get('av_custom_sigma', 1.0)); er = float(c.get('av_custom_er', 26.0))
        rows = dict(PROFILES); rows[6] = ('Custom', sigma, sigma + 1.0, er, 50.0, 1.00, 0.35, 0.00)
        self.engs = [_Eng(*rows[k]) for k in range(7)]
        # attributes the Engine touches on gaps/new days (compatibility only; the indicator state lives below)
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.hist = deque(maxlen=max(64, 2 * self.swing + 2)); self.i = 0
        self.atr = None; self.trs = deque(maxlen=14); self.vols = deque(maxlen=20); self.moves = deque(maxlen=10)
        self.bull = None; self.bear = None          # the shared anchors: dicts, or None while inactive
        self.last_side = None                       # side proposed on the current bar, read by check_exit
        self.stats = Counter()                      # read by the research runner

    # ------------------------------------------------------------------ helpers
    def _tick_round(self, x): return round(x / self.tick) * self.tick

    def _end(self, e, label, status):
        e.plan['status'] = status
        if e is self.engs[self.profile]: self.stats[label] += 1

    def _seed(self, b, hist, n, pivot, side, atr, real_vol):
        """The indicator's exact reconstruction of the anchored VWAP from the pivot bar to this bar."""
        swp = swp2 = sw = 0.0; ext = b.high if side == 1 else b.low
        for k in range(n, -1, -1):
            x = hist[-k] if k else b
            span_k = max(x.high - x.low, self.tick)
            wk = max(x.volume, 1e-6) if real_vol else max(span_k / max(atr, self.tick), 0.1)
            pk = (x.high + x.low + x.close) / 3
            swp += wk * pk; swp2 += wk * pk * pk; sw += wk
            if side == 1 and x.high >= ext: ext = x.high
            if side == -1 and x.low <= ext: ext = x.low
        avwap = swp / max(sw, 1e-9)
        std = max(math.sqrt(max(0.0, swp2 / max(sw, 1e-9) - avwap * avwap)), atr * 0.25)
        return {'price': pivot, 'bar': self.i - 1 - n, 'swp': swp, 'swp2': swp2, 'sw': sw, 'avwap': avwap, 'std': std,
                'imp': ext, 'armed': side * (ext - pivot) >= self.min_imp * atr}

    # ------------------------------------------------------------------ the bar
    def on_bar(self, b):
        bar_index = self.i; self.i += 1; self.bars.append(b); self.last_side = None
        hist = self.hist; prev = hist[-1] if hist else None
        # --- section 3 of the indicator: volatility, activity, efficiency, quality
        tr = b.high - b.low if prev is None else max(b.high - b.low, abs(b.high - prev.close), abs(b.low - prev.close))
        if self.atr is None:
            self.trs.append(tr)
            if len(self.trs) == 14: self.atr = sum(self.trs) / 14          # seeded like Pine's rma()
        else:
            self.atr = (self.atr * 13 + tr) / 14
        atr = self.atr if self.atr is not None else max(b.high - b.low, self.tick * 10)
        span = max(b.high - b.low, self.tick)
        self.vols.append(b.volume); vol_sma = sum(self.vols) / 20 if len(self.vols) == 20 else None
        real_vol = b.volume > 0 and vol_sma is not None and vol_sma > 0
        rel_act = b.volume / vol_sma if real_vol else span / max(atr, self.tick)
        act_norm = _clamp(rel_act / 2, 0.0, 1.0)
        weight = max(b.volume, 1e-6) if real_vol else max(rel_act, 0.1)
        self.moves.append(abs(b.close - prev.close) if prev else 0.0)
        c10 = hist[-10].close if len(hist) >= 10 else b.close
        path = sum(self.moves) if len(self.moves) == 10 else 0.0
        er = _clamp(abs(b.close - c10) / path * 100, 0.0, 100.0) if path > 0 else 0.0
        er_norm = _clamp(er / 55, 0.0, 1.0)
        bull_q = _round1(_clamp((0.40 * _clamp((b.close - b.low) / span, 0, 1) + 0.35 * er_norm + 0.25 * act_norm) * 100 * (1.0 if b.close > b.open else 0.85), 0, 100))
        bear_q = _round1(_clamp((0.40 * _clamp((b.high - b.close) / span, 0, 1) + 0.35 * er_norm + 0.25 * act_norm) * 100 * (1.0 if b.close < b.open else 0.85), 0, 100))
        prev_high = prev.high if prev else b.high; prev_low = prev.low if prev else b.low
        c5 = hist[-5].close if len(hist) >= 5 else b.close
        move5 = (b.close - c5) / max(atr, self.tick)
        bear_crash = move5 < -3.6 and b.close < b.open; bull_crash = move5 > 3.6 and b.close > b.open
        in_window = True; flatten = False
        if self.session:
            clock = b.dt().astimezone(self.tz).strftime('%H:%M')
            in_window = self.c['entry_start'] <= clock < self.c['entry_end']; flatten = clock >= self.c['flatten_time']

        # --- step A: resolve the open plans (targets count one tick through, the stop on a touch)
        for e in self.engs:
            p = e.plan
            if p is None or p['status'] != 0: continue
            if flatten: self._end(e, 'plan: session flatten', 3); continue
            if bar_index <= p['entry_bar']: continue
            s = p['dir']; ext = b.high if s == 1 else b.low
            if s * (p['active_sl'] - (b.low if s == 1 else b.high)) >= 0:
                self._end(e, ('plan: break-even stop' if self.use_be else 'plan: stop after TP1') if p['tp1_hit'] else 'plan: stop', 2 if p['tp1_hit'] else -1); continue
            if not p['tp1_hit'] and s * (ext - p['tp1']) >= self.tick:
                p['tp1_hit'] = True
                if self.use_be: p['active_sl'] = p['entry']
            if not p['tp2_hit'] and s * (ext - p['tp2']) >= self.tick: p['tp2_hit'] = True
            if not p['tp3_hit'] and s * (ext - p['tp3']) >= self.tick:
                p['tp3_hit'] = True; self._end(e, 'plan: TP3', 1)
            elif bar_index - p['entry_bar'] >= self.expire:
                self._end(e, 'plan: expired after TP1' if p['tp1_hit'] else 'plan: expired', 2 if p['tp1_hit'] else 3)

        # --- step B: carry the active anchors forward with this bar
        hlc3 = (b.high + b.low + b.close) / 3
        for side in (1, -1):
            a = self.bull if side == 1 else self.bear
            if not a: continue
            a['swp'] += weight * hlc3; a['swp2'] += weight * hlc3 * hlc3; a['sw'] += weight
            a['avwap'] = a['swp'] / max(a['sw'], 1e-9)
            a['std'] = max(math.sqrt(max(0.0, a['swp2'] / max(a['sw'], 1e-9) - a['avwap'] * a['avwap'])), atr * 0.25)
            if side == 1 and b.high >= a['imp']: a['imp'] = b.high
            if side == -1 and b.low <= a['imp']: a['imp'] = b.low
            if not a['armed'] and side * (a['imp'] - a['price']) >= self.min_imp * atr: a['armed'] = True
            dead = (b.close < a['price'] or b.close < a['avwap'] - 2.6 * a['std']) if side == 1 else (b.close > a['price'] or b.close > a['avwap'] + 2.6 * a['std'])
            if dead:
                if side == 1:
                    self.bull = None
                    for e in self.engs: e.bull_zone = False
                else:
                    self.bear = None
                    for e in self.engs: e.bear_zone = False

        # --- step C: a confirmed swing seeds a new anchor (centre bar strictly beyond the 10 bars either side)
        n = self.swing
        if len(hist) >= 2 * n:
            cand = hist[-n]
            others = [hist[-k] for k in range(n + 1, 2 * n + 1)] + [b] + [hist[-k] for k in range(1, n)]
            bal = self.engs[0]
            if all(cand.low < x.low for x in others):
                pl = cand.low; a = self.bull
                replace = a is None or pl < a['price'] or bal.bull_used >= self.max_pb or (a['armed'] and pl > a['price'] and b.high - pl >= self.min_imp * atr)
                if replace and b.close > pl:
                    self.bull = self._seed(b, hist, n, pl, 1, atr, real_vol); self.stats['anchor long'] += 1
                    for e in self.engs: e.bull_zone = False; e.bull_pb_low = None; e.bull_used = 0
            if all(cand.high > x.high for x in others):
                ph = cand.high; a = self.bear
                replace = a is None or ph > a['price'] or bal.bear_used >= self.max_pb or (a['armed'] and ph < a['price'] and ph - b.low >= self.min_imp * atr)
                if replace and b.close < ph:
                    self.bear = self._seed(b, hist, n, ph, -1, atr, real_vol); self.stats['anchor short'] += 1
                    for e in self.engs: e.bear_zone = False; e.bear_pb_high = None; e.bear_used = 0

        # --- step D: pullback zones, reclaims and plans, every profile in parallel
        proposal = None
        for idx, e in enumerate(self.engs):
            p = e.plan; open_dir = p['dir'] if p and p['status'] == 0 else None
            take = 0; pb_level = None
            a = self.bull
            if a and a['armed'] and e.bull_used < self.max_pb:
                upper = a['avwap'] + e.band * a['std']; lower_def = a['avwap'] - e.outer * a['std']
                if b.low <= upper and b.close >= lower_def and b.close > a['price'] and b.high < a['imp']:
                    if not e.bull_zone: e.bull_zone = True; e.bull_pb_low = b.low
                    elif b.low < (e.bull_pb_low if e.bull_pb_low is not None else b.low): e.bull_pb_low = b.low
                elif b.close < lower_def:
                    e.bull_zone = False
                reclaim = e.bull_zone and b.close > a['avwap'] and b.close > b.open and b.close >= prev_high - 0.20 * atr
                if reclaim and open_dir != 1 and in_window:
                    pb_level = e.bull_pb_low if e.bull_pb_low is not None else b.low
                    depth = (a['imp'] - pb_level) / max(a['imp'] - a['price'], atr * 0.5)
                    if er >= e.min_er and bull_q >= e.min_qual and rel_act >= e.min_rel_act and 0.12 <= depth <= 0.85 and not bear_crash:
                        take = 1
                    else:
                        e.bull_zone = False
                        if idx == self.profile: self.stats['x skip long (filters)'] += 1
            a = self.bear
            if take == 0 and a and a['armed'] and e.bear_used < self.max_pb:
                lower = a['avwap'] - e.band * a['std']; upper_def = a['avwap'] + e.outer * a['std']
                if b.high >= lower and b.close <= upper_def and b.close < a['price'] and b.low > a['imp']:
                    if not e.bear_zone: e.bear_zone = True; e.bear_pb_high = b.high
                    elif b.high > (e.bear_pb_high if e.bear_pb_high is not None else b.high): e.bear_pb_high = b.high
                elif b.close > upper_def:
                    e.bear_zone = False
                reclaim = e.bear_zone and b.close < a['avwap'] and b.close < b.open and b.close <= prev_low + 0.20 * atr
                if reclaim and open_dir != -1 and in_window:
                    pb_level = e.bear_pb_high if e.bear_pb_high is not None else b.high
                    depth = (pb_level - a['imp']) / max(a['price'] - a['imp'], atr * 0.5)
                    if er >= e.min_er and bear_q >= e.min_qual and rel_act >= e.min_rel_act and 0.12 <= depth <= 0.85 and not bull_crash:
                        take = -1
                    else:
                        e.bear_zone = False
                        if idx == self.profile: self.stats['x skip short (filters)'] += 1
            if take == 0: continue
            # --- spawn the plan (a plan still open here is the opposite direction: the indicator flips it)
            if open_dir is not None: self._end(e, 'plan: flipped', 2 if p['tp1_hit'] else 3)
            s = take; a = self.bull if s == 1 else self.bear
            band_edge = a['avwap'] - s * e.band * a['std']
            raw_sl = (min(pb_level, band_edge) if s == 1 else max(pb_level, band_edge)) - s * self.sl_buf * e.sl_scale * atr
            risk = _clamp(abs(b.close - raw_sl), atr * e.min_risk_atr, atr * 3.0)
            entry = b.close
            tp = [entry + s * risk, entry + s * 2 * risk, entry + s * 3 * risk]; magnet = None
            if self.hybrid:
                dist_r = s * (a['imp'] - entry) / risk
                if 1.3 <= dist_r <= 2.4: tp[1] = a['imp']; magnet = 'tp2'
                elif 2.4 < dist_r <= 4.5: tp[2] = a['imp']; magnet = 'tp3'
            sl = self._tick_round(entry - s * risk)
            e.plan = {'dir': s, 'entry_bar': bar_index, 'entry': entry, 'init_sl': sl, 'active_sl': sl, 'risk': risk,
                      'tp1': self._tick_round(tp[0]), 'tp2': self._tick_round(tp[1]), 'tp3': self._tick_round(tp[2]),
                      'tp1_hit': False, 'tp2_hit': False, 'tp3_hit': False, 'status': 0, 'magnet': magnet}
            if s == 1: e.bull_zone = False; e.bull_used += 1
            else: e.bear_zone = False; e.bear_used += 1
            if idx == self.profile:
                plan = e.plan; self.last_side = s
                self.stats['signal long' if s == 1 else 'signal short'] += 1
                if magnet: self.stats['magnet on ' + magnet] += 1
                be_at = plan['tp1'] + s * self.tick if (self.leg != 'tp1' and self.use_be) else None
                proposal = {'side': s, 'stop': plan['init_sl'], 'target': plan[self.leg], 'breakeven_at': be_at,
                            'signal_time': b.timestamp, 'intended_side': s, 'signal_close': b.close,
                            'tp1': plan['tp1'], 'tp2': plan['tp2'], 'tp3': plan['tp3'], 'plan_risk': round(risk, 4), 'magnet': magnet,
                            'reason': f"AVWAP pullback {'long' if s == 1 else 'short'} ({e.name}, leg {self.leg})"}
        hist.append(b)
        return proposal

    def check_exit(self, position, b):
        """Called by the Engine after on_bar while a trade is open: a signal the other way on this bar flips
        the indicator's plan, so the trade leaves at this bar's close. Compares intended sides, so the
        random-direction control exits at the same bars."""
        s0 = position.get('intended_side', position['side'])
        return 'flip' if self.last_side is not None and self.last_side != s0 else None
