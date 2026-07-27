# mostVisitedManager.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import os
import json
import time
import globalVars
from logHandler import log

class MostVisitedManager:
	def __init__(self):
		self.dataDir = os.path.join(globalVars.appArgs.configPath, "ChaiChaimee", "AbsoluteSite")
		os.makedirs(self.dataDir, exist_ok=True)
		self.dataPath = os.path.join(self.dataDir, "MostVisited.json")
		self.visits = []
		self.pinned = set()
		self.order = []
		self.load()

	def load(self):
		if os.path.isfile(self.dataPath):
			try:
				with open(self.dataPath, 'r', encoding='utf-8') as f:
					data = json.load(f)
				self.visits = data.get("visits", [])
				self.pinned = set(data.get("pinned", []))
				self.order = data.get("order", [])
			except Exception as e:
				log.error(f"Error loading MostVisited.json: {e}")
				self.visits = []
				self.pinned = set()
				self.order = []
		else:
			self.visits = []
			self.pinned = set()
			self.order = []

	def save(self):
		data = {
			"visits": self.visits,
			"pinned": list(self.pinned),
			"order": self.order
		}
		try:
			with open(self.dataPath, 'w', encoding='utf-8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception as e:
			log.error(f"Error saving MostVisited.json: {e}")

	def add_visit(self, url):
		self.visits = [v for v in self.visits if v["url"] != url]
		self.visits.insert(0, {"url": url, "timestamp": time.time()})
		if len(self.visits) > 50:
			self.visits = self.visits[:50]
		self.save()

	def get_ordered_most_visited(self, siteManager):
		site_info = {}
		for category, sites in siteManager.data.items():
			for site in sites:
				url = site["url"]
				site_info[url] = (site["name"], category)

		result = []
		pinned_urls = set(self.pinned)
		ordered_pinned = []
		for url in self.order:
			if url in pinned_urls:
				ordered_pinned.append(url)
				pinned_urls.remove(url)
		ordered_pinned.extend(pinned_urls)

		for url in ordered_pinned:
			if url in site_info:
				name, cat = site_info[url]
				result.append({"display_name": name, "url": url, "category": cat})

		seen_urls = {item["url"] for item in result}
		for visit in self.visits:
			url = visit["url"]
			if url in seen_urls:
				continue
			if url in site_info:
				name, cat = site_info[url]
				result.append({"display_name": name, "url": url, "category": cat})
				seen_urls.add(url)
		return result

	def pin(self, url):
		self.pinned.add(url)
		if url in self.order:
			self.order.remove(url)
		insert_index = 0
		for i, u in enumerate(self.order):
			if u in self.pinned:
				insert_index = i
				break
		self.order.insert(insert_index, url)
		self.save()

	def unpin(self, url):
		self.pinned.discard(url)
		self.save()

	def move_up(self, url):
		if url not in self.order:
			self._add_to_order(url)
		idx = self.order.index(url)
		if idx == 0:
			return False
		is_pinned = url in self.pinned
		if is_pinned:
			if self.order[idx-1] in self.pinned:
				self.order[idx], self.order[idx-1] = self.order[idx-1], self.order[idx]
				self.save()
				return True
			return False
		else:
			if self.order[idx-1] not in self.pinned:
				self.order[idx], self.order[idx-1] = self.order[idx-1], self.order[idx]
				self.save()
				return True
			return False

	def move_down(self, url):
		if url not in self.order:
			self._add_to_order(url)
		idx = self.order.index(url)
		if idx == len(self.order) - 1:
			return False
		is_pinned = url in self.pinned
		if is_pinned:
			if self.order[idx+1] in self.pinned:
				self.order[idx], self.order[idx+1] = self.order[idx+1], self.order[idx]
				self.save()
				return True
			return False
		else:
			if self.order[idx+1] not in self.pinned:
				self.order[idx], self.order[idx+1] = self.order[idx+1], self.order[idx]
				self.save()
				return True
			return False

	def _add_to_order(self, url):
		if url in self.pinned:
			last_pinned_idx = -1
			for i, u in enumerate(self.order):
				if u in self.pinned:
					last_pinned_idx = i
			if last_pinned_idx == -1:
				self.order.insert(0, url)
			else:
				self.order.insert(last_pinned_idx + 1, url)
		else:
			self.order.append(url)
		self.save()

	def remove_url(self, url):
		self.visits = [v for v in self.visits if v["url"] != url]
		self.pinned.discard(url)
		if url in self.order:
			self.order.remove(url)
		self.save()

	def terminate(self):
		self.save()