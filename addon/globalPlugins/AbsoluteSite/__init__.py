# __init__.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import addonHandler
import globalPluginHandler
import scriptHandler
import api
import ui
import time
import core
import re
from .siteManager import SiteManager
from .mostVisitedManager import MostVisitedManager
from .gui import MainDialog, AddSiteDialog, MostVisitedDialog, SearchDialog
import gui as nvdaGui

addonHandler.initTranslation()

MULTI_TAP_THRESHOLD = 0.4

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Absolute Site")

	def __init__(self):
		super().__init__()
		self.manager = SiteManager()
		self.mostVisitedManager = MostVisitedManager()
		self._last_tap_time = 0
		self._tap_count = 0
		self._multiTapTimer = None

	def _get_document_url_from_object(self, obj):
		"""Traverse up the parent chain to find a document object and return its URL."""
		current = obj
		while current is not None:
			try:
				# Check if current object is a browse mode document itself
				if hasattr(current, 'documentConstantIdentifier'):
					url = current.documentConstantIdentifier
					if url:
						return url

				# Check if current object has a treeInterceptor (browse mode)
				if hasattr(current, 'treeInterceptor') and current.treeInterceptor is not None:
					url = current.treeInterceptor.documentConstantIdentifier
					if url:
						return url
			except Exception:
				pass

			try:
				current = current.parent
			except Exception:
				break
		return None

	def get_current_url(self):
		try:
			focus = api.getFocusObject()

			# First, try to get URL from the document via treeInterceptor or parent chain
			url = self._get_document_url_from_object(focus)
			if url and (url.startswith('http') or url.startswith('https') or url.startswith('file')):
				return url

			# Fallback to IAccessible accValue (some browsers store URL there)
			if hasattr(focus, 'IAccessibleObject'):
				try:
					url = focus.IAccessibleObject.accValue(0)
					if url and (url.startswith('http') or url.startswith('https') or url.startswith('file')):
						return url
				except Exception:
					pass

			# Fallback to UIAElement (for UIA-based browsers)
			if hasattr(focus, 'UIAElement'):
				try:
					url = focus.UIAElement.CurrentValue
					if url and (url.startswith('http') or url.startswith('https') or url.startswith('file')):
						return url
				except Exception:
					pass

			# Fallback to window text regex
			if hasattr(focus, 'windowText'):
				window_text = focus.windowText
				url_pattern = r'https?://[^\s]+|file:///[^\s]+'
				match = re.search(url_pattern, window_text)
				if match:
					return match.group(0)

			return None
		except Exception:
			return None

	@scriptHandler.script(
		description=_("Open Absolute Site manager (single tap), Add new site (double tap), or Most Visited (triple tap)"),
		gesture="kb:alt+backspace",
		category=_("Absolute Site")
	)
	def script_absoluteSite(self, gesture):
		current_time = time.time()
		if self._multiTapTimer:
			self._multiTapTimer.Stop()
			self._multiTapTimer = None
		if current_time - self._last_tap_time > MULTI_TAP_THRESHOLD:
			self._tap_count = 0
		self._tap_count += 1
		self._last_tap_time = current_time

		def execute_action():
			try:
				if self._tap_count == 1:
					last_cat = self.manager.get_last_category()
					nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager, self.mostVisitedManager, last_cat)
				elif self._tap_count == 2:
					current_url = self.get_current_url()
					if not current_url:
						ui.message(_("Cannot capture URL. Make sure you are in a browser."))
					else:
						nvdaGui.mainFrame.popupSettingsDialog(AddSiteDialog, self.manager, current_url)
				elif self._tap_count >= 3:
					nvdaGui.mainFrame.popupSettingsDialog(MostVisitedDialog, self.mostVisitedManager, self.manager)
			finally:
				self._tap_count = 0

		self._multiTapTimer = core.callLater(int(MULTI_TAP_THRESHOLD * 1000), execute_action)

	@scriptHandler.script(
		description=_("Search the web via Google"),
		gesture="kb:windows+alt+backspace",
		category=_("Absolute Site")
	)
	def script_searchSites(self, gesture):
		nvdaGui.mainFrame.popupSettingsDialog(SearchDialog, self.mostVisitedManager)

	def terminate(self):
		self.manager.terminate()
		self.mostVisitedManager.terminate()

