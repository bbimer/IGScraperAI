import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import getpass


class InstagramScraper:
    def __init__(self):
        self.driver = None
        self.session = requests.Session()
        self.batch_size = 15  # Количество профилей для проверки перед анализом
        self.scroll_pixels = 300  # Количество пикселей для скролла
        self.scroll_delay = 1.5  # Задержка между скроллами
        self.csrf_token = None
        self.session_id = None
        self.logged_in = False
        self.request_delay = 3
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
        }

    def init_selenium(self):
        """Инициализация Selenium драйвера"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=chrome_options)

    def manual_login(self):
        """Ручная авторизация в Instagram"""
        print("\n[i] Пожалуйста, выполните вход в Instagram в открывшемся окне браузера")
        print("[i] После успешного входа нажмите Enter в этом окне...")
        self.driver.get("https://www.instagram.com/")
        input("[i] Нажмите Enter после авторизации...")

        # Получаем cookies из Selenium и переносим в requests.Session
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
            if cookie['name'] == 'csrftoken':
                self.csrf_token = cookie['value']
            if cookie['name'] == 'sessionid':
                self.session_id = cookie['value']

        self.logged_in = True
        self.headers.update({
            'X-CSRFToken': self.csrf_token,
            'Referer': 'https://www.instagram.com/'
        })

    def get_profile_info_api(self, username):
        """Получение информации о профиле через API"""
        if not self.logged_in:
            print("[!] Необходима авторизация")
            return None

        try:
            time.sleep(self.request_delay)
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

            self.headers.update({
                'X-CSRFToken': self.csrf_token,
                'Referer': f'https://www.instagram.com/{username}/'
            })

            response = self.session.get(url, headers=self.headers)
            if response.status_code == 200:
                user_data = response.json().get('data', {}).get('user', {})

                # Получаем локации из постов через Selenium
                location = self.get_user_location_selenium(username)

                # Извлекаем возраст из биографии
                age = ""
                bio = user_data.get('biography', '')
                match = re.search(r'(\d{2})\s?yo', bio.lower())
                if match:
                    age = match.group(1)

                return {
                    'id': user_data.get('id'),
                    'username': user_data.get('username'),
                    'full_name': user_data.get('full_name'),
                    'biography': bio,
                    'profile_pic_url': user_data.get('profile_pic_url_hd'),
                    'followers_count': user_data.get('edge_followed_by', {}).get('count'),
                    'following_count': user_data.get('edge_follow', {}).get('count'),
                    'is_private': user_data.get('is_private'),
                    'is_verified': user_data.get('is_verified'),
                    'external_url': user_data.get('external_url'),
                    'location': location,
                    'age': age,
                    'profile_url': f"https://www.instagram.com/{username}/"
                }
            elif response.status_code == 404:
                print(f"[!] Пользователь @{username} не найден")
            else:
                print(f"[!] API Error: HTTP {response.status_code}")
            return None

        except Exception as e:
            print(f"[!] Ошибка при получении информации о профиле: {str(e)}")
            return None

    def get_user_location_selenium(self, username, max_posts=3):
        """Получение локации пользователя из постов через Selenium"""
        if not self.driver:
            self.init_selenium()

        try:
            post_links = self.get_post_links_selenium(username, max_posts)
            for link in post_links:
                location = self.get_location_from_post_selenium(link)
                if location:
                    return location
        except Exception as e:
            print(f"[!] Ошибка при получении локации: {str(e)}")
        return None

    def get_post_links_selenium(self, username, count=3):
        """Получение ссылок на посты через Selenium"""
        url = f"https://www.instagram.com/{username}/"
        self.driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        links = []
        for a in soup.find_all("a", href=True):
            if "/p/" in a["href"]:
                links.append("https://www.instagram.com" + a["href"])
            if len(links) >= count:
                break
        return links

    def get_location_from_post_selenium(self, post_url):
        """Получение локации из конкретного поста через Selenium"""
        self.driver.get(post_url)
        time.sleep(2)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        for a in soup.find_all("a", href=True):
            if "/explore/locations/" in a["href"]:
                return a.get_text(strip=True)
        return None

    def filter_profile_by_deepseek(self, profile_data, openrouter_api_key):
        """Фильтрация профиля через DeepSeek AI"""
        prompt = f"""
Вопрос: Это мужчина из Украины? Сделать отсев - геев, негров, женщин, ботов. У него может быть украинский - никнейм, username, био. Если локации конретной не имеется, это не значит что не Украинец. Ответь только "Да" или "Нет" и коротко почему.

