import random
import time
import base64
import requests
from seleniumbase import SB


def get_geo_data():
    """Obține date de geolocație reale (sau fallback)"""
    try:
        r = requests.get("http://ip-api.com/json/", timeout=6)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            raise ValueError("ip-api failed")
        return data
    except Exception as e:
        print(f"Geo fallback: {e}")
        return {
            "lat": 46.77, "lon": 23.58,      # Cluj-Napoca exemplu
            "timezone": "Europe/Bucharest",
            "countryCode": "RO"
        }


def main():
    # ───────────────────────────────────────────────
    # Configurare țintă
    # ───────────────────────────────────────────────
    channel_encoded = "YnJ1dGFsbGVz"
    channel_name = base64.b64decode(channel_encoded).decode("utf-8")
    target_url = f"https://www.twitch.tv/{channel_name}"

    # ───────────────────────────────────────────────
    # Date geolocație & limbă
    # ───────────────────────────────────────────────
    geo = get_geo_data()
    latitude = geo["lat"]
    longitude = geo["lon"]
    timezone = geo["timezone"]
    lang_code = geo["countryCode"].lower()          # ro, us, etc.

    print(f"→ Targeting: {target_url}")
    print(f"→ Geo: {latitude:.4f}, {longitude:.4f}  |  TZ: {timezone}")

    while True:
        try:
            # Durată watch random realistă: 7.5 – 16 minute
            watch_time_sec = random.randint(450, 960)

            with SB(
                uc=True,
                locale="en",
                ad_block=True,
                chromium_arg="--disable-webgl",          # opțional – Twitch nu mai cere WebGL mereu
                # proxy="socks5://user:pass@ip:port"     # dacă vrei proxy real mai târziu
                proxy=False
            ) as driver:

                print(f"  Watch session started – planned {watch_time_sec//60} min")

                # Pornim cu fingerprint spoofing + geolocație
                driver.activate_cdp_mode(
                    target_url,
                    tzone=timezone,
                    geoloc=(latitude, longitude)
                )

                time.sleep(random.uniform(1.8, 3.2))     # human-like delay

                # Accept cookies / GDPR / age gate
                for selector, text in [
                    ('button:contains("Accept")', "Accept"),
                    ('button:contains("OK")', "OK"),
                    ('button:contains("Start Watching")', "Start Watching"),
                    ('button:contains("Got it")', "Got it"),
                ]:
                    if driver.is_element_present(selector):
                        try:
                            driver.cdp.click(selector, timeout=5)
                            print(f"    Clicked: {text}")
                            time.sleep(random.uniform(0.7, 1.9))
                        except:
                            pass

                # Așteptăm să se încarce player-ul
                driver.sleep(random.uniform(8, 14))

                if not driver.is_element_present("#live-channel-stream-information"):
                    print("  Stream not live or page did not load correctly → break")
                    break

                # Deschidem al doilea tab / driver (cea mai stabilă metodă de moment)
                driver2 = driver.get_new_driver(undetectable=True)
                driver2.activate_cdp_mode(
                    target_url,
                    tzone=timezone,
                    geoloc=(latitude, longitude)
                )

                # Mic delay + accept pe al doilea tab
                driver2.sleep(random.uniform(6, 11))
                if driver2.is_element_visible('button:has-text("Start Watching")'):
                    driver2.cdp.click('button:has-text("Start Watching")')
                    driver2.sleep(3)

                # Așteptăm watch_time
                print(f"  Watching for ~{watch_time_sec} seconds ...")
                time.sleep(watch_time_sec)

                # Închidere curată
                try:
                    driver2.quit()
                except:
                    pass

                print("  Session finished cleanly\n")

        except Exception as e:
            print(f"Critical error in loop: {e.__class__.__name__}: {e}")
            time.sleep(45)   # cooldown mai lung la eroare gravă

        # Pauză între sesiuni (anti-pattern detect)
        inter_session_pause = random.randint(40, 140)
        print(f"Pause {inter_session_pause} sec before next session...")
        time.sleep(inter_session_pause)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
