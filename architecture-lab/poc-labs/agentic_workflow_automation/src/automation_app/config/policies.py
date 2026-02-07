POLICY_RULES = [

    # -------------------------------------------------
    # Workday
    # -------------------------------------------------

    {
        "id": "WD-ALLOW-PTO-HR-MGR-EMP",
        "description": "Allow HR, Manager, and Employees to create time off requests",
        "effect": "allow",
        "target": {
            "adapter": "Workday",
            "method": "create_time_off",
        },
        "conditions": {
            "roles": ["HR", "Manager", "Employee"],
            "departments": ["Engineering", "HR", "Sales"],
        },
    },

    # -------------------------------------------------
    # MS Graph
    # -------------------------------------------------

    {
        "id": "MSG-ALLOW-SEND-EMAIL",
        "description": "Allow employees and managers to send emails",
        "effect": "allow",
        "target": {
            "adapter": "MSGraph",
            "method": "send_email",
        },
        "conditions": {
            "roles": ["Employee", "Manager", "HR"],
        },
    },

    {
        "id": "MSG-ALLOW-CALENDAR-EVENT",
        "description": "Allow employees and managers to create calendar events",
        "effect": "allow",
        "target": {
            "adapter": "MSGraph",
            "method": "create_calendar_event",
        },
        "conditions": {
            "roles": ["Employee", "Manager"],
        },
    },

    {
        "id": "MSG-DENY-INTERN-EMAIL",
        "description": "Prevent interns from sending emails",
        "effect": "deny",
        "target": {
            "adapter": "MSGraph",
            "method": "send_email",
        },
        "conditions": {
            "roles": ["Intern"],
        },
    },
]
