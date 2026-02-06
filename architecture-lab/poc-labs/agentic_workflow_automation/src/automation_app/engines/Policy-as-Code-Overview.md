# README – Updating Policies
## Policy-as-Code Overview

This system uses a deny-by-default Policy-as-Code engine.
All actions must be explicitly allowed by a policy rule.

## How to Add or Update Policies

Policies are defined in:
``` 
  config/policies.py
```
Each policy rule has the following structure:
``` 
    {
        "id": "UNIQUE-RULE-ID",
        "description": "Human-readable explanation",
        "effect": "allow" | "deny",
        "target": {
            "adapter": "AdapterName",
            "method": "method_name",
        },
        "conditions": {
            "roles": ["Role1", "Role2"],
            "departments": ["Dept1", "Dept2"],
        },
    }
```

## Example: Allow a New Action

To allow Managers to delete calendar events:
```
    {
        "id": "MSG-ALLOW-DELETE-CALENDAR",
        "description": "Managers may delete calendar events",
        "effect": "allow",
        "target": {
            "adapter": "MSGraph",
            "method": "delete_calendar_event",
        },
        "conditions": {
            "roles": ["Manager"],
        },
    }
```

## Example: Deny Rule

Deny rules override allows if matched:
```
{
    "id": "GLOBAL-DENY-INTERNS",
    "description": "Interns may not perform destructive actions",
    "effect": "deny",
    "target": {
        "adapter": "MSGraph",
        "method": "create_calendar_event",
    },
    "conditions": {
        "roles": ["Intern"],
    },
}
```
## Security Guarantees

* No rule → **action denied**
* Rules are **audited by ID**
* Supports future conditions (time windows, quotas, approval level)
* Compatible with HITL + async execution

## What You’ve Built (Important)

At this point your system has:
* **Saga execution**
* **Audit logging**
* **PII scrubbing** 
* **Async orchestration** 
* **Policy-as-Code with deny-by-default**

