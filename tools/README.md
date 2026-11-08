# Third-party tools kept in this repo

## tradingview-mcp

- **Source:** https://github.com/tradesdontlie/tradingview-mcp (MIT licence, see its LICENSE)
- **Copied:** 8 November 2026, upstream commit `c05b8f5`, without its `.git` folder
- **What it is:** an MCP server (84 tools) that lets Claude Code read and drive the
  **TradingView Desktop app** on this Mac through Chrome's debugging port 9222. It can
  inject and compile Pine scripts, change symbol and timeframe, read indicator values,
  and read Strategy Tester results (`data_get_strategy_results`, `data_get_trades`,
  `data_get_equity`) plus take screenshots.
- **What it needs:** TradingView Desktop installed and launched with
  `--remote-debugging-port=9222` (use `scripts/launch_tv_debug_mac.sh`), Node 18+,
  and `npm install` run in this folder (`node_modules/` is not committed).
- **Registered in:** `.mcp.json` at the repo root. Claude Code loads it on start-up.
- **Install state (8 Nov 2026):** `npm install --omit=dev --ignore-scripts`, then
  `npm audit fix` (MCP SDK moved to 1.32.2 inside the allowed range; 0 vulnerabilities
  remain; `package-lock.json` changed accordingly). Offline tests: 81 pass. The server
  starts and registers 84 tools. Live connection not yet verified: TradingView Desktop is
  not installed on this Mac.
- **Network note:** chart data stays local, but a few tools call TradingView web
  endpoints through the app's own logged-in session (price alerts, saved Pine scripts,
  symbol search, the server-side Pine compile check). Review the upstream README's
  disclaimer; TradingView's terms restrict automated use.
- **Its `CLAUDE.md`** is the upstream author's guidance on which tool to use when. It is
  reference material, not instructions for this project.
- **To update:** re-clone upstream into a scratch folder and copy over this one with
  `rsync -a --exclude .git`, then update the commit hash above and re-run `npm install`.
