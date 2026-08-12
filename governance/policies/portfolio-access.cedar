permit (
    principal == User::"PM_USER",
    action == Action::"access",
    resource == Portfolio::"PORT_A"
);

permit (
    principal == User::"RISK_USER",
    action == Action::"access",
    resource
);

permit (
    principal == User::"ADMIN_USER",
    action == Action::"access",
    resource
);
