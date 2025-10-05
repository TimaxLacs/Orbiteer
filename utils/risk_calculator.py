import math

# Константы, используемые в формуле
# Rз (Радиус Земли, км)
R_EARTH_KM = 6371.0
# Количество секунд в одном году
SEC_PER_YEAR = 31536000
# Коэффициент для расчета страховой премии (150%)
INSURANCE_COEFFICIENT = 1.5


def assign_risk_class(collision_probability: float) -> str:
    """
    Присваивает класс риска на основе вероятности столкновения.
    """
    if collision_probability > 1e-2:  # > 1%
        return "F (Extremely High)"
    if collision_probability > 1e-3:  # > 0.1%
        return "E (Very High)"
    if collision_probability > 1e-4:  # > 0.01%
        return "D (High)"
    if collision_probability > 1e-5:  # > 0.001%
        return "C (Moderate)"
    if collision_probability > 1e-6:  # > 0.0001%
        return "B (Low)"
    if collision_probability > 1e-7:  # > 0.00001%
        return "A (Very Low)"
    return "A+ (Minimal)"


def calculate_collision_financial_risk(
    N_objects: float,
    H_upper: float,
    H_lower: float,
    V_rel: float,
    A_effective: float,
    T_years: float,
    C_full: float,
    D_lost: float,
) -> dict:
    """
    Рассчитывает ожидаемый финансовый риск (ФР) из-за столкновения
    космического аппарата с мусором за весь срок миссии.
    """
    R_upper = R_EARTH_KM + H_upper
    R_lower = R_EARTH_KM + H_lower
    V_shell = (4 / 3) * math.pi * (R_upper**3 - R_lower**3)

    if V_shell <= 0:
        return {"error": "Invalid altitude range, shell volume is zero or negative."}

    density = N_objects / V_shell
    T_seconds = T_years * SEC_PER_YEAR
    A_effective_km2 = A_effective / 1_000_000

    expected_collisions = density * V_rel * A_effective_km2 * T_seconds
    P_collision = 1.0 - math.exp(-expected_collisions)

    total_cost_at_risk = C_full + D_lost
    financial_risk = P_collision * total_cost_at_risk
    insurance_premium = financial_risk * INSURANCE_COEFFICIENT
    risk_class = assign_risk_class(P_collision)

    return {
        "financial_risk": round(financial_risk, 2),
        "collision_risk": P_collision,
        "insurance_premium": round(insurance_premium, 2),
        "risk_class": risk_class,
    }


def calculate_launch_collision_risk(
    N_objects: float,
    H_ascent: float,
    launch_cylinder_radius_m: int,
    V_rel: float,
    A_rocket: float,
    T_seconds: float,
    C_total_loss: float,
) -> dict:
    """
    Рассчитывает ожидаемый финансовый риск (ФР) из-за столкновения
    ракеты-носителя или спутника с мусором во время активного участка выведения.
    """
    # Объем считается как объем цилиндра
    # launch_cylinder_radius_m переводится в км для соответствия с H_ascent
    launch_cylinder_radius_km = launch_cylinder_radius_m / 1000.0
    V_corridor = math.pi * (launch_cylinder_radius_km**2) * H_ascent

    if V_corridor <= 0:
        return {
            "error": "Invalid ascent altitude or radius, corridor volume is zero or negative."
        }

    density = N_objects / V_corridor
    A_rocket_km2 = A_rocket / 1_000_000

    expected_collisions = density * V_rel * A_rocket_km2 * T_seconds
    P_collision = 1.0 - math.exp(-expected_collisions)
    financial_risk = P_collision * C_total_loss

    insurance_premium = financial_risk * INSURANCE_COEFFICIENT
    risk_class = assign_risk_class(P_collision)

    return {
        "financial_risk": round(financial_risk, 2),
        "collision_risk": P_collision,
        "insurance_premium": round(insurance_premium, 2),
        "risk_class": risk_class,
    }

