# siteManager.py

import os
import json
import globalVars
from logHandler import log

class SiteManager:
	def __init__(self):
		self.configPath = os.path.join(globalVars.appArgs.configPath, "AbsoluteSites.json")
		self.data = {}
		self.load()

	def load(self):
		if os.path.isfile(self.configPath):
			try:
				with open(self.configPath, 'r', encoding='utf-8') as f:
					self.data = json.load(f)
				if not isinstance(self.data, dict):
					self.data = {}
			except Exception as e:
				log.error(f"Error loading AbsoluteSites.json: {e}")
				self.data = {}
		else:
			self.data = {}

	def save(self):
		try:
			with open(self.configPath, 'w', encoding='utf-8') as f:
				json.dump(self.data, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log.error(f"Error saving AbsoluteSites.json: {e}")

	def get_all_categories(self):
		return sorted(self.data.keys())

	def get_sites_by_category(self, category):
		return self.data.get(category, [])

	def get_site_by_url(self, url):
		for cat, sites in self.data.items():
			for name, u in sites:
				if u == url:
					return (cat, name, u)
		return None

	def add_category(self, category_name):
		if category_name and category_name not in self.data:
			self.data[category_name] = []
			self.save()
			return True
		return False

	def add_site(self, category, display_name, url):
		if self.get_site_by_url(url) is not None:
			return False
		if category not in self.data:
			self.data[category] = []
		self.data[category].append([display_name, url])
		self.save()
		return True

	def update_site(self, old_category, old_display_name, old_url, new_category, new_display_name, new_url):
		if old_category not in self.data:
			return False
		found = None
		for idx, (name, url) in enumerate(self.data[old_category]):
			if name == old_display_name and url == old_url:
				found = idx
				break
		if found is None:
			return False
		# Remove old entry
		del self.data[old_category][found]
		# Add new entry, checking URL conflict
		if new_url != old_url:
			existing = self.get_site_by_url(new_url)
			if existing is not None:
				# Restore old entry
				self.data[old_category].insert(found, [old_display_name, old_url])
				return False
		if new_category not in self.data:
			self.data[new_category] = []
		self.data[new_category].append([new_display_name, new_url])
		self.save()
		return True

	def remove_site(self, category, display_name, url):
		if category not in self.data:
			return False
		for idx, (name, u) in enumerate(self.data[category]):
			if name == display_name and u == url:
				del self.data[category][idx]
				self.save()
				return True
		return False