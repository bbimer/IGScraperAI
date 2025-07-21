import threading
import queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import re
import os
import requests
from fake_useragent import UserAgent

CHROMEDRIVER_PATH = './chromedriver-win64/chromedriver.exe'
NUM_THREADS = 10
REQUEST_DELAY = 3
MAX_CONSECUTIVE_NO = 25
BATCH_SIZE = 45
CHROME_PROFILES_DIR = 'chrome_profiles'

# Country-specific settings
COUNTRY_SETTINGS = {
    "UK": {
        "name_patterns": ["uk", "brit", "eng", "london", "gb", "england", "british"],
        "bio_keywords": ["uk", "british", "england", "london", "manchester", "ukrainian"],
        "age_regex": r'(\d{2})\s?(?:yo|yrs|years|year|age)',
        "location_priority": ["london", "manchester", "birmingham", "uk", "england"],
        "filter_prompt": "Is this a male from UK? Check name, username, bio. Filter out women, non-traditional orientations."
    },
    "DE": {
        "name_patterns": ["ger", "deutsch", "berlin", "munich", "de", "german", "deutsche"],
        "bio_keywords": ["germany", "deutschland", "berlin", "munich", "hamburg", "köln"],
        "age_regex": r'(\d{2})\s?(?:jahr|jahre|alt)',
        "location_priority": ["berlin", "munich", "hamburg", "germany", "deutschland"],
        "filter_prompt": "Ist das ein Mann aus Deutschland? Prüfe Name, Benutzername, Bio. Filtere Frauen, nicht-traditionelle Orientierungen."
    },
    "FR": {
        "name_patterns": ["fr", "paris", "france", "français", "francais", "lyon"],
        "bio_keywords": ["france", "paris", "lyon", "marseille", "français", "francais"],
        "age_regex": r'(\d{2})\s?(?:ans|age)',
        "location_priority": ["paris", "lyon", "marseille", "france"],
        "filter_prompt": "Est-ce un homme de France? Vérifiez le nom, le pseudo, la bio. Filtrez les femmes, les orientations non traditionnelles."
    },
    "CH": {  # Швейцария
        "name_patterns": ["ch", "suisse", "schweiz", "svizzera", "zürich", "geneva", "bern", "swiss"],
        "bio_keywords": ["switzerland", "suisse", "schweiz", "svizzera", "zürich", "geneva", "basel", "bern"],
        "age_regex": r'(\d{2})\s?(?:jahr|jahre|ans|years|alt|age)',
        "location_priority": ["zürich", "geneva", "basel", "bern", "lausanne", "switzerland"],
        "filter_prompt": "Ist das ein Mann aus der Schweiz? Prüfe Name, Benutzername, Bio. Filtere Frauen, nicht-traditionelle Orientierungen."
    },
    "PL": {  # Польша
        "name_patterns": ["pl", "pol", "warsaw", "warszawa", "krakow", "polish", "polski"],
        "bio_keywords": ["poland", "polska", "warsaw", "warszawa", "krakow", "gdansk", "polish"],
        "age_regex": r'(\d{2})\s?(?:lat|rok|roku|years|wiek)',
        "location_priority": ["warsaw", "warszawa", "krakow", "gdansk", "poland", "polska"],
        "filter_prompt": "Czy to mężczyzna z Polski? Sprawdź imię, nazwę użytkownika, bio. Odfiltruj kobiety, nietradycyjne orientacje."
    },
    "NL": {  # Нидерланды
        "name_patterns": ["nl", "nederland", "holland", "amsterdam", "rotterdam", "dutch"],
        "bio_keywords": ["netherlands", "nederland", "holland", "amsterdam", "rotterdam", "utrecht", "dutch"],
        "age_regex": r'(\d{2})\s?(?:jaar|years|oud|age)',
        "location_priority": ["amsterdam", "rotterdam", "utrecht", "hague", "netherlands", "nederland"],
        "filter_prompt": "Is dit een man uit Nederland? Controleer naam, gebruikersnaam, bio. Filter vrouwen, niet-traditionele oriëntaties."
    },
    "UA": {  # Украина
        "name_patterns": ["ua", "ukr", "kyiv", "kiev", "lviv", "odesa", "ukrainian", "україна"],
        "bio_keywords": ["ukraine", "ukrainian", "kyiv", "kiev", "lviv", "odesa", "kharkiv", "україна"],
        "age_regex": r'(\d{2})\s?(?:років|роки|рік|years|вік)',
        "location_priority": ["kyiv", "kiev", "lviv", "odesa", "kharkiv", "ukraine", "україна"],
        "filter_prompt": "Це чоловік з України? Перевірте ім'я, нікнейм, біо. Відфільтруйте жінок, нетрадиційні орієнтації."
    },
    "IT & ES": {
        "name_patterns": [
            # Italian
            "it", "ita", "italy", "roma", "milano", "napoli",
            # Spanish
            "es", "esp", "spain", "españa", "madrid", "barcelona", "sevilla", "valencia"
        ],
        "bio_keywords": [
            # Italian
            "italy", "italiano", "roma", "milano", "napoli", "torino", "sicilia", "calcio",
            "italian", "firenze", "venezia", "bologna", "padova", "bergamo",
            # Spanish
            "spain", "español", "españa", "madrid", "barcelona", "valencia", "sevilla", "granada",
            "málaga", "zaragoza", "bilbao", "mallorca", "sevillista", "barça", "real madrid", "espanol"
        ],
        "age_regex": r'(\d{2})\s?(?:anni|años|ano|yo|yrs|years|year|age)',
        "location_priority": [
            # Italy
            "rome", "milan", "naples", "turin", "palermo", "genoa", "bologna", "florence",
            "venice", "bari", "italy", "sicily", "sardinia",
            # Spain
            "madrid", "barcelona", "valencia", "seville", "granada", "malaga", "zaragoza",
            "bilbao", "alicante", "cordoba", "spain", "españa", "canary islands", "mallorca"
        ],
        "filter_prompt": (
            "Strictly analyze this Instagram profile for MALE from Italy or Spain.\n"
            "CRITERIA (all must be satisfied):\n"
            "1. If the NAME or USERNAME is a typical MALE Italian or Spanish name (e.g. Marco, Luca, Juan, Miguel), "
            "and the bio is empty, minimal, or contains only neutral info (city, sport, emoji, etc.), "
            "then this is OK and can be accepted.\n"
            "2. If the bio contains anything female (female names, -a/-ia endings, pronouns like she/her, words like miss, lady), "
            "LGBT/rainbow/pride, marriage/family (wife, esposa, moglie, mujer, family, married, esposo, esposa, figli, hijos, kids), "
            "beauty, fashion, makeup, cosmetics, nails, spa, or ads/business, migrants (Arabic, African, Asian names), or unclear gender — REJECT.\n"
            "3. If the profile is unclear or suspicious, REJECT.\n"
            "Location (Italy/Spain) is only a plus, but not required if the rest is OK.\n"
            "If in doubt — REJECT.\n"
            "Answer ONLY 'Yes' or 'No', and briefly explain (max 5 words)."
        )
    }
}


