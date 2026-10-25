"""
Membership Calculator Tool — Computes total membership cost with discounts.
Useful for: "How much would 6 months of Premium cost?", "Student discount on Standard plan?"
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger("fitzone.tools.calculator")

# FitZone membership pricing (sourced from domain documents)
PLANS = {
    "basic": {
        "name": "Basic Plan",
        "monthly_rate": 4000,
        "registration_fee": 2000,
        "includes": "Gym floor, free weights, cardio equipment, locker rooms",
    },
    "standard": {
        "name": "Standard Plan",
        "monthly_rate": 6000,
        "registration_fee": 2000,
        "includes": "Basic + unlimited group fitness classes (Yoga, HIIT, Strength, Zumba)",
    },
    "premium": {
        "name": "Premium Plan",
        "monthly_rate": 9000,
        "registration_fee": 2000,
        "includes": "Standard + 4 PT sessions/month, sauna, steam room, 2 guest passes/month",
    },
    "student": {
        "name": "Student Plan",
        "monthly_rate": 3000,
        "registration_fee": 1500,
        "includes": "Off-peak hours gym floor access (10 AM - 4 PM weekdays)",
    },
    "corporate": {
        "name": "Corporate Wellness Plan",
        "monthly_rate": 5000,
        "registration_fee": 0,
        "includes": "Standard plan benefits billed through employer",
    },
    "senior": {
        "name": "Senior Citizen Plan",
        "monthly_rate": 3500,
        "registration_fee": 1000,
        "includes": "Full access with guided senior mobility classes",
    },
    "couples": {
        "name": "Couples / Family Package",
        "monthly_rate": 7000,
        "registration_fee": 3000,
        "includes": "Two Standard memberships at discounted combined rate",
    },
    "off-peak": {
        "name": "Off-Peak Hours Pass",
        "monthly_rate": 2500,
        "registration_fee": 1000,
        "includes": "Gym floor access during off-peak hours only",
    },
    "weekend": {
        "name": "Weekend Warrior Membership",
        "monthly_rate": 3000,
        "registration_fee": 1500,
        "includes": "Full access on Saturdays and Sundays only",
    },
    "vip": {
        "name": "VIP Executive Access",
        "monthly_rate": 15000,
        "registration_fee": 5000,
        "includes": "All amenities, private locker, priority booking, dedicated trainer",
    },
}

# Annual commitment gives 15% discount (documented in MEM-04)
ANNUAL_DISCOUNT_PERCENT = 15
STUDENT_DISCOUNT_PERCENT = 10


class MembershipCalculatorTool:
    """Calculates total membership cost including registration, monthly fees, and discounts."""

    name = "calculate_membership"
    description = (
        "Calculates the total cost of a FitZone Gym membership based on plan type, "
        "duration in months, and applicable discounts (student, annual commitment). "
        "Returns an itemized cost breakdown in Pakistani Rupees (Rs.)."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "plan": {
                "type": "string",
                "description": (
                    "Membership plan name. One of: basic, standard, premium, student, "
                    "corporate, senior, couples, off-peak, weekend, vip."
                ),
                "enum": list(PLANS.keys()),
            },
            "months": {
                "type": "integer",
                "description": "Number of months to calculate for (1-24).",
                "minimum": 1,
                "maximum": 24,
            },
            "student_discount": {
                "type": "boolean",
                "description": "Whether to apply the 10% student discount (requires valid student ID).",
                "default": False,
            },
        },
        "required": ["plan", "months"],
    }

    async def execute(self, arguments: Dict[str, Any] | None = None, **kwargs) -> Dict[str, Any]:
        """Computes an itemized cost breakdown for the requested membership."""
        args = dict(arguments or {})
        args.update(kwargs)
        plan_key = str(args.get("plan", "")).lower().strip()
        months = args.get("months", 1)
        student_discount = args.get("student_discount", False)

        # Validate plan
        if plan_key not in PLANS:
            available = ", ".join(PLANS.keys())
            return {
                "success": False,
                "error": f"Unknown plan '{plan_key}'. Available plans: {available}",
            }

        # Validate months
        try:
            months = int(months)
            if months < 1 or months > 24:
                raise ValueError
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": "Months must be an integer between 1 and 24.",
            }

        plan = PLANS[plan_key]
        monthly_rate = plan["monthly_rate"]
        registration_fee = plan["registration_fee"]

        # Calculate base cost
        subtotal_monthly = monthly_rate * months

        # Apply annual commitment discount (15% off monthly rates for 12+ months)
        annual_discount_amount = 0
        if months >= 12:
            annual_discount_amount = round(subtotal_monthly * ANNUAL_DISCOUNT_PERCENT / 100)

        # Apply student discount (additional 10% off)
        student_discount_amount = 0
        if student_discount:
            remaining = subtotal_monthly - annual_discount_amount
            student_discount_amount = round(remaining * STUDENT_DISCOUNT_PERCENT / 100)

        total_discounts = annual_discount_amount + student_discount_amount
        total_cost = registration_fee + subtotal_monthly - total_discounts

        return {
            "success": True,
            "plan_name": plan["name"],
            "includes": plan["includes"],
            "months": months,
            "monthly_rate_rs": monthly_rate,
            "registration_fee_rs": registration_fee,
            "subtotal_monthly_rs": subtotal_monthly,
            "annual_discount_applied": months >= 12,
            "annual_discount_rs": annual_discount_amount,
            "student_discount_applied": student_discount,
            "student_discount_rs": student_discount_amount,
            "total_discounts_rs": total_discounts,
            "total_cost_rs": total_cost,
            "per_month_effective_rs": round(
                (total_cost - registration_fee) / months
            ) if months > 0 else monthly_rate,
            "currency": "PKR (Pakistani Rupees)",
        }
