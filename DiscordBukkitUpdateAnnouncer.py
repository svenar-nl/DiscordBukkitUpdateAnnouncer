#!/usr/bin/python3

import requests
import re
from bs4 import BeautifulSoup
import json
import cloudscraper
import time
import urllib.request

webhook_url = "{discord_webhook_url}" # Put your Discord webhook URL here
plugin_url = "https://servermods.forgesvc.net/servermods/files?projectIds={bukkit_project_id}" # change {bukkit_project_id} to you Bukkit project ID
bukkit_base_url = "https://dev.bukkit.org/projects/{bukkit_project_name}/files/" # change {bukkit_project_name} to you Bukkit project name

data = {}
first_run = False
sleep_time = 6 * 60 * 60 # Check every six hours

newest_plugin_version = 0
newest_plugin_version_string = ""
newest_plugin_changelog = ""

def main():
	global newest_plugin_version
	global newest_plugin_version_string
	global first_run

	while True:
		with urllib.request.urlopen(plugin_url) as url:
			data = json.loads(url.read().decode())
			latest_version = data[len(data) - 1]
			bukkit_version = convert_version(latest_version["name"].lower().replace("plugin ", "").replace("v", ""))
			newest_plugin_version_string = latest_version["name"].lower().replace("plugin ", "").replace("v", "")
			project_file_link = bukkit_base_url + latest_version["fileUrl"].split("/")[-1]
			if bukkit_version > newest_plugin_version:
				newest_plugin_version = bukkit_version
				if first_run:
					first_run = False
					print("[INFO] First run, ignoring: " + newest_plugin_version_string)
				else:
					print("[INFO] New version found: " + newest_plugin_version_string)
					process_new_version(newest_plugin_version, project_file_link)
		time.sleep(sleep_time)

def process_new_version(version, project_link): # Scrape Bukkit for the changelog, this may fail because Bukkit uses Cloudfare :/
	global newest_plugin_changelog

	try:
		scraper = cloudscraper.create_scraper()
		soup = BeautifulSoup(scraper.get(project_link).text, 'html.parser')

		logbox = soup.find(class_="logbox")
		changelog = logbox.find("ul").find_all("li")

		for line in changelog:
			newest_plugin_changelog += "* "
			newest_plugin_changelog += line.contents[0]
			newest_plugin_changelog += "\n"

		newest_plugin_changelog = newest_plugin_changelog[0:-2]

		send_discord_embed()
	except:
		print("[ERROR] Cannot get latest changelog for v" + newest_plugin_version_string)

def convert_version(version_string): # Convert version string with some magic (1.2.3 > 123)
	version = 0
	version_split = version_string.split(".")
	if len(version_split) == 3:
		version += int(version_split[0]) * 100
		version += int(version_split[1]) * 10
		version += int(version_split[2])

	if len(version_split) == 2:
		version += int(version_split[0]) * 100
	version += int(version_split[1]) * 10

	if len(version_split) == 1:
                version += int(version_split[0]) * 100

	return version

def send_discord_embed(): # Finally create a message using the Discord webhook url.
	global newest_plugin_version_string
	global newest_plugin_changelog
	global bukkit_base_url

	embed = {}

	embed["title"] = newest_plugin_version_string
	embed["color"] = 1127128
	embed["fields"] = []

	embed["fields"].append({"name": "Info", "value": "A new plugin version is available!"})
	embed["fields"].append({"name": "Changelog", "value": "```{changelog}```".replace("{changelog}", newest_plugin_changelog)})
	embed["fields"].append({"name": "Download", "value": bukkit_base_url "inline": True})

	embed["fields"].append({"name": "Support", "value": """
Put some support information here.
"""})

	data["embeds"] = []
	data["embeds"].append(embed)

	data["content"] = "@everyone"

#	print(json.dumps(data))

	result = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
	try:
		result.raise_for_status()
	except requests.exceptions.HTTPError as err:
		print("[ERROR] " + err)
	else:
		print("[INFO] Successfully announced new version on Discord")

if __name__ == "__main__":
	main()
