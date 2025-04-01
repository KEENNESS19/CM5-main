from uiutils import (get_font, display_cjk_string, Button, color_white,
                     color_bg, color_purple, lal, draw, splash, display,
                     wifi_logo, arrow_logo_2)
import time, os
import subprocess


# Init Key
button = Button()

# Font Loading
font1 = get_font(16)
font2 = get_font(18)

# Wifi Path
wifi1 = "/etc/default/crda"
wifi2 = "/etc/wpa_supplicant/wpa_supplicant.conf"

def safe_write_file(path, content):
    """Securely write to system files with sudo fallback"""
    try:
        # Method 1: Direct write with sudo tee
        subprocess.run(
            f'echo "{content}" | sudo tee {path} >/dev/null',
            shell=True,
            check=True,
            executable='/bin/bash'
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Write failed, trying temp file... Error: {e}")
        try:
            # Method 2: Temp file fallback
            tmp_path = f"/tmp/{os.path.basename(path)}.tmp"
            with open(tmp_path, "w") as f:
                f.write(content)
            subprocess.run(
                ["sudo", "cp", tmp_path, path],
                check=True
            )
            os.remove(tmp_path)
            return True
        except Exception as e:
            print(f"Temp file method failed: {e}")
            return False

# Read original configuration
try:
    with open(wifi1, "r") as f:
        content = f.read()
        ct = content.find("REGDOMAIN=")
        ct_code = content[ct + 10: ct + 12]

    with open(wifi2, "r") as f:
        content2 = f.read()
        ct2 = content2.find("country=")
        ct_code2 = content2[ct2 + 8: ct2 + 10]
except PermissionError:
    print("Permission denied, trying sudo read...")
    content = subprocess.getoutput(f"sudo cat {wifi1}")
    ct = content.find("REGDOMAIN=")
    ct_code = content[ct + 10: ct + 12]
    content2 = subprocess.getoutput(f"sudo cat {wifi2}")
    ct2 = content2.find("country=")
    ct_code2 = content2[ct2 + 8: ct2 + 10]

# UI initialization
splash.paste(wifi_logo, (133, 25), wifi_logo)
text_width = draw.textlength(lal["WIFISET"]["SET"], font=font2)
title_x = (320 - text_width) / 2

display_cjk_string(
    draw,
    title_x,
    90,
    lal["WIFISET"]["SET"],
    font_size=font2,
    color=color_white,
    background_color=color_bg,
)

print("Current country code:", ct_code, ct_code2)

country_list = [
    ["United States", "US"],
    ["Britain(UK)", "GB"],
    ["Japan", "JP"],
    ["Koera(South)", "KR"],
    ["China", "CN"],
    ["Australia", "AU"],
    ["Canada", "CA"],
    ["France", "FR"],
    ["Hong Kong", "HK"],
    ["Singapore", "SG"],
]
select = 0

# Display current country code
draw.rectangle([(20, 130), (120, 160)], fill=color_purple)
display_cjk_string(
    draw, 55, 133, ct_code, 
    font_size=font2, 
    color=color_white, 
    background_color=color_purple
)
display.ShowImage(splash)


while True:
    draw.rectangle([(20, 175), (300, 210)], fill=color_white)
    splash.paste(arrow_logo_2, (277, 185), arrow_logo_2)
    display_cjk_string(
        draw,
        30,
        180,
        country_list[select][0],
        font_size=font2,
        color=(0, 0, 0),
        background_color=color_white,
    )
    display.ShowImage(splash)
    
    if button.press_c():  # Previous
        select = len(country_list) - 1 if select == 0 else select - 1
    elif button.press_d():  # Next
        select = 0 if select == len(country_list) - 1 else select + 1
    elif button.press_a():  # Confirm
        break
    elif button.press_b():  # Exit
        os._exit(0)

new_code = country_list[select][1]
print("Selected country code:", new_code)

# Update configuration content
if ct >= 0:
    content = content.replace(f"REGDOMAIN={ct_code}", f"REGDOMAIN={new_code}")
else:
    content = f"{content}\nREGDOMAIN={new_code}\n" if content else f"REGDOMAIN={new_code}\n"

if ct2 >= 0:
    content2 = content2.replace(f"country={ct_code2}", f"country={new_code}")
else:
    content2 = f"{content2}\ncountry={new_code}\n" if content2 else f"country={new_code}\n"

# Securely write files
if safe_write_file(wifi1, content) and safe_write_file(wifi2, content2):
    # Apply settings immediately
    try:
        subprocess.run(["sudo", "iw", "reg", "set", new_code], check=True)
        subprocess.run(["sudo", "systemctl", "restart", "wpa_supplicant"], check=True)
        msg = "Settings Saved!"
        bg_color = color_purple
    except subprocess.CalledProcessError as e:
        msg = "Failed to apply settings!"
        bg_color = (255, 0, 0)
else:
    msg = "Save Failed! Check permissions"
    bg_color = (255, 0, 0)

# Show operation result
text_width = draw.textlength(msg, font=font2)
title_x = (320 - text_width) / 2
display_cjk_string(
    draw,
    title_x,
    210,
    msg,
    font_size=font2,
    color=color_white,
    background_color=bg_color,
)
display.ShowImage(splash)
time.sleep(2)