# siteManager.py

import os
import json
import shutil
import globalVars
from logHandler import log

class SiteManager:
	def __init__(self):
		# Directory for storing add-on data
		self.dataDir = os.path.join(globalVars.appArgs.configPath, "ChaiChaimee", "AbsoluteSite")
		try:
			os.makedirs(self.dataDir, exist_ok=True)
		except Exception as e:
			log.error(f"Could not create data directory {self.dataDir}: {e}")

		self.configPath = os.path.join(self.dataDir, "AbsoluteSites.json")
		self.prefsPath = os.path.join(self.dataDir, "AbsoluteSitePrefs.json")
		self.orderPath = os.path.join(self.dataDir, "AbsoluteSiteOrder.json")

		self._migrate_old_files()

		self.data = {}          # category -> list of [name, url]
		self.prefs = {}          # last_category etc.
		self.order = {}          # category -> list of URLs in custom order
		self.pinned = {}         # category -> set of pinned URLs

		self.load()
		self.load_prefs()
		self.load_order()

	def _migrate_old_files(self):
		old_root_config = os.path.join(globalVars.appArgs.configPath, "AbsoluteSites.json")
		old_root_prefs = os.path.join(globalVars.appArgs.configPath, "AbsoluteSitePrefs.json")
		old_dir = os.path.join(globalVars.appArgs.configPath, "ConfigAbsoluteSite")
		old_dir_config = os.path.join(old_dir, "AbsoluteSites.json")
		old_dir_prefs = os.path.join(old_dir, "AbsoluteSitePrefs.json")

		new_config = self.configPath
		new_prefs = self.prefsPath

		if os.path.exists(new_config) and os.path.exists(new_prefs):
			return

		if not os.path.exists(new_config) and os.path.exists(old_dir_config):
			try:
				shutil.move(old_dir_config, new_config)
				log.info(f"Migrated {old_dir_config} to {new_config}")
			except Exception as e:
				log.error(f"Failed to migrate {old_dir_config}: {e}")
		elif not os.path.exists(new_config) and os.path.exists(old_root_config):
			try:
				shutil.move(old_root_config, new_config)
				log.info(f"Migrated {old_root_config} to {new_config}")
			except Exception as e:
				log.error(f"Failed to migrate {old_root_config}: {e}")

		if not os.path.exists(new_prefs) and os.path.exists(old_dir_prefs):
			try:
				shutil.move(old_dir_prefs, new_prefs)
				log.info(f"Migrated {old_dir_prefs} to {new_prefs}")
			except Exception as e:
				log.error(f"Failed to migrate {old_dir_prefs}: {e}")
		elif not os.path.exists(new_prefs) and os.path.exists(old_root_prefs):
			try:
				shutil.move(old_root_prefs, new_prefs)
				log.info(f"Migrated {old_root_prefs} to {new_prefs}")
			except Exception as e:
				log.error(f"Failed to migrate {old_root_prefs}: {e}")

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

	def load_order(self):
		"""Load custom order and pinned data from JSON file."""
		if os.path.isfile(self.orderPath):
			try:
				with open(self.orderPath, 'r', encoding='utf-8') as f:
					data = json.load(f)
				self.order = data.get("order", {})
				pinned_dict = data.get("pinned", {})
				self.pinned = {cat: set(urls) for cat, urls in pinned_dict.items()}
			except Exception as e:
				log.error(f"Error loading AbsoluteSiteOrder.json: {e}")
				self.order = {}
				self.pinned = {}
		else:
			self.order = {}
			self.pinned = {}

	def save_order(self):
		"""Save custom order and pinned data to JSON file."""
		pinned_serializable = {cat: list(urls) for cat, urls in self.pinned.items()}
		data = {
			"order": self.order,
			"pinned": pinned_serializable
		}
		try:
			with open(self.orderPath, 'w', encoding='utf-8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log.error(f"Error saving AbsoluteSiteOrder.json: {e}")

	def get_last_category(self):
		return self.prefs.get("last_category")

	def set_last_category(self, category):
		if category:
			self.prefs["last_category"] = category
			self.save_prefs()

	def get_all_categories(self):
		return sorted(self.data.keys(), key=str.lower)

	def get_sites_by_category(self, category):
		return self.data.get(category, [])

	def get_ordered_sites(self, category):
		"""
		Return list of [name, url] for a category in display order:
		- Pinned sites appear first, in the order stored in self.order (preserving manual arrangement).
		- Unpinned sites follow, sorted alphabetically by display name (case‑insensitive).
		This method always ensures that unpinned sites are correctly sorted,
		even if the internal order list becomes inconsistent.
		"""
		if category not in self.data:
			return []

		pinned_urls = self.pinned.get(category, set())
		all_sites = self.data[category]
		sites_dict = {url: [name, url] for name, url in all_sites}

		# Get current order list for this category
		current_order = self.order.get(category, [])

		# Build pinned section in the order they appear in current_order
		pinned_sites = []
		pinned_seen = set()
		for url in current_order:
			if url in pinned_urls and url in sites_dict:
				pinned_sites.append(sites_dict[url])
				pinned_seen.add(url)

		# Add any pinned sites not present in current_order (should not happen, but handle gracefully)
		for url in pinned_urls:
			if url not in pinned_seen and url in sites_dict:
				pinned_sites.append(sites_dict[url])
				pinned_seen.add(url)

		# Collect unpinned sites and sort them alphabetically by name (case‑insensitive)
		unpinned_sites = []
		for url, site in sites_dict.items():
			if url not in pinned_urls:
				unpinned_sites.append(site)
		unpinned_sites.sort(key=lambda s: s[0].lower())

		# Combine
		ordered_sites = pinned_sites + unpinned_sites

		# Update self.order to match the computed order (for consistency and future moves)
		new_order = [s[1] for s in ordered_sites]
		if new_order != current_order:
			self.order[category] = new_order
			self.save_order()

		return ordered_sites

	def _reorder_category(self, category):
		"""
		Reconstruct the order list for a category based on current data and pinned set.
		Pinned sites keep their relative order from the existing order (if any);
		unpinned sites are sorted alphabetically by name (case‑insensitive).
		This method is called after modifications to ensure the order list is correct.
		"""
		if category not in self.data:
			return

		current_order = self.order.get(category, [])
		pinned_set = self.pinned.get(category, set())
		sites_dict = {url: name for name, url in self.data[category]}

		# Preserve order of pinned sites from current_order
		pinned_urls = [url for url in current_order if url in pinned_set and url in sites_dict]

		# All URLs in this category
		all_urls = [url for name, url in self.data[category]]

		# Unpinned URLs (exclude pinned)
		unpinned_urls = [url for url in all_urls if url not in pinned_set]
		# Sort by display name (case‑insensitive)
		unpinned_urls.sort(key=lambda url: sites_dict.get(url, "").lower())

		new_order = pinned_urls + unpinned_urls
		self.order[category] = new_order
		self.save_order()

	def get_site_by_url(self, url):
		for cat, sites in self.data.items():
			for name, u in sites:
				if u == url:
					return (cat, name, u)
		return None

	def _find_site_in_category(self, category, url):
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
			self.order[category_name] = []
			self.pinned[category_name] = set()
			self.save_order()
			return True
		return False

	def delete_category(self, category):
		if category not in self.data:
			return False
		del self.data[category]
		if self.prefs.get("last_category") == category:
			self.prefs.pop("last_category", None)
			self.save_prefs()
		self.order.pop(category, None)
		self.pinned.pop(category, None)
		self.save()
		self.save_order()
		return True

	def rename_category(self, old_name, new_name):
		if old_name not in self.data:
			return False
		if new_name in self.data:
			return False
		self.data[new_name] = self.data.pop(old_name)
		if old_name in self.order:
			self.order[new_name] = self.order.pop(old_name)
		if old_name in self.pinned:
			self.pinned[new_name] = self.pinned.pop(old_name)
		if self.prefs.get("last_category") == old_name:
			self.prefs["last_category"] = new_name
			self.save_prefs()
		self.save()
		self.save_order()
		return True

	def add_site(self, category, display_name, url):
		if self._find_site_in_category(category, url) is not None:
			return False
		if category not in self.data:
			self.data[category] = []
		self.data[category].append([display_name, url])
		self.save()
		# Ensure pinned set exists for this category
		if category not in self.pinned:
			self.pinned[category] = set()
		# Reorder the category to maintain alphabetical order for unpinned sites
		self._reorder_category(category)
		return True

	def update_site(self, old_category, old_display_name, old_url, new_category, new_display_name, new_url):
		if old_category not in self.data:
			return False
		old_idx = None
		for idx, (name, url) in enumerate(self.data[old_category]):
			if name == old_display_name and url == old_url:
				old_idx = idx
				break
		if old_idx is None:
			return False

		if new_category != old_category or new_url != old_url:
			if new_category in self.data:
				for idx, (name, url) in enumerate(self.data[new_category]):
					if url == new_url:
						if new_category == old_category and idx == old_idx:
							continue
						return False

		was_pinned = self.is_pinned(old_category, old_url)

		del self.data[old_category][old_idx]

		if old_category in self.order and old_url in self.order[old_category]:
			self.order[old_category].remove(old_url)
		if old_category in self.pinned and old_url in self.pinned[old_category]:
			self.pinned[old_category].remove(old_url)

		if new_category not in self.data:
			self.data[new_category] = []
		self.data[new_category].append([new_display_name, new_url])
		self.save()

		if was_pinned:
			if new_category not in self.pinned:
				self.pinned[new_category] = set()
			self.pinned[new_category].add(new_url)

		self._reorder_category(old_category)
		if new_category != old_category:
			self._reorder_category(new_category)

		return True

	def remove_site(self, category, display_name, url):
		if category not in self.data:
			return False
		for idx, (name, u) in enumerate(self.data[category]):
			if name == display_name and u == url:
				del self.data[category][idx]
				self.save()
				if category in self.order and url in self.order[category]:
					self.order[category].remove(url)
				if category in self.pinned and url in self.pinned[category]:
					self.pinned[category].remove(url)
				self._reorder_category(category)
				return True
		return False

	def is_pinned(self, category, url):
		return category in self.pinned and url in self.pinned[category]

	def pin_site(self, category, url):
		if category not in self.pinned:
			self.pinned[category] = set()
		self.pinned[category].add(url)
		self._reorder_category(category)

	def unpin_site(self, category, url):
		if category in self.pinned and url in self.pinned[category]:
			self.pinned[category].remove(url)
			self._reorder_category(category)

	def move_up(self, category, url):
		if category not in self.order:
			self._reorder_category(category)
		order = self.order[category]
		if url not in order:
			return False
		idx = order.index(url)
		if idx == 0:
			return False
		pinned_set = self.pinned.get(category, set())
		is_pinned = url in pinned_set
		if is_pinned:
			if idx > 0 and order[idx-1] in pinned_set:
				order[idx], order[idx-1] = order[idx-1], order[idx]
				self.save_order()
				return True
			return False
		else:
			if idx > 0 and order[idx-1] in pinned_set:
				return False
			order[idx], order[idx-1] = order[idx-1], order[idx]
			self.save_order()
			return True

	def move_down(self, category, url):
		if category not in self.order:
			self._reorder_category(category)
		order = self.order[category]
		if url not in order:
			return False
		idx = order.index(url)
		if idx == len(order) - 1:
			return False
		pinned_set = self.pinned.get(category, set())
		is_pinned = url in pinned_set
		if is_pinned:
			last_pinned_idx = -1
			for i, u in enumerate(order):
				if u in pinned_set:
					last_pinned_idx = i
			if idx < last_pinned_idx and order[idx+1] in pinned_set:
				order[idx], order[idx+1] = order[idx+1], order[idx]
				self.save_order()
				return True
			return False
		else:
			order[idx], order[idx+1] = order[idx+1], order[idx]
			self.save_order()
			return True

	def move_site_to_category(self, old_category, url, new_category):
		if old_category not in self.data or new_category not in self.data:
			return False
		site_entry = None
		for name, u in self.data[old_category]:
			if u == url:
				site_entry = (name, u)
				break
		if site_entry is None:
			return False
		if self._find_site_in_category(new_category, url) is not None:
			return False
		name, _ = site_entry
		was_pinned = self.is_pinned(old_category, url)

		self.remove_site(old_category, name, url)

		if new_category not in self.data:
			self.data[new_category] = []
		self.data[new_category].append([name, url])
		self.save()

		if was_pinned:
			if new_category not in self.pinned:
				self.pinned[new_category] = set()
			self.pinned[new_category].add(url)

		self._reorder_category(new_category)
		return True