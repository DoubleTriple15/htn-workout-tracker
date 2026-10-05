"""Fitness calculations used by the HTN app."""

from __future__ import annotations


def bmi(weight_kg: float, height_cm: float) -> float:
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive.")
    height_m = height_cm / 100.0
    return weight_kg / (height_m * height_m)


def bmi_category(value: float) -> str:
    if value < 18.5:
        return "Underweight"
    if value < 25:
        return "Normal"
    if value < 30:
        return "Overweight"
    return "Obesity"


def ffmi(weight_kg: float, height_cm: float, body_fat_pct: float) -> float:
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive.")
    if not 0 <= body_fat_pct < 100:
        raise ValueError("Body fat percentage must be between 0 and 100.")
    lean_mass = weight_kg * (1 - body_fat_pct / 100.0)
    height_m = height_cm / 100.0
    return lean_mass / (height_m * height_m)


def ffmi_category(value: float) -> str:
    if value < 18:
        return "Below average"
    if value < 20:
        return "Average"
    if value < 22:
        return "Above average"
    if value < 25:
        return "Advanced"
    return "Very high"


def bmr_mifflin(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
) -> float:
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Weight, height, and age must be positive.")

    s = str(sex).strip().lower()
    if s == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    if s == "female":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    raise ValueError("Sex must be Male or Female for this calorie estimate.")


ACTIVITY_FACTORS = {
    "Sedentary": 1.20,
    "Lightly active": 1.375,
    "Moderately active": 1.55,
    "Very active": 1.725,
    "Extra active": 1.90,
}

# Keep the labels used by the Profile/Home dropdowns in one place.
GOAL_ADJUSTMENTS = {
    "Lose weight": -300,
    "Maintain": 0,
    "Gain muscle": 250,
}

# Short labels used by Home.py when displaying the active goal.
GOAL_SHORT_LABELS = {
    "Lose weight": "Lose weight",
    "Maintain": "Maintain",
    "Gain muscle": "Gain muscle",
}


def _normalize_goal(goal: str) -> str:
    """Normalize common goal text so Profile/Home use the same keys."""
    if goal is None:
        raise ValueError("Goal is required.")

    text = str(goal).strip()
    aliases = {
        "gain": "Gain muscle",
        "gain muscle": "Gain muscle",
        "build muscle": "Gain muscle",
        "bulk": "Gain muscle",
        "maintain": "Maintain",
        "maintenance": "Maintain",
        "maintain weight": "Maintain",
        "lose": "Lose weight",
        "lose weight": "Lose weight",
        "cut": "Lose weight",
        "weight loss": "Lose weight",
    }
    normalized = aliases.get(text.lower())
    if normalized:
        return normalized

    # Preserve the exact public labels too.
    if text in GOAL_ADJUSTMENTS:
        return text

    raise ValueError(f"Unknown goal: {goal!r}")


def calorie_goal(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity_level: str,
    goal: str,
) -> int:
    if activity_level not in ACTIVITY_FACTORS:
        raise ValueError(f"Unknown activity level: {activity_level!r}")

    normalized_goal = _normalize_goal(goal)
    bmr = bmr_mifflin(weight_kg, height_cm, age, sex)
    maintenance = bmr * ACTIVITY_FACTORS[activity_level]
    adjustment = GOAL_ADJUSTMENTS[normalized_goal]
    return max(1000, round(maintenance + adjustment))


def kg_to_lbs(value: float) -> float:
    return float(value) * 2.2046226218


def lbs_to_kg(value: float) -> float:
    return float(value) / 2.2046226218


def cm_to_ft_in(value_cm: float) -> tuple[int, float]:
    total_inches = float(value_cm) / 2.54
    feet = int(total_inches // 12)
    inches = total_inches - feet * 12
    return feet, inches


def ft_in_to_cm(feet: int, inches: float) -> float:
    if int(feet) < 0 or float(inches) < 0:
        raise ValueError("Height values cannot be negative.")
    if float(inches) >= 12:
        raise ValueError("Inches must be below 12.")
    return (int(feet) * 12 + float(inches)) * 2.54
