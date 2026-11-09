# Strategy spec: opening gap fade, version 1

Written 8 November 2026, before any run. Source: practitioner gap-fill statistics on ES and the
old Step 1 `gap_fade` v9 rule (4 Nov), which on 1 NQ contract with looser costs made +$36,045
2010–2020, 8 of 11 years positive, and passed that folder's random check. Those numbers are a
hint, not evidence. Times are Chicago (CT). **[grey]** marks a judgement call.

## Rules
- **Yesterday's close** = the close of the last bar that ends at or before 15:00 CT on the
  previous session (the cash close). **Today's open** = the open of the 08:30 CT bar.
- **Gap** = today's open minus yesterday's close. Trade only if |gap| ≥ **0.2%** of yesterday's
  close **[grey: the Step 1 value; 0.5% is a logged variant]**.
- **Direction**: against the gap. Gap up → short; gap down → long.
- **Signal** at the close of the 08:30 bar; **entry at the next bar's open** with 2 ticks
  slippage (08:31 on 1-minute bars, the primary; 08:35 on 5-minute bars, a variant).
- **Target** = yesterday's close (the gap fills). **Stop** = one gap-size beyond the open. Both
  are real orders: the target fills on a one-tick penetration, the stop fills intrabar with
  slippage (engine rules).
- **Flat by 10:30 CT** if neither has hit (engine flatten at the close of the 10:30 bar).
- No trade if the 08:30 bar has already run past the target or through the stop by its close
  (geometry guard, counted).
- One trade a day, fixed 1 contract, $0.75 per side, 2 ticks slippage. NQ as the MNQ proxy.

## Control
Same days, same stop and target distances, direction by coin toss (`random_direction`), 8 seeds.

## Expect
Step 1's cousin: 2018 and 2020 gave about $33,000 of the $36,000 and 2019 lost $10,945. With
micro costs the honest result may be smaller or negative.

## Acceptance (frozen)
Beats its control, profit factor above 1.0, positive in 6 of 11 years or more, after costs.
Only that earns 2021–2026, which is not run in this chat.

## Variants (rows 85–90)
85 sanity NQ 2020 1m · 86 primary 1m · 87 5m bars · 88 min gap 0.5% · 89 control · 90 zero costs