def get_user_agent(thread_id):
    ua = UserAgent()
    return ua.random + f' IGThread{thread_id}'


def chrome_profile_dir(thread_id):
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CHROME_PROFILES_DIR, f'profile_{thread_id}')
    os.makedirs(profile_dir, exist_ok=True)
    return profile_dir


def print_profile_info(profile_data, filter_result, passed):
    line = f'''
Profile: {profile_data["profile_url"]}
Name: {profile_data.get("full_name", "")}
Username: {profile_data.get("username", "")}
Bio: {profile_data.get("biography", "")}
Followers: {profile_data.get("followers", "")}
Location: {profile_data.get("location", "not specified")}
Age: {profile_data.get("age", "not specified")}
Filter: {filter_result}
'''
    print(line)


class InstagramScraperThread(threading.Thread):
    def __init__(self, thread_id, channel_queue, profile_queue, result_queue, openrouter_api_key, mode, country,
                 driver=None,
                 lock=None, target_profiles=None):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.channel_queue = channel_queue
        self.profile_queue = profile_queue
        self.result_queue = result_queue
        self.openrouter_api_key = openrouter_api_key
        self.mode = mode
        self.lock = lock or threading.Lock()
        self.driver = driver if driver else self.init_driver()
        self.max_retries = 3
        self.request_delay = REQUEST_DELAY
        self.ready = threading.Event()
        self.target_profiles = target_profiles
        self.found_profiles = 0
        self.consecutive_no = 0
        self.country = country.upper()
        self.country_settings = COUNTRY_SETTINGS.get(self.country, {})

    def init_driver(self):
        chrome_options = Options()
        profile_dir = chrome_profile_dir(self.thread_id)
        chrome_options.add_argument(f'--user-data-dir={profile_dir}')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument(f'user-agent={get_user_agent(self.thread_id)}')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--remote-allow-origins=*')
        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver

    def safe_get(self, url):
        for attempt in range(self.max_retries):
            try:
                self.driver.get(url)
                return True
            except Exception as e:
                print(f'[Thread {self.thread_id}] Error loading URL (attempt {attempt + 1}): {str(e)}')
                time.sleep(2)
        return False

    def manual_login(self):
        if not self.safe_get('https://www.instagram.com/'):
            return False
        time.sleep(3)
        if 'accounts/login' not in self.driver.current_url:
            print(f'[Thread {self.thread_id}] Already logged in, no login needed.')
            return True
        print(f'\n[Thread {self.thread_id}] Please log in to Instagram manually in this window!')
        return True

    def wait_for_login_confirmation(self):
        if not self.safe_get('https://www.instagram.com/'):
            return False
        time.sleep(3)
        if 'accounts/login' in self.driver.current_url:
            print(f'[Thread {self.thread_id}] Login not completed.')
            return False
        self.ready.set()
        return True

    def collect_usernames_from_followers(self, already_collected):
        usernames = []
        last_count = len(already_collected)
        scroll_try = 0
        batch_collected = False

        while not batch_collected:
            time.sleep(1.5)
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Поиск в модальном окне (новый интерфейс)
            modal = soup.find('div', attrs={'role': 'dialog'})
            links = []

            if modal:
                links = modal.find_all('a', href=re.compile(r'^/[^/]+/$'))
            else:
                # Поиск в полноразмерном списке (старый интерфейс)
                main = soup.find('main') or soup.find('section')
                if main:
                    links = main.find_all('a', href=re.compile(r'^/[^/]+/$'))

            # Собираем новые usernames
            new_usernames = []
            for a in links:
                try:
                    uname = a['href'].strip('/').split('/')[0]
                    if (uname and uname not in already_collected
                            and uname not in usernames
                            and uname not in new_usernames):
                        new_usernames.append(uname)
                except:
                    continue

            usernames.extend(new_usernames)

            # Проверяем, собрали ли нужное количество
            if len(usernames) >= BATCH_SIZE:
                usernames = usernames[:BATCH_SIZE]  # Берем ровно BATCH_SIZE
                batch_collected = True
                break

            # Скроллинг в зависимости от типа интерфейса
            try:
                if modal:
                    # Для модального окна
                    scrollbox = self.driver.find_element(
                        By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]")
                    self.driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight + 300",
                        scrollbox)
                else:
                    # Для полноразмерного списка
                    self.driver.execute_script("window.scrollBy(0, 800)")
            except Exception as e:
                print(f'[!] Ошибка скролла: {e}')
                time.sleep(2)

            # Проверка зацикливания
            if len(usernames) == last_count:
                scroll_try += 1
                if scroll_try > 10:
                    print('[!] Прекращаем скролл - нет новых профилей')
                    break
            else:
                scroll_try = 0
                last_count = len(usernames)

        return usernames

    def process_channels(self):
        self.ready.wait()
        while True:
            try:
                channel_url = self.channel_queue.get_nowait()
            except queue.Empty:
                break

            print(f'\n[Thread {self.thread_id}] Парсим канал: {channel_url}')
            if not self.safe_get(channel_url):
                self.channel_queue.task_done()
                continue

            time.sleep(3)

            try:
                # Находим кнопку подписчиков
                followers_btn = self.driver.find_element(
                    By.XPATH, "//a[contains(@href, '/followers')]")
                followers_btn.click()
                time.sleep(3)

                collected_usernames = set()
                self.consecutive_no = 0

                while True:
                    new_usernames = self.collect_usernames_from_followers(collected_usernames)
                    if not new_usernames:
                        print(f'[Channel] Больше нет подписчиков в канале {channel_url}')
                        break

                    for uname in new_usernames:
                        self.profile_queue.put((uname, channel_url))
                        collected_usernames.add(uname)

                    print(f'[Channel] Добавлено {len(new_usernames)} профилей из {channel_url}')

                    for idx in range(len(new_usernames)):
                        _, result = self.result_queue.get()
                        if result == 'yes':
                            self.found_profiles += 1
                            self.consecutive_no = 0
                        else:
                            self.consecutive_no += 1
                            if self.consecutive_no >= MAX_CONSECUTIVE_NO:
                                print(f'[Channel] {MAX_CONSECUTIVE_NO} подряд "нет" - пропускаем канал')
                                for __ in range(idx + 1, len(new_usernames)):
                                    self.result_queue.get()
                                break

                    if self.consecutive_no >= MAX_CONSECUTIVE_NO:
                        break

                    if self.target_profiles and self.found_profiles >= self.target_profiles:
                        print(f'[Thread {self.thread_id}] Достигнуто целевое количество профилей')
                        break


            except Exception as e:
                print(f'[Channel] Ошибка: {e}')

            self.channel_queue.task_done()
            time.sleep(5)

    def get_profile_info_api(self, username):
        try:
            if not self.safe_get(f'https://www.instagram.com/{username}/'):
                return None
            time.sleep(self.request_delay)
            cookies = self.driver.get_cookies()
            session = requests.Session()
            csrf_token = None
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
                if cookie['name'] == 'csrftoken':
                    csrf_token = cookie['value']
            headers = {
                'User-Agent': self.driver.execute_script('return navigator.userAgent;'),
                'X-CSRFToken': csrf_token,
                'Referer': f'https://www.instagram.com/{username}/',
                'X-IG-App-ID': '936619743392459',
                'X-Requested-With': 'XMLHttpRequest'
            }
            url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
            response = session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get('data', {}).get('user', {})
            return None
        except Exception as e:
            print(f'[Profile {self.thread_id}] Error API: {e}')
            return None

    def _get_user_location(self, username, max_posts=3):
        for attempt in range(self.max_retries):
            try:
                if not self.safe_get(f'https://www.instagram.com/{username}/'):
                    continue
                time.sleep(2)
                post_links = []
                for _ in range(2):
                    self.driver.execute_script("window.scrollBy(0, 500)")
                    time.sleep(1.5)
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    new_links = [
                        "https://www.instagram.com" + a["href"]
                        for a in soup.find_all("a", href=re.compile(r'/p/'))
                        if "https://www.instagram.com" + a["href"] not in post_links
                    ]
                    post_links.extend(new_links[:max_posts - len(post_links)])
                    if len(post_links) >= max_posts:
                        break
                for post_url in post_links[:max_posts]:
                    if not self.safe_get(post_url):
                        continue
                    time.sleep(2)
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    location_tag = soup.find("a", href=re.compile(r'/explore/locations/'))
                    if location_tag:
                        return location_tag.get_text(strip=True)
                return None
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2)

    def filter_profile(self, profile_data):
        if not profile_data:
            print('   [!] No profile data for filtering')
            return 'no (no data)'

        # Только нейросеть решает
        prompt = self.country_settings.get("filter_prompt", "") + f"""
    Profile data:
    Name: {profile_data.get('full_name', '')}
    Username: {profile_data.get('username', '')}
    Bio: {profile_data.get('biography', '')}
    Location: {profile_data.get('location', 'not specified')}
    Age: {profile_data.get('age', 'not specified')}

    Answer ONLY 'Yes' or 'No' and briefly explain (up to 5 words). Do NOT pass any profile if there is ANY suspicion of female gender, even ambiguous or unisex names. Reject all unclear and empty profiles by default.
    """
        try:
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json={
                    'model': 'deepseek/deepseek-chat',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.1
                },
                timeout=30
            )
            result = response.json()['choices'][0]['message']['content'].strip().lower()
            print(f'[AI Filter]: {result}')
            return result
        except Exception as e:
            print(f'[!] Thread {self.thread_id}: AI filter error: {str(e)}')
            return 'no (error)'

    def simple_country_check(self, profile_data):
        """Quick check using country-specific patterns"""
        name = (profile_data.get('full_name') or '').lower()
        username = (profile_data.get('username') or '').lower()
        bio = (profile_data.get('biography') or '').lower()
        location = (profile_data.get('location') or '').lower()

        # Check name patterns
        name_patterns = self.country_settings.get("name_patterns", [])
        for pattern in name_patterns:
            if pattern in name or pattern in username:
                return True

        # Check bio keywords
        bio_keywords = self.country_settings.get("bio_keywords", [])
        for keyword in bio_keywords:
            if keyword in bio:
                return True

        # Check location priority
        location_priority = self.country_settings.get("location_priority", [])
        for loc in location_priority:
            if loc in location:
                return True

        return False

    def process_profiles(self):
        self.ready.wait()
        while True:
            try:
                item = self.profile_queue.get(timeout=30)
            except queue.Empty:
                break

            if self.target_profiles is not None and self.found_profiles >= self.target_profiles:
                print(f'[Thread {self.thread_id}] Reached target number of profiles. Stopping.')
                self.profile_queue.task_done()
                break

            if isinstance(item, tuple):
                username, channel_url = item
                profile_url = f'https://www.instagram.com/{username}/'
            else:
                username = item.split('/')[-2]
                profile_url = item

            profile = self.get_profile_info_api(username)
            if not profile:
                self.result_queue.put((username, 'no'))
                self.profile_queue.task_done()
                continue

            location = self._get_user_location(username)
            age = ''
            bio = profile.get('biography', '')
            if bio:
                age_regex = self.country_settings.get("age_regex", r'(\d{2})\s?(?:yo|yrs|years|year|age)')
                match = re.search(age_regex, bio.lower())
                if match:
                    age = match.group(1)

            profile_data = {
                'username': username,
                'full_name': profile.get('full_name', ''),
                'biography': bio,
                'followers': profile.get('edge_followed_by', {}).get('count', ''),
                'location': location,
                'age': age,
                'profile_url': profile_url,
                'source_channel': channel_url if isinstance(item, tuple) else 'direct_link'
            }

            filter_result = self.filter_profile(profile_data)
            passed = filter_result.startswith('yes')
            print_profile_info(profile_data, filter_result, passed)

            with self.lock:
                with open('checked_profiles.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{profile_url}\t{profile_data.get("source_channel", "")}\n')
                if passed:
                    with open('valid_profiles.txt', 'a', encoding='utf-8') as f:
                        f.write(f'{profile_url}\t{profile_data.get("source_channel", "")}\n')
                    print(f'✅ PASSED FILTER! Added: {profile_url}')
                    self.found_profiles += 1

            if passed:
                self.result_queue.put((username, 'yes'))
            else:
                self.result_queue.put((username, 'no'))

            self.profile_queue.task_done()

    def run(self):
        if self.mode == 'channels':
            self.process_channels()
        else:
            self.process_profiles()


