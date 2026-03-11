# __init__.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import addonHandler
import globalPluginHandler
import scriptHandler
import api
import ui
import time
import wx
import re
from .siteManager import SiteManager
from .gui import MainDialog, AddSiteDialog
import gui as nvdaGui

addonHandler.initTranslation()

DOUBLE_TAP_THRESHOLD = 0.4

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Absolute Site")

	def __init__(self):
		super().__init__()
		self.manager = SiteManager()
		self._last_tap_time = 0
		self._tap_count = 0
		# Variable to check if this is the first time opening the dialog after NVDA starts
		self._first_open = True

	def get_current_url(self):
		try:
			focus = api.getFocusObject()
			if hasattr(focus, 'treeInterceptor') and focus.treeInterceptor is not None:
				ti = focus.treeInterceptor
				if hasattr(ti, 'documentConstantIdentifier'):
					url = ti.documentConstantIdentifier
					if url and (url.startswith('http') or url.startswith('https') or url.startswith('file')):
						return url
			if hasattr(focus, 'IAccessibleObject'):
				try:
					url = focus.IAccessibleObject.accValue(0)
					if url and (url.startswith('http') or url.startswith('https') or url.startswith('file')):
						return url
				except:
					pass
			if hasattr(focus, 'UIAElement'):
				try:
					url = focus.UIAElement.CurrentValue
					if url and (url.startswith('http') or url.startswith('https') or url.startswith('file')):
						return url
				except:
					pass
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
		description=_("Open Absolute Site manager (single tap) or Add new site (double tap)"),
		gesture="kb:alt+backspace",
		category=_("Absolute Site")
	)
	def script_openSiteManager(self, gesture):
		current_time = time.time()
		if current_time - self._last_tap_time > DOUBLE_TAP_THRESHOLD:
			self._tap_count = 0
		self._tap_count += 1
		self._last_tap_time = current_time

		def execute_action():
			if self._tap_count == 1:
				# Single tap: open manager dialog
				if self._first_open:
					# First time after NVDA restart -> do not pass last category
					nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager)
				else:
					# Subsequent opens -> pass last category (if any)
					last_cat = self.manager.get_last_category()
					nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager, last_cat)
				self._first_open = False
			elif self._tap_count >= 2:
				# Double tap: open add site dialog
				current_url = self.get_current_url()
				if not current_url:
					ui.message(_("Cannot capture URL. Make sure you are in a browser."))
				else:
					nvdaGui.mainFrame.popupSettingsDialog(AddSiteDialog, self.manager, current_url)
			self._tap_count = 0

		wx.CallLater(int(DOUBLE_TAP_THRESHOLD * 1000), execute_action)