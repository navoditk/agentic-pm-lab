permit (
    principal == Role::"pm",
    action == Action::"invoke",
    resource
)
when {
    resource == Tool::"price-bond" ||
    resource == Tool::"curve" ||
    resource == Tool::"research" ||
    resource == Tool::"econometrics" ||
    resource == Tool::"backtest" ||
    resource == Tool::"portfolio" ||
    resource == Tool::"risk" ||
    resource == Tool::"price_bond" ||
    resource == Tool::"price_option" ||
    resource == Tool::"interpolate_curve" ||
    resource == Tool::"get_portfolio_exposure" ||
    resource == Tool::"get_volatility" ||
    resource == Tool::"get_max_drawdown" ||
    resource == Tool::"get_risk_metrics" ||
    resource == Tool::"run_factor_regression" ||
    resource == Tool::"run_backtest" ||
    resource == Tool::"get_research_summary"
};

permit (
    principal == Role::"risk",
    action == Action::"invoke",
    resource
)
when {
    resource == Tool::"curve" ||
    resource == Tool::"econometrics" ||
    resource == Tool::"backtest" ||
    resource == Tool::"portfolio" ||
    resource == Tool::"risk" ||
    resource == Tool::"interpolate_curve" ||
    resource == Tool::"get_portfolio_exposure" ||
    resource == Tool::"get_volatility" ||
    resource == Tool::"get_max_drawdown" ||
    resource == Tool::"get_risk_metrics" ||
    resource == Tool::"run_factor_regression" ||
    resource == Tool::"run_backtest"
};

permit (
    principal == Role::"admin",
    action == Action::"invoke",
    resource
)
when {
    resource == Tool::"price-bond" ||
    resource == Tool::"curve" ||
    resource == Tool::"research" ||
    resource == Tool::"econometrics" ||
    resource == Tool::"backtest" ||
    resource == Tool::"portfolio" ||
    resource == Tool::"risk" ||
    resource == Tool::"price_bond" ||
    resource == Tool::"price_option" ||
    resource == Tool::"interpolate_curve" ||
    resource == Tool::"get_portfolio_exposure" ||
    resource == Tool::"get_volatility" ||
    resource == Tool::"get_max_drawdown" ||
    resource == Tool::"get_risk_metrics" ||
    resource == Tool::"run_factor_regression" ||
    resource == Tool::"run_backtest" ||
    resource == Tool::"get_research_summary"
};