def main():
    print('Instagram Multi-Thread Parser')
    openrouter_api_key = input('Enter OpenRouter API Key: ').strip()
    if not openrouter_api_key:
        print('[!] API key required')
        return

    # Select country
    print("\nAvailable countries:")
    for i, country in enumerate(COUNTRY_SETTINGS.keys(), 1):
        print(f"{i}. {country}")
    country_choice = input("Select country (1-8): ").strip()
    try:
        country_index = int(country_choice) - 1
        selected_country = list(COUNTRY_SETTINGS.keys())[country_index]
    except:
        print("[!] Invalid country selection")
        return

    target_profiles = input("How many target profiles to find? (leave empty for unlimited): ").strip()
    target_profiles = int(target_profiles) if target_profiles else None

    # Create Chrome profiles directory
    os.makedirs(CHROME_PROFILES_DIR, exist_ok=True)

    # Clear output files
    for fname in ['links.txt', 'valid_profiles.txt', 'checked_profiles.txt']:
        if os.path.exists(fname):
            os.remove(fname)

    if not os.path.exists('channel.txt'):
        print('[!] channel.txt file not found!')
        return

    with open('channel.txt', 'r', encoding='utf-8') as f:
        channels = [line.strip() for line in f if line.strip()]

    channel_queue = queue.Queue()
    profile_queue = queue.Queue()
    result_queue = queue.Queue()

    for ch in channels:
        channel_queue.put(ch)

    print('\n[+] Preparing browsers for login...')
    drivers = []
    for i in range(NUM_THREADS):
        chrome_options = Options()
        profile_dir = chrome_profile_dir(i)
        chrome_options.add_argument(f'--user-data-dir={profile_dir}')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument(f'user-agent={get_user_agent(i)}')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--remote-allow-origins=*')
        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        driver.get('https://www.instagram.com/')
        drivers.append(driver)

    input('\n[!] After logging in all windows, press ENTER...\n')

    lock = threading.Lock()

    # Create channel processing thread
    channel_thread = InstagramScraperThread(
        thread_id=0,
        channel_queue=channel_queue,
        profile_queue=profile_queue,
        result_queue=result_queue,
        openrouter_api_key=openrouter_api_key,
        mode='channels',
        country=selected_country,
        driver=drivers[0],
        lock=lock,
        target_profiles=target_profiles
    )

    # Create profile processing threads
    profile_threads = []
    for i in range(1, NUM_THREADS):
        profile_threads.append(InstagramScraperThread(
            thread_id=i,
            channel_queue=channel_queue,
            profile_queue=profile_queue,
            result_queue=result_queue,
            openrouter_api_key=openrouter_api_key,
            mode='profiles',
            country=selected_country,
            driver=drivers[i],
            lock=lock,
            target_profiles=target_profiles
        ))

    # Start all threads
    channel_thread.ready.set()
    channel_thread.start()

    for t in profile_threads:
        t.ready.set()
        t.start()

    # Wait for threads to complete
    channel_thread.join()
    for t in profile_threads:
        t.join()

    print('\n[+] Work completed!')

    # Show statistics
    if os.path.exists('valid_profiles.txt'):
        with open('valid_profiles.txt', 'r', encoding='utf-8') as f:
            valid_profiles = [line.strip().split('\t') for line in f if line.strip()]
            valid_count = len(valid_profiles)

        print(f'\nFound valid profiles: {valid_count}')
        print('\nProfile sources:')
        sources = {}
        for profile, source in valid_profiles:
            sources[source] = sources.get(source, 0) + 1

        for source, count in sources.items():
            print(f'{source}: {count} profiles')

        # Save list of parsed channels
        parsed_channels = set()
        with open('checked_profiles.txt', 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) > 1 and parts[1] and parts[1] != 'direct_link':
                    parsed_channels.add(parts[1])

        if parsed_channels:
            with open('parsed_channels.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(parsed_channels))
            print(f'\nParsed channels saved to parsed_channels.txt ({len(parsed_channels)} channels)')

    # Close drivers
    for driver in drivers:
        try:
            driver.quit()
        except:
            pass


if __name__ == '__main__':
    main()