Профиль пользователя:
Имя: {profile_data.get('full_name', '')}
Username: {profile_data.get('username', '')}
Биография: {profile_data.get('biography', '')}
Локация: {profile_data.get('location', '')}
Возраст (если есть): {profile_data.get('age', '')}
"""
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json"
        }
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": "deepseek/deepseek-chat-v3-0324",
            "messages": [
                {"role": "system",
                 "content": "Отвечай только 'Да' или 'Нет'. Если есть причина, добавь короткое пояснение."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            result = response.json()
            answer = result['choices'][0]['message']['content'].strip().lower()
            return answer
        except Exception as e:
            print(f"[!] Ошибка разбора ответа нейросети: {e}")
            return "нет"

    def extract_usernames_batch(self, account_list, accountlist_class, batch_size):
        """Извлечение пачки username'ов"""
        usernames = set()

        for _ in range(3):  # Делаем несколько скроллов для сбора username'ов
            self.driver.execute_script(f"arguments[0].scrollBy(0, {self.scroll_pixels});", account_list)
            time.sleep(self.scroll_delay)

            accountlist_html = account_list.get_attribute('outerHTML')
            soup = BeautifulSoup(accountlist_html, 'html.parser')
            account_links = soup.find_all('a', href=True)
            new_usernames = [link['href'].strip('/').split('/')[0] for link in account_links if
                             link['href'].startswith('/')]
            usernames.update(new_usernames)

            if len(usernames) >= batch_size:
                break

        return list(usernames)[:batch_size]

    def scrape_channel(self, channel_url, openrouter_api_key):
        """Парсинг канала с проверкой пачками по 15 профилей"""
        try:
            print(f"\n==== Начинаем парсинг канала: {channel_url} ====")

            # Переходим на страницу канала
            self.driver.get(channel_url)
            time.sleep(4)

            # Открываем список подписчиков
            button_xpath = "//a[contains(@href, '/followers/')]"
            followers_link = self.driver.find_element(By.XPATH, button_xpath)
            self.driver.execute_script("arguments[0].click();", followers_link)
            time.sleep(4)

            # Находим div со списком подписчиков
            accountlist_div = None
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            for div in soup.find_all('div', style=True):
                if div.get('style') == "height: auto; overflow: hidden auto;":
                    accountlist_div = div.find_parent('div')
                    break

            if not accountlist_div:
                print("[!] Не удалось найти список подписчиков")
                return False

            accountlist_class = accountlist_div.get('class')[0]
            account_list = self.driver.find_element(By.CLASS_NAME, accountlist_class)

            processed_count = 0
            valid_found_in_channel = False

            while True:
                # Собираем пачку username'ов
                print(f"\n[+] Собираем пачку из {self.batch_size} профилей...")
                usernames = self.extract_usernames_batch(account_list, accountlist_class, self.batch_size)

                if not usernames:
                    print("[!] Не удалось собрать новые профили")
                    break

                print(f"[+] Проверяем {len(usernames)} профилей...")
                valid_found_in_batch = False

                for username in usernames:
                    processed_count += 1
                    print(f"\n[{processed_count}] --> Проверяем профиль: @{username}")

                    profile = self.get_profile_info_api(username)
                    if not profile or not profile.get("full_name"):
                        print("   [!] Не удалось получить информацию о профиле")
                        continue

                    print(f"   Имя: {profile.get('full_name', '')}")
                    print(f"   Bio: {profile.get('biography', '')}")
                    print(f"   Локация: {profile.get('location', 'не указана')}")
                    print(f"   Возраст: {profile.get('age', 'не указан')}")

                    answer = self.filter_profile_by_deepseek(profile, openrouter_api_key)
                    print(f"   [DeepSeek]: {answer}")

                    if answer.startswith("да"):
                        with open("links.txt", "a", encoding="utf-8") as f:
                            f.write(profile["profile_url"] + "\n")
                        print(f"   [✔] ПРОШЁЛ ФИЛЬТР! Добавлен: {profile['profile_url']}")
                        valid_found_in_batch = True
                        valid_found_in_channel = True
                    else:
                        print(f"   [✖] НЕ ПРОШЁЛ по фильтру.")

                # Проверяем, нужно ли продолжать
                if not valid_found_in_batch:
                    print("\n[⚠] В этой пачке не найдено подходящих профилей. Прекращаем парсинг этого канала.")
                    break
                else:
                    print("\n[✓] В пачке найден подходящий профиль. Продолжаем парсинг...")

            return valid_found_in_channel

        except Exception as e:
            print(f"[!] Ошибка при парсинге канала: {str(e)}")
            return False

    def close(self):
        """Закрытие соединений"""
        if self.driver:
            self.driver.quit()


def main():
    print("=== Instagram Scraper + DeepSeek Filter ===")
    scraper = InstagramScraper()
    scraper.init_selenium()

    # Ручная авторизация
    scraper.manual_login()

    # API ключ для DeepSeek
    openrouter_api_key = input("Введите OpenRouter API Key: ").strip()

    # Чтение каналов из файла
    try:
        with open('channel.txt', 'r', encoding='utf-8') as f:
            channels = [line.strip() for line in f if line.strip()]
        if not channels:
            print("[!] Файл channel.txt пустой!")
            return
    except Exception as e:
        print(f"[!] Ошибка при чтении channel.txt: {str(e)}")
        return

    # Обработка каналов
    for channel_url in channels:
        print(f"\n=== Обработка канала: {channel_url} ===")
        valid_found = scraper.scrape_channel(channel_url, openrouter_api_key)

        if valid_found:
            print("[✓] В канале найдены подходящие профили!")
        else:
            print("[⚠] В канале не найдено подходящих профилей. Переходим к следующему.")

    scraper.close()
    print("\n[+] Работа завершена!")


if __name__ == "__main__":
    main()