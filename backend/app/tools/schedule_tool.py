"""
Class Schedule Tool — Queries FitZone class schedules by day and/or class type.
Useful for: "What classes are available on Monday?", "When is the next Yoga class?"
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fitzone.tools.schedule")

# Complete FitZone class schedule (sourced from domain CLS-01 through CLS-15 documents)
CLASS_SCHEDULE: List[Dict[str, Any]] = [
    {
        "class_id": "CLS-01",
        "name": "Vinyasa Yoga Flow",
        "type": "yoga",
        "days": ["monday", "wednesday", "friday"],
        "time": "6:00 PM - 7:00 PM",
        "location": "Studio A (Mind & Body Studio)",
        "instructor": "Sarah Ali",
        "intensity": "Moderate (Level 2)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-02",
        "name": "Yin Restorative Yoga",
        "type": "yoga",
        "days": ["tuesday", "thursday"],
        "time": "10:00 AM - 11:00 AM",
        "location": "Studio A (Mind & Body Studio)",
        "instructor": "Sarah Ali",
        "intensity": "Low (Level 1)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-03",
        "name": "Power Yoga Flow",
        "type": "yoga",
        "days": ["saturday"],
        "time": "9:00 AM - 10:00 AM",
        "location": "Studio A (Mind & Body Studio)",
        "instructor": "Sarah Ali",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-04",
        "name": "HIIT Cardio Burn",
        "type": "hiit",
        "days": ["tuesday", "thursday"],
        "time": "7:00 PM - 7:45 PM",
        "location": "Studio B (Performance Studio)",
        "instructor": "Usman Malik",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-05",
        "name": "HIIT Tabata Intervals",
        "type": "hiit",
        "days": ["monday", "wednesday", "friday"],
        "time": "7:00 AM - 7:30 AM",
        "location": "Studio B (Performance Studio)",
        "instructor": "Usman Malik",
        "intensity": "Very High (Level 4)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-06",
        "name": "Strength & Conditioning",
        "type": "strength",
        "days": ["monday", "wednesday"],
        "time": "8:00 PM - 9:00 PM",
        "location": "Weight Room Studio",
        "instructor": "Ahmed Khan",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-07",
        "name": "Olympic Weightlifting Fundamentals",
        "type": "strength",
        "days": ["saturday"],
        "time": "11:00 AM - 12:30 PM",
        "location": "Olympic Platform Zone",
        "instructor": "Ahmed Khan",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-08",
        "name": "Zumba Cardio Dance",
        "type": "zumba",
        "days": ["saturday"],
        "time": "5:00 PM - 6:00 PM",
        "location": "Studio A",
        "instructor": "Guest Instructor",
        "intensity": "Moderate (Level 2)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-09",
        "name": "Mat Pilates Core",
        "type": "pilates",
        "days": ["tuesday", "thursday"],
        "time": "5:30 PM - 6:30 PM",
        "location": "Studio A (Mind & Body Studio)",
        "instructor": "Elena Rostova",
        "intensity": "Moderate (Level 2)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-10",
        "name": "Reformer Pilates Studio",
        "type": "pilates",
        "days": ["monday", "wednesday", "friday"],
        "time": "9:00 AM - 10:00 AM",
        "location": "Pilates Reformer Room",
        "instructor": "Elena Rostova",
        "intensity": "Moderate (Level 2)",
        "membership_required": "Premium or VIP",
    },
    {
        "class_id": "CLS-11",
        "name": "Spin & Rhythm Cycling",
        "type": "cycling",
        "days": ["monday", "wednesday", "friday"],
        "time": "6:30 AM - 7:15 AM",
        "location": "Spin Studio",
        "instructor": "Usman Malik",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-12",
        "name": "Boxing & Kickboxing Conditioning",
        "type": "boxing",
        "days": ["tuesday", "thursday", "saturday"],
        "time": "6:00 PM - 7:00 PM",
        "location": "Studio B (Performance Studio)",
        "instructor": "Tariq Vance",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-13",
        "name": "Kettlebell Functional Movement",
        "type": "strength",
        "days": ["tuesday", "thursday"],
        "time": "8:00 AM - 8:45 AM",
        "location": "Functional Turf Zone",
        "instructor": "Farhan Qureshi",
        "intensity": "High (Level 3)",
        "membership_required": "Standard or above",
    },
    {
        "class_id": "CLS-14",
        "name": "Senior Mobility & Balance",
        "type": "mobility",
        "days": ["monday", "wednesday", "friday"],
        "time": "10:00 AM - 11:00 AM",
        "location": "Studio A (Mind & Body Studio)",
        "instructor": "Dr. Zoya Merchant",
        "intensity": "Low (Level 1)",
        "membership_required": "Senior or above",
    },
    {
        "class_id": "CLS-15",
        "name": "Aqua Fitness & Swimming Clinic",
        "type": "aqua",
        "days": ["monday", "wednesday", "saturday"],
        "time": "4:00 PM - 5:00 PM",
        "location": "25m Indoor Pool",
        "instructor": "Guest Coach",
        "intensity": "Moderate (Level 2)",
        "membership_required": "Standard or above",
    },
]

# Valid class types for lookup
VALID_CLASS_TYPES = sorted(set(c["type"] for c in CLASS_SCHEDULE))
VALID_DAYS = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


class ClassScheduleTool:
    """Queries the FitZone class schedule by day and/or class type."""

    name = "check_class_schedule"
    description = (
        "Queries the FitZone Gym group fitness class schedule. "
        "Can filter by day of the week (e.g., 'monday') and/or class type "
        "(e.g., 'yoga', 'hiit', 'strength', 'pilates', 'cycling', 'boxing', 'zumba'). "
        "Returns matching classes with times, locations, and instructors."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "class_type": {
                "type": "string",
                "description": (
                    f"Filter by class type. Options: {', '.join(VALID_CLASS_TYPES)}. "
                    "Leave empty or set to 'all' to show all class types."
                ),
            },
            "day_of_week": {
                "type": "string",
                "description": (
                    "Filter by day of the week (e.g., 'monday', 'tuesday'). "
                    "Leave empty or set to 'all' to show all days."
                ),
            },
        },
        "required": [],
    }

    async def execute(self, arguments: Dict[str, Any] | None = None, **kwargs) -> Dict[str, Any]:
        """Filters and returns matching class schedule entries."""
        args = dict(arguments or {})
        args.update(kwargs)
        class_type = str(args.get("class_type", "all")).lower().strip()
        day_of_week = str(args.get("day_of_week", "all")).lower().strip()

        results = CLASS_SCHEDULE

        # Filter by class type
        if class_type and class_type not in ("all", "any", ""):
            # Fuzzy match: allow partial matches like "yoga" matching "yoga"
            results = [
                c for c in results
                if class_type in c["type"] or class_type in c["name"].lower()
            ]

        # Filter by day
        if day_of_week and day_of_week not in ("all", "any", ""):
            # Normalize day name
            day_normalized = day_of_week.lower().strip()
            # Handle abbreviations
            day_map = {
                "mon": "monday", "tue": "tuesday", "tues": "tuesday",
                "wed": "wednesday", "thu": "thursday", "thurs": "thursday",
                "fri": "friday", "sat": "saturday", "sun": "sunday",
            }
            day_normalized = day_map.get(day_normalized, day_normalized)
            results = [c for c in results if day_normalized in c["days"]]

        if not results:
            return {
                "success": True,
                "message": f"No classes found matching type='{class_type}', day='{day_of_week}'.",
                "classes": [],
                "total_found": 0,
                "filters_applied": {"class_type": class_type, "day_of_week": day_of_week},
                "available_types": VALID_CLASS_TYPES,
            }

        formatted = []
        for c in results:
            formatted.append({
                "class_id": c["class_id"],
                "name": c["name"],
                "type": c["type"],
                "days": ", ".join(d.capitalize() for d in c["days"]),
                "time": c["time"],
                "location": c["location"],
                "instructor": c["instructor"],
                "intensity": c["intensity"],
                "membership_required": c["membership_required"],
            })

        return {
            "success": True,
            "classes": formatted,
            "total_found": len(formatted),
            "filters_applied": {"class_type": class_type, "day_of_week": day_of_week},
        }
