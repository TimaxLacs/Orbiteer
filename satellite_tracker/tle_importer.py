import requests
import time
from typing import List, Dict, Any


def get_all_trackable_objects() -> List[Dict[str, Any]]:
    """
    Загружает и парсит TLE-данные для всех отслеживаемых объектов
    (активные спутники, станции, мусор) с CelesTrak, используя
    стабильный текстовый формат TLE.
    """
    base_url = "https://celestrak.org/NORAD/elements/gp.php"

    # URL-адреса для получения данных в формате TLE
    urls = {
        "active": f"{base_url}?GROUP=active&FORMAT=tle",
        "stations": f"{base_url}?GROUP=stations&FORMAT=tle",
        "rocket-bodies": f"{base_url}?GROUP=rocket-bodies&FORMAT=tle",
        "cosmos-1408-debris": f"{base_url}?GROUP=cosmos-1408-debris&FORMAT=tle",
        "iridium-33-debris": f"{base_url}?GROUP=iridium-33-debris&FORMAT=tle",
        "cosmos-2251-debris": f"{base_url}?GROUP=cosmos-2251-debris&FORMAT=tle",
        "fengyun-1c-debris": f"{base_url}?GROUP=fengyun-1c-debris&FORMAT=tle",
        "dmsp-f13-debris": f"{base_url}?GROUP=dmsp-f13-debris&FORMAT=tle",
        "breeze-m-debris": f"{base_url}?GROUP=breeze-m-debris&FORMAT=tle",
        "debris": f"{base_url}?GROUP=DEBRIS&FORMAT=tle",
        "decaying": f"{base_url}?SPECIAL=DECAYING&FORMAT=tle",
    }

    # Используем словарь для хранения уникальных объектов по их номеру, чтобы избежать дубликатов
    unique_objects: Dict[int, Dict[str, Any]] = {}

    for category, url in urls.items():
        print(f"Загрузка данных из категории '{category}' с {url}...")

        # ДОБАВЛЕНО: Пауза в 1 секунду перед каждым запросом, чтобы не перегружать сервер CelesTrak
        time.sleep(1)

        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()

            # Парсим ответ как простой текст
            lines = response.text.strip().splitlines()

            print(f"Получено {len(lines) // 3} объектов из '{category}'.")

            # TLE данные идут блоками по 3 строки: Имя, Строка 1, Строка 2
            # Итерируемся с шагом 3
            for i in range(0, len(lines), 3):
                try:
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()

                    # Проверяем, что строки TLE имеют корректную длину
                    if len(line1) != 69 or len(line2) != 69:
                        continue

                    # Извлекаем номер спутника из первой строки TLE
                    sat_num = int(line1[2:7])

                    unique_objects[sat_num] = {
                        "name": name,
                        "number": sat_num,
                        "line1": line1,
                        "line2": line2,
                    }
                except (IndexError, ValueError) as e:
                    # Пропускаем некорректно сформированные TLE-блоки
                    # print(f"Пропущен некорректный блок TLE в категории {category}: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Произошла ошибка при запросе {url}: {e}")
            continue

    print(f"Загрузка завершена. Всего уникальных объектов: {len(unique_objects)}")
    return list(unique_objects.values())
