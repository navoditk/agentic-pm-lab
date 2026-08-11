---
name: portfolio-risk-summary
description: Combine portfolio exposure, rolling volatility, and maximum drawdown into a concise PM-style risk summary grounded only in tool outputs.
license: MIT
covers:
  - src/agents/single_agent.py
  - src/analytics/portfolio.py
  - src/analytics/risk.py
last_verified_commit: 73a1ed3
---

# portfolio-risk-summary

Use this skill for questions asking what risks dominate a portfolio, how
volatile it has been, or how severe its observed losses were.

## Required workflow

1. Call `get_portfolio_exposure` for weights, asset-class/sector exposure, and
   concentration.
2. Call `get_volatility` with the supplied periodic returns and disclose its
   window and annualization assumption.
3. Call `get_max_drawdown` with the supplied portfolio-value history.
4. Synthesize the outputs into:
   - the largest exposures and concentrations;
   - current/latest measured volatility;
   - maximum drawdown with peak and trough positions;
   - explicit data limitations and no unsupported recommendations.

Never calculate or invent missing values in prose. The security-master
classification is mocked, so label sector and asset-class conclusions as
illustrative. Volatility and drawdown are historical measurements, not
forecasts.
