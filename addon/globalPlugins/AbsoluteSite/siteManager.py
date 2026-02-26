# siteManager.py

import os
import json
import globalVars
from logHandler import log

class SiteManager:
	def __init__(self):
		self.configPath = os.path.join(globalVars.appArgs.configPath, "AbsoluteSites.json")
		self.prefsPath = os.path.join(globalVars.appArgs.configPath, "AbsoluteSitePrefs.json")
		self.data = {}
		self.prefs = {}
		self.load()
		self.load_prefs()

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

	def load_prefs(self):
		if os.path.isfile(self.prefsPath):
			try:
				with open(self.prefsPath, 'r', encoding='utf-8') as f:
					self.prefs = json.load(f)
				if not isinstance(self.prefs, dict):
					self.prefs = {}
			except Exception as e:
				log.error(f"Error loading AbsoluteSitePrefs.json: {e}")
				self.prefs = {}
		else:
			self.prefs = {}

	def save_prefs(self):
		try:
			with open(self.prefsPath, 'w', encoding='utf-8') as f:
				json.dump(self.prefs, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log.error(f"Error saving AbsoluteSitePrefs.json: {e}")

	def get_last_category(self):
		"""Return the last used category or None."""
		return self.prefs.get("last_category")

	def set_last_category(self, category):
		"""Save the last used category."""
		if category:
			self.prefs["last_category"] = category
			self.save_prefs()

	def get_all_categories(self):
		return sorted(self.data.keys())

	def get_sites_by_category(self, category):
		return self.data.get(category, [])

	def get_site_by_url(self, url):
		"""Return (category, name, url) if URL exists anywhere, else None."""
		for cat, sites in self.data.items():
			for name, u in sites:
				if u == url:
					return (cat, name, u)
		return None

	def _find_site_in_category(self, category, url):
		"""Return index of site with given URL in the specified category, or None."""
		if category not in self.data:
			return None
		for idx, (name, u) in enumerate(self.data[category]):
			if u == url:
				return idx
		return None

	def add_category(self, category_name):
		if category_name and category_name not in self.data:
			self.data[category_name] = []
			self.save()
			return True
		return False

	def add_site(self, category, display_name, url):
		# Check if URL already exists in this category
		if self._find_site_in_category(category, url) is not None:
			return False
		if category not in self.data:
			self.data[category] = []
		self.data[category].append([display_name, url])
		self.save()
		return True

	def update_site(self, old_category, old_display_name, old_url, new_category, new_display_name, new_url):
		# Find the old entry
		if old_category not in self.data:
			return False
		old_idx = None
		for idx, (name, url) in enumerate(self.data[old_category]):
			if name == old_display_name and url == old_url:
				old_idx = idx
				break
		if old_idx is None:
			return False

		# If category or URL is changing, check for duplicates in the new category
		if new_category != old_category or new_url != old_url:
			if new_category in self.data:
				for idx, (name, url) in enumerate(self.data[new_category]):
					if url == new_url:
						# If same category and this is the old entry itself, allow
						if new_category == old_category and idx == old_idx:
							continue
						return False  # Duplicate in the new category

		# Remove old entry
		del self.data[old_category][old_idx]

		# Add new entry
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