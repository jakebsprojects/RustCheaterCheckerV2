import tkinter as tk
from tkinter import ttk, messagebox
import requests
import re
import time
from bs4 import BeautifulSoup

class RustCheaterCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rust Cheater Checker")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        # Header Label
        header_label = ttk.Label(self.root, text="Rust Cheater Checker", font=("Helvetica", 20, "bold"))
        header_label.pack(pady=20)

        # Input Section
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=20)

        steam_url_label = ttk.Label(input_frame, text="Enter Steam URL:")
        steam_url_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.steam_url_entry = ttk.Entry(input_frame, width=50)
        self.steam_url_entry.grid(row=0, column=1, padx=10, pady=10)

        # Action Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)

        check_button = ttk.Button(button_frame, text="Check for Cheater", command=self.check_cheater)
        check_button.grid(row=0, column=0, padx=10, pady=10)

        breakdown_button = ttk.Button(button_frame, text="Show Breakdown", command=self.show_breakdown)
        breakdown_button.grid(row=0, column=1, padx=10, pady=10)

        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh)
        refresh_button.grid(row=0, column=2, padx=10, pady=10)

        # Result Display
        result_frame = ttk.Frame(self.root)
        result_frame.pack(pady=20)

        self.result_label = ttk.Label(result_frame, text="", font=("Helvetica", 14), wraplength=500, justify="center")
        self.result_label.pack()

        # Status Label (Processing Messages)
        self.status_label = ttk.Label(self.root, text="", font=("Helvetica", 12, "italic"))
        self.status_label.pack(pady=10)

    def fetch_profile_data(self, steam_url):
        api_key = "C82411981FA3ED92A9744F9FD4F30A8F"
        base_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"

        # Extract user ID from Steam URL using regex
        pattern = r"steamcommunity\.com/(profiles|id)/(\w+)"
        match = re.search(pattern, steam_url)
        if not match:
            messagebox.showerror("Error", "Invalid Steam URL format.")
            return None

        steam_id = match.group(2)
        params = {
            'key': api_key,
            'steamids': steam_id
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            if 'players' in data['response'] and data['response']['players']:
                profile_data = data['response']['players'][0]
                if profile_data.get('communityvisibilitystate') != 3:
                    messagebox.showinfo("Info", "This Steam account is private or does not exist.")
                    return None
                return profile_data
            else:
                messagebox.showinfo("Info", "This Steam account is private or does not exist.")
                return None
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch data from Steam API: {str(e)}")
            return None

    def fetch_hours_played(self, steam_id):
        api_key = "C82411981FA3ED92A9744F9FD4F30A8F"
        base_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        params = {
            'key': api_key,
            'steamid': steam_id,
            'format': 'json'
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            if 'response' in data and 'games' in data['response']:
                for game in data['response']['games']:
                    if game['appid'] == 252490:  # 252490 is the AppID for Rust
                        return game['playtime_forever'] // 60  # Convert minutes to hours
                # If Rust is not found in the games list, assume 0 hours
                return 0
            else:
                messagebox.showerror("Error", "Failed to fetch hours played from Steam API.")
                return None
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch hours played from Steam API: {str(e)}")
            return None

    def calculate_points(self, profile_data, steam_url):
        points = 0
        breakdown_text = ""

        # Account Age Calculation
        if 'timecreated' in profile_data:
            account_creation_time = profile_data['timecreated']
            account_age_days = (time.time() - account_creation_time) / (60 * 60 * 24)
            if account_age_days < 30:
                points += 4
                breakdown_text += "+4 points: Account created less than 30 days ago\n"
            elif 30 <= account_age_days < 90:
                points += 3
                breakdown_text += "+3 points: Account created 30-90 days ago\n"
            elif 90 <= account_age_days < 180:
                points += 1
                breakdown_text += "+1 point: Account created 90-180 days ago\n"
            elif account_age_days > 365:
                points -= 2
                breakdown_text += "-2 points: Account created more than 1 year ago\n"

        # Friend Count Calculation
        steam_id = re.search(r"steamcommunity\.com/(profiles|id)/(\w+)", steam_url).group(2)
        friend_count = self.scrape_friend_count(steam_id)
        if friend_count is not None:
            if friend_count <= 1:
                points += 3
                breakdown_text += "+3 points: Fewer than 1 friend\n"
            elif 1 < friend_count <= 5:
                points += 2
                breakdown_text += "+2 points: 1-5 friends\n"
            elif 5 < friend_count <= 7:
                points += 1
                breakdown_text += "+1 point: 5-7 friends\n"
            elif friend_count > 10:
                breakdown_text += "+0 points: More than 10 friends\n"
            elif friend_count > 15:
                points -= 2
                breakdown_text += "-2 points: More than 15 friends\n"

        # Steam Level Calculation
        steam_level = self.scrape_steam_level(steam_url)
        if steam_level is not None:
            if 0 <= steam_level <= 2:
                points += 2
                breakdown_text += "+2 points: Steam level 0-2\n"
            elif 2 < steam_level <= 4:
                points += 1
                breakdown_text += "+1 point: Steam level 2-4\n"
            elif steam_level >= 6:
                breakdown_text += "+0 points: Steam level 6+\n"

        # Hours Played Calculation
        hours_played = self.fetch_hours_played(steam_id)
        if hours_played is not None:
            if hours_played < 50:
                points += 4
                breakdown_text += "+4 points: Less than 50 hours played in Rust\n"
            elif 50 <= hours_played < 100:
                points += 3
                breakdown_text += "+3 points: 50-100 hours played in Rust\n"
            elif 100 <= hours_played < 300:
                points += 2
                breakdown_text += "+2 points: 100-300 hours played in Rust\n"
            elif 300 <= hours_played < 400:
                points += 1
                breakdown_text += "+1 point: 300-400 hours played in Rust\n"
            elif 400 <= hours_played < 500:
                breakdown_text += "+0 points: 400-500 hours played in Rust\n"
            elif hours_played >= 500:
                points -= 1
                breakdown_text += "-1 points: More than 500 hours played in Rust\n"
            if hours_played >= 1000:
                points -= 3
                breakdown_text += "-3 points: More than 1000 hours played in Rust\n"

        # VAC Ban Status Calculation
        vac_banned = self.fetch_vac_ban_status_api(steam_id)
        if vac_banned is not None:
            if vac_banned:
                points += 5
                breakdown_text += "+5 points: Previous VAC ban\n"
            else:
                breakdown_text += "+0 points: No VAC ban\n"

        return points, breakdown_text

    def determine_hacking_chance(self, points):
        max_points = 10
        if points <= 0:
            return "No Chance Of Hacking", 0
        elif points >= max_points:
            return "Hacking", 100
        else:
            percentage = (points / max_points) * 100
            if percentage <= 10:
                return "No Chance Of Hacking", percentage
            elif 10 < percentage <= 30:
                return "Small Chance Of Hacking", percentage
            elif 30 < percentage <= 50:
                return "Medium Chance Of Hacking", percentage
            elif 50 < percentage <= 70:
                return "High Chance Of Hacking", percentage
            elif 70 < percentage <= 80:
                return "Extremely High Chance Of Hacking", percentage
            else:
                return "Hacking", percentage

    def check_cheater(self):
        steam_url = self.steam_url_entry.get().strip()
        if not steam_url:
            messagebox.showerror("Error", "Please enter a Steam URL.")
            return

        self.status_label.config(text="Processing...")
        self.root.update_idletasks()
        profile_data = self.fetch_profile_data(steam_url)
        if not profile_data:
            self.status_label.config(text="")
            return

        points, breakdown_text = self.calculate_points(profile_data, steam_url)
        hacking_chance, percentage = self.determine_hacking_chance(points)

        self.status_label.config(text="Completing background checks...")
        self.root.update_idletasks()
        time.sleep(1.2)
        self.status_label.config(text="")

        result_text = f"This user is in the {hacking_chance} zone.\nChance: {percentage:.2f}%"
        self.result_label.config(text=result_text)

    def show_breakdown(self):
        steam_url = self.steam_url_entry.get().strip()
        if not steam_url:
            messagebox.showerror("Error", "Please enter a Steam URL.")
            return

        profile_data = self.fetch_profile_data(steam_url)
        if not profile_data:
            return

        points, breakdown_text = self.calculate_points(profile_data, steam_url)

        breakdown_window = tk.Toplevel(self.root)
        breakdown_window.title("Points Breakdown")

        text_area = tk.Text(breakdown_window, width=60, height=20, wrap=tk.WORD)
        text_area.pack(padx=10, pady=10)
        text_area.insert(tk.END, breakdown_text)
        text_area.configure(state='disabled')

    def refresh(self):
        self.steam_url_entry.delete(0, tk.END)
        self.status_label.config(text="")
        self.result_label.config(text="")

    def scrape_friend_count(self, steam_id):
        url = f"https://steamladder.com/profile/{steam_id}/"
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            friend_count_element = soup.find('table', class_='table stats general').find('tbody').find_all('tr')[6].find('td').find('a')
            friend_count = int(friend_count_element.text.strip())
            return friend_count
        except Exception as e:
            print(f"Error scraping friend count: {str(e)}")
            return None

    def scrape_steam_level(self, steam_url):
        try:
            response = requests.get(steam_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            level_span = soup.find('div', class_='persona_name persona_level').find('div').find('span')
            steam_level = int(level_span.text.strip())
            return steam_level
        except Exception as e:
            print(f"Error scraping Steam level: {str(e)}")
            return None

    def fetch_vac_ban_status_api(self, steam_id):
        api_key = "C82411981FA3ED92A9744F9FD4F30A8F"
        base_url = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"

        params = {
            'key': api_key,
            'steamids': steam_id
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            if 'players' in data and len(data['players']) > 0:
                player_data = data['players'][0]
                return player_data.get('VACBanned', False)
            else:
                messagebox.showinfo("Info", "Failed to fetch VAC ban status.")
                return None
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch VAC ban status: {str(e)}")
            return None


if __name__ == "__main__":
    root = tk.Tk()
    app = RustCheaterCheckerApp(root)
    root.mainloop()
