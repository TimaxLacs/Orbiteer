from datetime import datetime, timezone, timedelta

from sanic import Blueprint
from sanic.response import json

from satellite_tracker import (
    get_all_trackable_objects,
    calculate_orbit_congestion_by_altitude,
    calculate_satellite_position,
)
from utils.distance_calculation import quick_distance
from utils.risk_calculator import (
    calculate_collision_financial_risk,
    calculate_launch_collision_risk,
)

bp = Blueprint("risks", url_prefix="/api")


@bp.get("/orbit_risk")
async def orbit_collision_risk(request):
    """
    Рассчет риска при нахождении на орбите.
    openapi:
    parameters:
      - name: height
        in: query
        description: Высота на орбите (км)
        required: true
        schema:
          type: integer
          example: 550
      - name: A_effective
        in: query
        description: Эффективная площадь поперечного сечения (м^2)
        required: true
        schema:
          type: number
          format: float
          example: 1.5
      - name: T_years
        in: query
        description:  Срок службы миссии в годах
        required: true
        schema:
          type: integer
          example: 5
      - name: C_full
        in: query
        description: Полная стоимость миссии
        required: true
        schema:
          type: integer
          example: 50000000
      - name: D_lost
        in: query
        description:  Упущенный доход в случае потери спутника
        required: true
        schema:
          type: integer
          example: 100000000
      - name: V_rel
        in: query
        description: Средняя относительная скорость столкновения (км/c)
        required: false
        schema:
          type: number
          format: float
          example: 12.5
    """
    try:
        height = float(request.args["height"][0])
        a_effective = float(request.args["A_effective"][0])
        t_years = float(request.args["T_years"][0])
        c_full = float(request.args["C_full"][0])
        d_lost = float(request.args["D_lost"][0])
        v_rel = (
            float(request.args.get("V_rel")[0]) if request.args.get("V_rel") else 12.5
        )

        all_objects = get_all_trackable_objects()
        congestion_map, _ = calculate_orbit_congestion_by_altitude(
            all_objects, height - 50, height + 50, 0, 180
        )

        total_objects_in_layer = sum(data["count"] for data in congestion_map.values())

        orbit_risk_data = calculate_collision_financial_risk(
            total_objects_in_layer,
            height + 50,
            height - 50,
            v_rel,
            a_effective,
            t_years,
            c_full,
            d_lost,
        )

        return json(orbit_risk_data)

    except KeyError as e:
        return json({"message": f"Missing required parameter: {e.args[0]}"}, status=400)
    except (ValueError, TypeError):
        return json(
            {"message": "Invalid parameter type. Please provide valid numbers."},
            status=400,
        )


@bp.get("/takeoff_risk")
async def takeoff_collision_risk(request):
    """
    Рассчет риска при подъеме объекта.
    openapi:
    parameters:
        - name: lat
          in: query
          description: Широта места запуска. Для расчета риска этот параметр теперь ОБЯЗАТЕЛЕН.
          required: true
          schema:
            type: number
            format: float
            example: 45.96
        - name: lon
          in: query
          description: Долгота места запуска. Для расчета риска этот параметр теперь ОБЯЗАТЕЛЕН.
          required: true
          schema:
            type: number
            format: float
            example: 63.30
        - name: date
          in: query
          description: Дата и время запуска (UTC) в формате YYYY-MM-DDTHH:MM:SS. Для расчета риска этот параметр теперь ОБЯЗАТЕЛЕН.
          required: true
          schema:
            type: string
            example: "2025-10-04T12:00:00"
        - name: launch_radius_meters
          in: query
          description: Радиус (в метрах) цилиндрического коридора запуска для обнаружения объектов.
          required: false
          schema:
            type: string
            example: "50000"
        - name: H_ascent
          in: query
          description: Высота (км), на которой заканчивается активный участок полета ракеты.
          required: true
          schema:
            type: number
            format: float
            example: 200.5
        - name: V_rel
          in: query
          description: Средняя относительная скорость столкновения (V_отн, в км/с). Типичное значение для НОО ~7.8 км/с.
          required: false
          schema:
            type: number
            format: float
            example: 7.8
        - name: A_rocket
          in: query
          description: Эффективная площадь поперечного сечения ракеты (м²).
          required: true
          schema:
            type: number
            format: float
            example: 15.8
        - name: T_seconds
          in: query
          description: Продолжительность (секунды) активного участка полета.
          required: true
          schema:
            type: number
            format: float
            example: 540.0
        - name: C_total_loss
          in: query
          description: Суммарные потери при неудачном запуске.
          required: true
          schema:
            type: number
            format: float
            example: 50000000
    """
    try:
        h_ascent = float(request.args["H_ascent"][0])
        a_rocket = float(request.args["A_rocket"][0])
        t_seconds = float(request.args["T_seconds"][0])
        c_total_loss = float(request.args["C_total_loss"][0])
        lat = float(request.args["lat"][0])
        lon = float(request.args["lon"][0])
        date_str = request.args["date"][0]

        launch_cylinder_radius_m = int(request.args.get("launch_radius_meters", ["50000"])[0])

        v_rel = float(request.args.get("V_rel", [12.5])[0])

        _, filtered_satellites = calculate_orbit_congestion_by_altitude(
            get_all_trackable_objects(), 0, h_ascent, 0, 180
        )

        launch_date = None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                launch_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if launch_date is None:
            return json(
                {"message": f"Invalid date format for '{date_str}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."},
                status=400,
            )

        if launch_date.tzinfo is None:
            launch_date = launch_date.replace(tzinfo=timezone.utc)

        dangerous_satellite_ids = set()
        time_step_seconds = 60

        for time_offset in range(0, int(t_seconds) + 1, time_step_seconds):
            current_time = launch_date + timedelta(seconds=time_offset)
            for sat_data in filtered_satellites:
                try:
                    position = calculate_satellite_position(sat_data, current_time)
                    distance_m = quick_distance(position["lat"], position["lon"], lat, lon)
                    if distance_m < launch_cylinder_radius_m:
                        dangerous_satellite_ids.add(sat_data.get("number"))
                except Exception:
                    continue

        N_objects = len(dangerous_satellite_ids)

        takeoff_risk_data = calculate_launch_collision_risk(
            N_objects,
            h_ascent,
            launch_cylinder_radius_m,
            v_rel,
            a_rocket,
            t_seconds,
            c_total_loss,
        )

        takeoff_risk_data['objects_in_corridor'] = N_objects
        takeoff_risk_data['launch_corridor_radius_km'] = launch_cylinder_radius_m / 1000

        return json(takeoff_risk_data)

    except KeyError as e:
        return json({"message": f"Missing required parameter: {e.args[0]}"}, status=400)
    except (ValueError, TypeError, AttributeError) as e:
        return json(
            {"message": f"Invalid or missing parameter type. Please provide valid numbers. Error: {e}"},
            status=400,
        )

