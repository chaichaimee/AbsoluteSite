# siteManager.py

import os
import json
import shutil
import uuid
import globalVars
from logHandler import log

class SiteManager:
	def __init__(self):
		self.dataDir = os.path.join(globalVars.appArgs.configPath, "ChaiChaimee", "AbsoluteSite")
		try:
			os.makedirs(self.dataDir, exist_ok=True)
		except Exception as e:
			log.error(f"Could not create data directory {self.dataDir}: {e}")

		self.configPath = os.path.join(self.dataDir, "AbsoluteSites.json")
		self.prefsPath = os.path.join(self.dataDir, "AbsoluteSitePrefs.json")
		self.orderPath = os.path.join(self.dataDir, "AbsoluteSiteOrder.json")

		self._migrate_old_files()

		self.data = {}
		self.prefs = {}
		self.order = {}
		self.pinned = {}

		self.load()
		self.load_prefs()
		self.load_order()
		self._migrate_legacy_data()

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
		if os.path.isfile(self.orderPath):
			try:
				with open(self.orderPath, 'r', encoding='utf-8') as f:
					data = json.load(f)
				self.order = data.get("order", {})
				pinned_dict = data.get("pinned", {})
				self.pinned = {cat: set(ids) for cat, ids in pinned_dict.items()}
			except Exception as e:
				log.error(f"Error loading AbsoluteSiteOrder.json: {e}")
				self.order = {}
				self.pinned = {}
		else:
			self.order = {}
			self.pinned = {}

	def save_order(self):
		pinned_serializable = {cat: list(ids) for cat, ids in self.pinned.items()}
		data = {
			"order": self.order,
			"pinned": pinned_serializable
		}
		try:
			with open(self.orderPath, 'w', encoding='utf-8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log.error(f"Error saving AbsoluteSiteOrder.json: {e}")

	def _migrate_legacy_data(self):
		need_save = False
		for category, sites in self.data.items():
			if sites and isinstance(sites[0], list):
				new_sites = []
				for name, url in sites:
					site_id = str(uuid.uuid4())
					new_sites.append({"id": site_id, "name": name, "url": url})
				self.data[category] = new_sites
				need_save = True
				if category not in self.order:
					self.order[category] = [site["id"] for site in new_sites]
				if category not in self.pinned:
					self.pinned[category] = set()
				need_save = True
		if need_save:
			self.save()
			self.save_order()

	def get_last_category(self):
		return self.prefs.get("last_category")

	def set_last_category(self, category):
		if category:
			self.prefs["last_category"] = category
			self.save_prefs()

	def get_category_browser(self, category):
		return self.prefs.get("category_browser", {}).get(category, "Default")

	def set_category_browser(self, category, browser_name):
		if not category:
			return
		categoryBrowsers = self.prefs.get("category_browser", {})
		categoryBrowsers[category] = browser_name
		self.prefs["category_browser"] = categoryBrowsers
		self.save_prefs()

	def get_all_categories(self):
		return sorted(self.data.keys(), key=str.lower)

	def get_sites_by_category(self, category):
		if category not in self.data:
			return []
		return [(site["name"], site["url"]) for site in self.data[category]]

	def get_ordered_sites(self, category):
		if category not in self.data:
			return []

		site_map = {site["id"]: (site["name"], site["url"]) for site in self.data[category]}
		current_order = self.order.get(category, [])
		pinned_ids = self.pinned.get(category, set())

		ordered_ids = []
		seen_ids = set()

		for site_id in current_order:
			if site_id in site_map:
				ordered_ids.append(site_id)
				seen_ids.add(site_id)

		for site_id in pinned_ids:
			if site_id not in seen_ids and site_id in site_map:
				ordered_ids.append(site_id)
				seen_ids.add(site_id)

		for site_id, (name, url) in site_map.items():
			if site_id not in seen_ids:
				ordered_ids.append(site_id)
				seen_ids.add(site_id)

		unpinned_ids = [sid for sid in ordered_ids if sid not in pinned_ids]
		unpinned_ids.sort(key=lambda sid: site_map[sid][0].lower())

		final_ids = [sid for sid in ordered_ids if sid in pinned_ids] + unpinned_ids
		self.order[category] = final_ids
		self.save_order()

		return [site_map[sid] for sid in final_ids]

	def _reorder_category(self, category):
		if category not in self.data:
			return

		site_ids = [site["id"] for site in self.data[category]]
		pinned_ids = self.pinned.get(category, set())
		current_order = self.order.get(category, [])
		preserved = [sid for sid in current_order if sid in site_ids and sid in pinned_ids]
		remaining = [sid for sid in site_ids if sid not in pinned_ids]
		remaining.sort(key=lambda sid: self._get_site_name_by_id(category, sid).lower())
		new_order = preserved + remaining
		if new_order != current_order:
			self.order[category] = new_order
			self.save_order()

	def _get_site_name_by_id(self, category, site_id):
		for site in self.data.get(category, []):
			if site["id"] == site_id:
				return site["name"]
		return ""

	def get_site_by_url(self, url):
		for cat, sites in self.data.items():
			for site in sites:
				if site["url"] == url:
					return (cat, site["name"], site["url"])
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
		prefsChanged = False
		if self.prefs.get("last_category") == category:
			self.prefs.pop("last_category", None)
			prefsChanged = True
		categoryBrowsers = self.prefs.get("category_browser", {})
		if category in categoryBrowsers:
			categoryBrowsers.pop(category, None)
			prefsChanged = True
		if prefsChanged:
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
		prefsChanged = False
		if self.prefs.get("last_category") == old_name:
			self.prefs["last_category"] = new_name
			prefsChanged = True
		categoryBrowsers = self.prefs.get("category_browser", {})
		if old_name in categoryBrowsers:
			categoryBrowsers[new_name] = categoryBrowsers.pop(old_name)
			prefsChanged = True
		if prefsChanged:
			self.save_prefs()
		self.save()
		self.save_order()
		return True

	def add_site(self, category, display_name, url):
		if category not in self.data:
			self.data[category] = []
		site_id = str(uuid.uuid4())
		self.data[category].append({"id": site_id, "name": display_name, "url": url})
		self.save()
		if category not in self.pinned:
			self.pinned[category] = set()
		self._reorder_category(category)
		return True

	def update_site(self, old_category, old_display_name, old_url, new_category, new_display_name, new_url):
		if old_category not in self.data:
			return False

		target_site = None
		target_index = None
		for idx, site in enumerate(self.data[old_category]):
			if site["name"] == old_display_name and site["url"] == old_url:
				target_site = site
				target_index = idx
				break
		if target_site is None:
			return False

		was_pinned = (old_category in self.pinned and target_site["id"] in self.pinned[old_category])
		site_id = target_site["id"]

		del self.data[old_category][target_index]
		if old_category in self.order and site_id in self.order.get(old_category, []):
			self.order[old_category].remove(site_id)
		if old_category in self.pinned and site_id in self.pinned.get(old_category, set()):
			self.pinned[old_category].remove(site_id)

		if new_category not in self.data:
			self.data[new_category] = []
		self.data[new_category].append({"id": site_id, "name": new_display_name, "url": new_url})
		self.save()

		if was_pinned:
			if new_category not in self.pinned:
				self.pinned[new_category] = set()
			self.pinned[new_category].add(site_id)

		self._reorder_category(old_category)
		if new_category != old_category:
			self._reorder_category(new_category)

		return True

	def remove_site(self, category, display_name, url):
		if category not in self.data:
			return False
		for idx, site in enumerate(self.data[category]):
			if site["name"] == display_name and site["url"] == url:
				site_id = site["id"]
				del self.data[category][idx]
				self.save()
				if category in self.order and site_id in self.order[category]:
					self.order[category].remove(site_id)
				if category in self.pinned and site_id in self.pinned.get(category, set()):
					self.pinned[category].remove(site_id)
				self._reorder_category(category)
				return True
		return False

	def is_pinned(self, category, url):
		for site in self.data.get(category, []):
			if site["url"] == url:
				return category in self.pinned and site["id"] in self.pinned.get(category, set())
		return False

	def pin_site(self, category, url):
		for site in self.data.get(category, []):
			if site["url"] == url:
				site_id = site["id"]
				if category not in self.pinned:
					self.pinned[category] = set()
				self.pinned[category].add(site_id)
				self._reorder_category(category)
				return True
		return False

	def unpin_site(self, category, url):
		for site in self.data.get(category, []):
			if site["url"] == url:
				site_id = site["id"]
				if category in self.pinned and site_id in self.pinned.get(category, set()):
					self.pinned[category].remove(site_id)
					self._reorder_category(category)
				return True
		return False

	def _get_site_id_by_url(self, category, url):
		for site in self.data.get(category, []):
			if site["url"] == url:
				return site["id"]
		return None

	def move_up(self, category, url):
		site_id = self._get_site_id_by_url(category, url)
		if site_id is None:
			return False

		if category not in self.order:
			self._reorder_category(category)
		order = self.order[category]
		if site_id not in order:
			return False
		idx = order.index(site_id)
		if idx == 0:
			return False
		pinned_set = self.pinned.get(category, set())
		if site_id in pinned_set:
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
		site_id = self._get_site_id_by_url(category, url)
		if site_id is None:
			return False

		if category not in self.order:
			self._reorder_category(category)
		order = self.order[category]
		if site_id not in order:
			return False
		idx = order.index(site_id)
		if idx == len(order) - 1:
			return False
		pinned_set = self.pinned.get(category, set())
		if site_id in pinned_set:
			last_pinned_idx = -1
			for i, sid in enumerate(order):
				if sid in pinned_set:
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

		source_site = None
		for site in self.data[old_category]:
			if site["url"] == url:
				source_site = site
				break
		if source_site is None:
			return False

		site_id = source_site["id"]
		name = source_site["name"]
		was_pinned = (old_category in self.pinned and site_id in self.pinned.get(old_category, set()))

		self.remove_site(old_category, name, url)
		self.data[new_category].append({"id": site_id, "name": name, "url": url})
		self.save()

		if was_pinned:
			if new_category not in self.pinned:
				self.pinned[new_category] = set()
			self.pinned[new_category].add(site_id)

		self._reorder_category(new_category)
		return True

	def terminate(self):
		self.save()
		self.save_prefs()
		self.save_order()