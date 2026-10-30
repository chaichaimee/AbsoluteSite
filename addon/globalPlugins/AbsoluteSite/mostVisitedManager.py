# mostVisitedManager.py

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
		self.pinned = {}
		self.load()

	def load(self):
		self.visits = []
		self.pinned = {}
		if not os.path.isfile(self.dataPath):
			return
		try:
			with open(self.dataPath, 'r', encoding='utf-8') as f:
				data = json.load(f)
			self.visits = data.get("visits", [])
			pinnedData = data.get("pinned", {})
			if isinstance(pinnedData, dict):
				self.pinned = {str(u): int(p) for u, p in pinnedData.items()}
			else:
				legacyOrder = [u for u in data.get("order", []) if u in pinnedData]
				legacyOrder.extend(u for u in pinnedData if u not in legacyOrder)
				self.pinned = {u: i for i, u in enumerate(legacyOrder)}
		except Exception as e:
			log.error(f"Error loading MostVisited.json: {e}")
			self.visits = []
			self.pinned = {}

	def save(self):
		data = {
			"visits": self.visits,
			"pinned": self.pinned
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

	def _siteInfo(self, siteManager):
		siteInfo = {}
		for category, sites in siteManager.data.items():
			for site in sites:
				siteInfo[site["url"]] = (site["name"], category)
		return siteInfo

	def _unpinnedUrls(self, siteInfo):
		seenUrls = set()
		unpinnedUrls = []
		for visit in self.visits:
			url = visit["url"]
			if url in seenUrls or url in self.pinned or url not in siteInfo:
				continue
			seenUrls.add(url)
			unpinnedUrls.append(url)
		return unpinnedUrls

	def get_ordered_most_visited(self, siteManager):
		siteInfo = self._siteInfo(siteManager)
		ordered = self._unpinnedUrls(siteInfo)
		pinnedSlots = sorted(
			((pos, url) for url, pos in self.pinned.items() if url in siteInfo),
			key=lambda slot: slot[0]
		)
		for pos, url in pinnedSlots:
			ordered.insert(min(max(pos, 0), len(ordered)), url)
		return [
			{"display_name": siteInfo[url][0], "url": url, "category": siteInfo[url][1]}
			for url in ordered
		]

	def _normalizePinned(self, siteManager):
		ordered = self.get_ordered_most_visited(siteManager)
		for index, site in enumerate(ordered):
			if site["url"] in self.pinned:
				self.pinned[site["url"]] = index

	def pin(self, url, position, siteManager):
		self.pinned[url] = max(int(position), 0)
		self._normalizePinned(siteManager)
		self.save()

	def unpin(self, url):
		if self.pinned.pop(url, None) is not None:
			self.save()

	def is_pinned(self, url):
		return url in self.pinned

	def _movePinned(self, url, siteManager, step):
		self._normalizePinned(siteManager)
		pinnedUrls = sorted(self.pinned, key=lambda u: self.pinned[u])
		if url not in pinnedUrls:
			return False
		targetIndex = pinnedUrls.index(url) + step
		if targetIndex < 0 or targetIndex >= len(pinnedUrls):
			return False
		otherUrl = pinnedUrls[targetIndex]
		self.pinned[url], self.pinned[otherUrl] = self.pinned[otherUrl], self.pinned[url]
		self.save()
		return True

	def _moveUnpinned(self, url, siteManager, step):
		unpinnedUrls = self._unpinnedUrls(self._siteInfo(siteManager))
		if url not in unpinnedUrls:
			return False
		targetIndex = unpinnedUrls.index(url) + step
		if targetIndex < 0 or targetIndex >= len(unpinnedUrls):
			return False
		visitUrls = [v["url"] for v in self.visits]
		firstIdx = visitUrls.index(url)
		secondIdx = visitUrls.index(unpinnedUrls[targetIndex])
		self.visits[firstIdx], self.visits[secondIdx] = self.visits[secondIdx], self.visits[firstIdx]
		self.save()
		return True

	def _move(self, url, siteManager, step):
		if url in self.pinned:
			return self._movePinned(url, siteManager, step)
		return self._moveUnpinned(url, siteManager, step)

	def move_up(self, url, siteManager):
		return self._move(url, siteManager, -1)

	def move_down(self, url, siteManager):
		return self._move(url, siteManager, 1)

	def clear_unpinned(self):
		removedCount = len([v for v in self.visits if v["url"] not in self.pinned])
		self.visits = [v for v in self.visits if v["url"] in self.pinned]
		self.save()
		return removedCount

	def remove_url(self, url):
		self.visits = [v for v in self.visits if v["url"] != url]
		self.pinned.pop(url, None)
		self.save()

	def terminate(self):
		self.save()