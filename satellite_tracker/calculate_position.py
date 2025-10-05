from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time
from datetime import datetime, timezone
from typing import Dict, Any

from skyfield.toposlib import wgs84

# Загрузка таймскейла Skyfield
ts = load.timescale()


def calculate_satellite_position(
    sat_data: Dict[str, Any], target_time: datetime
) -> Dict[str, float]:
    """
    Рассчитывает положение спутника (широта, долгота, высота) в заданный момент времени.

    Аргументы:
    sat_data (Dict[str, Any]): Словарь с данными спутника, включая 'line1' и 'line2'.
    target_time (datetime): Момент времени для расчета (объект datetime.datetime).

    Возвращает:
    Tuple[float, float, float]: (Широта в градусах, Долгота в градусах, Высота в км).
    """

    name = sat_data.get("name", "UNKNOWN")
    line1 = sat_data.get("line1")
    line2 = sat_data.get("line2")

    if not line1 or not line2:
        raise ValueError(
            "В данных спутника отсутствуют обязательные TLE-строки ('line1' или 'line2')."
        )

    try:
        # 1. Создание объекта EarthSatellite
        satellite = EarthSatellite(line1, line2, name, ts)

        # 2. Надежная обработка часовых поясов
        # Если время "наивное" (без tzinfo), считаем, что оно уже в UTC.
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)
        else:
            # Если время уже с таймзоной, приводим его к UTC для единообразия.
            target_time = target_time.astimezone(timezone.utc)

        t: Time = ts.utc(
            target_time.year,
            target_time.month,
            target_time.day,
            target_time.hour,
            target_time.minute,
            target_time.second + target_time.microsecond / 1_000_000.0,
        )

        # 3. Расчет геоцентрического положения (вектора)
        geocentric = satellite.at(t)

        # 4. КОРРЕКЦИЯ: Использование глобального объекта wgs84 для получения
        # подспутниковой точки (subpoint) из геоцентрического вектора.
        # Это самый надежный способ получить широту/долготу/высоту в Skyfield.
        subpoint = wgs84.subpoint(geocentric)

        # 5. Извлечение широты, долготы и высоты
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        alt_km = subpoint.elevation.km

        return {"lat": lat, "lon": lon, "alt_km": alt_km}

    except ValueError as e:
        raise ValueError(
            f"Ошибка при обработке TLE или расчете положения для {name}: {e}"
        )
    except Exception as e:
        raise Exception(f"Непредвиденная ошибка: {e}")
