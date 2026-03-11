# gui.py

import wx
import addonHandler
import ui
import gui as nvdaGui
import os
import re
import subprocess
import winreg
from .siteManager import SiteManager

addonHandler.initTranslation()

# Fallback paths for browsers (used if registry lookup fails)
FALLBACK_BROWSER_PATHS = {
	"Chrome": [
		os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
		os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
		os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
	],
	"Firefox": [
		os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
		os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
		os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe")
	],
	"Edge": [
		os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
		os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
		os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
	],
	"Brave": [
		os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
		os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
		os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe")
	],
	"Opera": [
		os.path.expandvars(r"%ProgramFiles%\Opera\launcher.exe"),
		os.path.expandvars(r"%ProgramFiles(x86)%\Opera\launcher.exe"),
		os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\launcher.exe")
	],
	"Vivaldi": [
		os.path.expandvars(r"%ProgramFiles%\Vivaldi\Application\vivaldi.exe"),
		os.path.expandvars(r"%ProgramFiles(x86)%\Vivaldi\Application\vivaldi.exe"),
		os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe")
	]
}

def get_installed_browsers():
	"""
	Detect installed browsers using Windows registry first,
	then fallback to checking common file system paths.
	Returns a list of (display_name, executable_path) sorted by popularity.
	"""
	browsers = []
	found_paths = set()

	# Registry keys for each browser (App Paths)
	reg_keys = {
		"Chrome": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
		"Firefox": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe",
		"Edge": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
		"Brave": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
		"Opera": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\opera.exe",
		"Vivaldi": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\vivaldi.exe",
	}

	# Alternative registry keys for browsers that use different executable names
	alt_reg_keys = {
		"Opera": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\launcher.exe"
	}

	# Helper to query registry from both HKLM and HKCU
	def query_registry(key_path):
		for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
			try:
				with winreg.OpenKey(hive, key_path) as key:
					value, _ = winreg.QueryValueEx(key, "")
					if value and os.path.isfile(value):
						return value
			except FileNotFoundError:
				continue
		return None

	# First pass: try main registry keys
	for browser_name, key in reg_keys.items():
		path = query_registry(key)
		if path and path not in found_paths:
			browsers.append((browser_name, path))
			found_paths.add(path)

	# Second pass: try alternative keys for browsers not found yet
	for browser_name, key in alt_reg_keys.items():
		if any(b[0] == browser_name for b in browsers):
			continue
		path = query_registry(key)
		if path and path not in found_paths:
			browsers.append((browser_name, path))
			found_paths.add(path)

	# Final pass: fallback to file system paths for browsers still missing
	for browser_name, paths in FALLBACK_BROWSER_PATHS.items():
		if any(b[0] == browser_name for b in browsers):
			continue
		for path in paths:
			if os.path.isfile(path) and path not in found_paths:
				browsers.append((browser_name, path))
				found_paths.add(path)
				break

	# Sort browsers by desired order (popularity)
	desired_order = ["Chrome", "Firefox", "Edge", "Brave", "Opera", "Vivaldi"]
	browser_dict = dict(browsers)
	ordered = []
	for name in desired_order:
		if name in browser_dict:
			ordered.append((name, browser_dict[name]))
	return ordered

def open_with_browser(url, browser_exe):
	"""Open URL with specified browser executable."""
	try:
		subprocess.Popen([browser_exe, url])
	except Exception as e:
		wx.MessageBox(_("Failed to open URL with browser: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)

class MainDialog(wx.Dialog):
	def __init__(self, parent, manager, selected_category=None):
		super().__init__(parent, title=_("Absolute Site"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
		self.manager = manager
		self.selected_category = selected_category

		# Timer for auto-close after 15 seconds of inactivity
		self.autoCloseTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onAutoCloseTimer, self.autoCloseTimer)
		self.Bind(wx.EVT_ACTIVATE, self.onActivate)

		self._initUI()
		self._bindEvents()
		self._populateCategories()
		if self.selected_category and self.selected_category in self.manager.get_all_categories():
			self.categoryCombo.SetStringSelection(self.selected_category)
		elif self.categoryCombo.GetCount() > 0:
			self.categoryCombo.SetSelection(0)
		self._updateSiteList()
		wx.CallAfter(self.resetAutoCloseTimer)
		wx.CallAfter(self.siteList.SetFocus)

	def resetAutoCloseTimer(self):
		"""Restart the auto-close timer."""
		if self.autoCloseTimer:
			self.autoCloseTimer.Stop()
			self.autoCloseTimer.Start(15000, wx.TIMER_ONE_SHOT)

	def onActivate(self, evt):
		"""Handle dialog activation/deactivation."""
		if evt.GetActive():
			# Dialog gained focus: reset timer
			self.resetAutoCloseTimer()
		# else: dialog lost focus (e.g., switched to another app) – timer continues running
		evt.Skip()

	def onAutoCloseTimer(self, evt):
		"""Close the dialog when timer expires."""
		self.Close()

	def _initUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		catSizer = wx.BoxSizer(wx.HORIZONTAL)
		catSizer.Add(wx.StaticText(self, label=_("Category:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.categoryCombo = wx.ComboBox(self, choices=[], style=wx.CB_READONLY)
		catSizer.Add(self.categoryCombo, 1, wx.EXPAND)
		mainSizer.Add(catSizer, 0, wx.EXPAND | wx.ALL, 5)

		self.siteList = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN)
		self.siteList.InsertColumn(0, _("Name"), width=250)
		self.siteList.InsertColumn(1, _("URL"), width=400)
		mainSizer.Add(self.siteList, 1, wx.EXPAND | wx.ALL, 5)

		self.showPathsCheck = wx.CheckBox(self, label=_("Show paths"))
		self.showPathsCheck.SetValue(False)
		mainSizer.Add(self.showPathsCheck, 0, wx.ALL, 5)

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.addSiteBtn = wx.Button(self, label=_("&Add Site"))
		self.editBtn = wx.Button(self, label=_("&Edit Site"))
		self.deleteBtn = wx.Button(self, label=_("&Delete Site"))
		self.addCategoryBtn = wx.Button(self, label=_("&Add Category"))
		self.editCategoryBtn = wx.Button(self, label=_("&Edit Category"))
		self.exitBtn = wx.Button(self, wx.ID_CLOSE, label=_("E&xit"))

		btnSizer.Add(self.addSiteBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.editBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.deleteBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.addCategoryBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.editCategoryBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.exitBtn, 0)

		mainSizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

		self.SetSizer(mainSizer)
		self.SetMinSize((700, 500))
		self.Fit()

	def _bindEvents(self):
		self.categoryCombo.Bind(wx.EVT_COMBOBOX, self.onCategoryChange)
		self.categoryCombo.Bind(wx.EVT_CONTEXT_MENU, self.onCategoryContextMenu)
		self.categoryCombo.Bind(wx.EVT_KEY_DOWN, self.onCategoryKeyDown)
		self.siteList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onOpenUrl)
		self.siteList.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
		self.siteList.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.showPathsCheck.Bind(wx.EVT_CHECKBOX, self.onShowPathsChanged)
		self.addSiteBtn.Bind(wx.EVT_BUTTON, self.onAddSite)
		self.editBtn.Bind(wx.EVT_BUTTON, self.onEdit)
		self.deleteBtn.Bind(wx.EVT_BUTTON, self.onDelete)
		self.addCategoryBtn.Bind(wx.EVT_BUTTON, self.onAddCategory)
		self.editCategoryBtn.Bind(wx.EVT_BUTTON, self.onEditCategory)
		self.exitBtn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)

	def _populateCategories(self):
		cats = self.manager.get_all_categories()
		self.categoryCombo.Clear()
		self.categoryCombo.AppendItems(cats)

	def _updateSiteList(self):
		self.siteList.DeleteAllItems()
		category = self.categoryCombo.GetStringSelection()
		if not category:
			return
		sites = self.manager.get_ordered_sites(category)
		show_paths = self.showPathsCheck.GetValue()
		for i, (name, url) in enumerate(sites):
			if show_paths:
				self.siteList.InsertItem(i, f"{name}; URL: {url}")
			else:
				self.siteList.InsertItem(i, name)
			self.siteList.SetItemData(i, i)
		self.current_sites = sites
		if self.siteList.GetItemCount() > 0:
			self.siteList.Select(0)
			self.siteList.Focus(0)
		self._updateButtons()

	def _updateButtons(self):
		has_selection = self.siteList.GetFirstSelected() != -1
		self.editBtn.Enable(has_selection)
		self.deleteBtn.Enable(has_selection)
		category_selected = bool(self.categoryCombo.GetStringSelection())
		self.addSiteBtn.Enable(category_selected)

	def onShowPathsChanged(self, evt):
		self.resetAutoCloseTimer()
		self._updateSiteList()

	def onCategoryChange(self, evt):
		self.resetAutoCloseTimer()
		self._updateSiteList()
		self._updateButtons()

	def onCategoryContextMenu(self, evt):
		self.resetAutoCloseTimer()
		menu = wx.Menu()
		addItem = menu.Append(wx.ID_ANY, _("&Add Category"))
		editItem = menu.Append(wx.ID_ANY, _("&Edit Category"))
		deleteItem = menu.Append(wx.ID_ANY, _("&Delete Category"))
		self.Bind(wx.EVT_MENU, self.onAddCategory, addItem)
		self.Bind(wx.EVT_MENU, self.onEditCategory, editItem)
		self.Bind(wx.EVT_MENU, self.onDeleteCategory, deleteItem)
		self.categoryCombo.PopupMenu(menu)
		menu.Destroy()

	def onCategoryKeyDown(self, evt):
		self.resetAutoCloseTimer()
		if evt.GetKeyCode() == wx.WXK_DELETE:
			self.onDeleteCategory(None)
		else:
			evt.Skip()

	def onEditCategory(self, evt):
		self.resetAutoCloseTimer()
		current_cat = self.categoryCombo.GetStringSelection()
		if not current_cat:
			wx.MessageBox(_("No category selected."), _("Error"), wx.OK | wx.ICON_ERROR)
			return
		# Stop timer while modal dialog is open
		self.autoCloseTimer.Stop()
		dlg = wx.TextEntryDialog(self, _("Enter new name for category '{}':").format(current_cat), _("Edit Category"))
		if dlg.ShowModal() == wx.ID_OK:
			new_cat = dlg.GetValue().strip()
			if not new_cat:
				wx.MessageBox(_("Category name cannot be empty."), _("Error"), wx.OK | wx.ICON_ERROR)
				dlg.Destroy()
				self.resetAutoCloseTimer()
				return
			if new_cat == current_cat:
				dlg.Destroy()
				self.resetAutoCloseTimer()
				return
			if self.manager.rename_category(current_cat, new_cat):
				self._populateCategories()
				self.categoryCombo.SetStringSelection(new_cat)
				self._updateSiteList()
			else:
				wx.MessageBox(_("Category '{}' already exists or invalid.").format(new_cat), _("Error"), wx.OK | wx.ICON_ERROR)
		dlg.Destroy()
		self.resetAutoCloseTimer()

	def onDeleteCategory(self, evt):
		self.resetAutoCloseTimer()
		current_cat = self.categoryCombo.GetStringSelection()
		if not current_cat:
			wx.MessageBox(_("No category selected."), _("Error"), wx.OK | wx.ICON_ERROR)
			return
		# Stop timer while modal dialog is open
		self.autoCloseTimer.Stop()
		if wx.MessageBox(_("Are you sure you want to delete category '{}' and all its sites?").format(current_cat),
						 _("Confirm Delete"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			if self.manager.delete_category(current_cat):
				self._populateCategories()
				if self.categoryCombo.GetCount() > 0:
					self.categoryCombo.SetSelection(0)
				else:
					self.categoryCombo.Clear()
				self._updateSiteList()
			else:
				wx.MessageBox(_("Failed to delete category."), _("Error"), wx.OK | wx.ICON_ERROR)
		self.resetAutoCloseTimer()

	def onContextMenu(self, evt):
		idx = self.siteList.GetFirstSelected()
		if idx == -1:
			return
		category = self.categoryCombo.GetStringSelection()
		site = self._get_selected_site()
		if not site:
			return
		name, url = site

		menu = wx.Menu()

		# Pin/Unpin (first item)
		if self.manager.is_pinned(category, url):
			pinLabel = _("&Unpin")
		else:
			pinLabel = _("&Pin to top")
		pinItem = menu.Append(wx.ID_ANY, pinLabel)

		# Move Up / Down
		upItem = menu.Append(wx.ID_ANY, _("Move &Up"))
		downItem = menu.Append(wx.ID_ANY, _("Move &Down"))

		# Edit and Delete
		editItem = menu.Append(wx.ID_ANY, _("&Edit"))
		deleteItem = menu.Append(wx.ID_ANY, _("&Delete"))

		menu.AppendSeparator()

		# Open with submenu
		openWithMenu = wx.Menu()
		browsers = get_installed_browsers()
		for browser_name, exe_path in browsers:
			item = openWithMenu.Append(wx.ID_ANY, browser_name)
			self.Bind(wx.EVT_MENU, lambda evt, path=exe_path: self.onOpenWith(url, path), item)
		if not browsers:
			noBrowserItem = openWithMenu.Append(wx.ID_ANY, _("No browsers found"))
			noBrowserItem.Enable(False)
		openWithItem = menu.AppendSubMenu(openWithMenu, _("&Open with"))

		# Move to category submenu
		moveMenu = wx.Menu()
		categories = self.manager.get_all_categories()
		for cat in categories:
			if cat != category:
				item = moveMenu.Append(wx.ID_ANY, cat)
				self.Bind(wx.EVT_MENU, lambda evt, c=cat: self.onMoveToCategory(c), item)
		moveItem = menu.AppendSubMenu(moveMenu, _("&Move to category"))

		# Bind events
		self.Bind(wx.EVT_MENU, lambda e: self.onTogglePin(category, url), pinItem)
		self.Bind(wx.EVT_MENU, lambda e: self.onMoveUp(category, url), upItem)
		self.Bind(wx.EVT_MENU, lambda e: self.onMoveDown(category, url), downItem)
		self.Bind(wx.EVT_MENU, self.onEdit, editItem)
		self.Bind(wx.EVT_MENU, self.onDelete, deleteItem)

		self.siteList.PopupMenu(menu)
		menu.Destroy()

	def onOpenWith(self, url, browser_exe):
		self.resetAutoCloseTimer()
		open_with_browser(url, browser_exe)

	def onKeyDown(self, evt):
		self.resetAutoCloseTimer()
		if evt.GetKeyCode() == wx.WXK_DELETE:
			self.onDelete(None)
		else:
			evt.Skip()

	def onCharHook(self, evt):
		self.resetAutoCloseTimer()
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.Close()
		else:
			evt.Skip()

	def _get_selected_site(self):
		idx = self.siteList.GetFirstSelected()
		if idx == -1:
			return None
		category = self.categoryCombo.GetStringSelection()
		if hasattr(self, 'current_sites') and idx < len(self.current_sites):
			return self.current_sites[idx]
		return None

	def onOpenUrl(self, evt):
		site = self._get_selected_site()
		if site:
			_, url = site
			try:
				os.startfile(url)
			except Exception as e:
				wx.MessageBox(_("Failed to open URL: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)
			current_category = self.categoryCombo.GetStringSelection()
			self.manager.set_last_category(current_category)
			self.Close()

	def onAddSite(self, evt):
		self.resetAutoCloseTimer()
		category = self.categoryCombo.GetStringSelection()
		if not category:
			wx.MessageBox(_("Please select a category first."), _("Error"), wx.OK | wx.ICON_ERROR)
			return
		# Stop timer while modal dialog is open
		self.autoCloseTimer.Stop()
		dlg = AddSiteDialog(self, self.manager, category=category, url=None, display_name=None, edit_mode=False)
		if dlg.ShowModal() == wx.ID_OK:
			self._updateSiteList()
		dlg.Destroy()
		self.resetAutoCloseTimer()

	def onEdit(self, evt):
		self.resetAutoCloseTimer()
		site = self._get_selected_site()
		if not site:
			return
		name, url = site
		category = self.categoryCombo.GetStringSelection()
		# Stop timer while modal dialog is open
		self.autoCloseTimer.Stop()
		dlg = AddSiteDialog(self, self.manager, category=category, display_name=name, url=url, edit_mode=True)
		if dlg.ShowModal() == wx.ID_OK:
			self._updateSiteList()
		dlg.Destroy()
		self.resetAutoCloseTimer()

	def onDelete(self, evt):
		self.resetAutoCloseTimer()
		site = self._get_selected_site()
		if not site:
			return
		name, url = site
		category = self.categoryCombo.GetStringSelection()
		# Stop timer while modal dialog is open
		self.autoCloseTimer.Stop()
		if wx.MessageBox(_("Are you sure you want to delete '{}'?").format(name),
						 _("Confirm Delete"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			self.manager.remove_site(category, name, url)
			self._updateSiteList()
		self.resetAutoCloseTimer()

	def onAddCategory(self, evt):
		self.resetAutoCloseTimer()
		# Stop timer while modal dialog is open
		self.autoCloseTimer.Stop()
		dlg = wx.TextEntryDialog(self, _("Enter new category name:"), _("Add Category"))
		if dlg.ShowModal() == wx.ID_OK:
			new_cat = dlg.GetValue().strip()
			if new_cat:
				if self.manager.add_category(new_cat):
					self._populateCategories()
					self.categoryCombo.SetStringSelection(new_cat)
					self._updateSiteList()
				else:
					wx.MessageBox(_("Category already exists or invalid."), _("Error"), wx.OK | wx.ICON_ERROR)
		dlg.Destroy()
		self.resetAutoCloseTimer()

	def onTogglePin(self, category, url):
		self.resetAutoCloseTimer()
		if self.manager.is_pinned(category, url):
			self.manager.unpin_site(category, url)
		else:
			self.manager.pin_site(category, url)
		self._updateSiteList()
		self._select_site_by_url(url)

	def onMoveUp(self, category, url):
		self.resetAutoCloseTimer()
		if self.manager.move_up(category, url):
			self._updateSiteList()
			self._select_site_by_url(url)
		else:
			ui.message(_("Cannot move up."))

	def onMoveDown(self, category, url):
		self.resetAutoCloseTimer()
		if self.manager.move_down(category, url):
			self._updateSiteList()
			self._select_site_by_url(url)
		else:
			ui.message(_("Cannot move down."))

	def onMoveToCategory(self, new_category):
		self.resetAutoCloseTimer()
		site = self._get_selected_site()
		if not site:
			return
		name, url = site
		old_category = self.categoryCombo.GetStringSelection()
		if old_category == new_category:
			return
		if self.manager.move_site_to_category(old_category, url, new_category):
			self._updateSiteList()
			self.categoryCombo.SetStringSelection(new_category)
			self._updateSiteList()
			self._select_site_by_url(url)
		else:
			wx.MessageBox(_("Failed to move site. It may already exist in the target category."), _("Error"), wx.OK | wx.ICON_ERROR)

	def _select_site_by_url(self, url):
		for i in range(self.siteList.GetItemCount()):
			if hasattr(self, 'current_sites') and i < len(self.current_sites):
				if self.current_sites[i][1] == url:
					self.siteList.Select(i)
					self.siteList.Focus(i)
					return


class AddSiteDialog(wx.Dialog):
	def __init__(self, parent, manager, url=None, category=None, display_name=None, edit_mode=False):
		title = _("Edit Site") if edit_mode else _("Add New Site")
		super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.manager = manager
		self.url = url
		self.edit_mode = edit_mode
		self.old_category = category
		self.old_display_name = display_name
		self.old_url = url
		self._initUI()
		self._bindEvents()
		self._populateCategories()
		if category and category in self.manager.get_all_categories():
			self.categoryCombo.SetStringSelection(category)
		elif self.categoryCombo.GetCount() > 0:
			self.categoryCombo.SetSelection(0)
		if display_name:
			self.nameCtrl.SetValue(display_name)
		elif url:
			self.nameCtrl.SetValue(self._generate_display_name(url))
		if url:
			self.urlCtrl.SetValue(url)
		wx.CallAfter(self.nameCtrl.SetFocus)

	def _initUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		catSizer = wx.BoxSizer(wx.HORIZONTAL)
		catSizer.Add(wx.StaticText(self, label=_("Category:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.categoryCombo = wx.ComboBox(self, choices=[], style=wx.CB_READONLY)
		catSizer.Add(self.categoryCombo, 1, wx.EXPAND)
		self.addCategoryBtn = wx.Button(self, label=_("&Add Category"))
		catSizer.Add(self.addCategoryBtn, 0, wx.LEFT, 5)
		mainSizer.Add(catSizer, 0, wx.EXPAND | wx.ALL, 5)

		nameSizer = wx.BoxSizer(wx.HORIZONTAL)
		nameSizer.Add(wx.StaticText(self, label=_("Display name:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.nameCtrl = wx.TextCtrl(self)
		nameSizer.Add(self.nameCtrl, 1, wx.EXPAND)
		mainSizer.Add(nameSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

		urlSizer = wx.BoxSizer(wx.HORIZONTAL)
		urlSizer.Add(wx.StaticText(self, label=_("Site URL:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.urlCtrl = wx.TextCtrl(self)
		urlSizer.Add(self.urlCtrl, 1, wx.EXPAND)
		mainSizer.Add(urlSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.saveBtn = wx.Button(self, wx.ID_OK, label=_("&Save"))
		self.cancelBtn = wx.Button(self, wx.ID_CANCEL, label=_("&Cancel"))
		btnSizer.Add(self.saveBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.cancelBtn, 0)
		mainSizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

		self.SetSizer(mainSizer)
		self.SetMinSize((500, -1))
		self.Fit()

	def _bindEvents(self):
		self.addCategoryBtn.Bind(wx.EVT_BUTTON, self.onAddCategory)
		self.saveBtn.Bind(wx.EVT_BUTTON, self.onSave)
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)

	def _populateCategories(self):
		cats = self.manager.get_all_categories()
		self.categoryCombo.Clear()
		self.categoryCombo.AppendItems(cats)

	def _generate_display_name(self, url):
		try:
			if "://" in url:
				url = url.split("://", 1)[1]
			domain = url.split("/")[0]
			if domain.startswith("www."):
				domain = domain[4:]
			domain = domain.split(":")[0]
			parts = domain.split('.')
			if parts:
				return parts[0].capitalize()
			return domain.capitalize()
		except:
			if len(url) > 30:
				return url[:27] + "..."
			return url

	def onAddCategory(self, evt):
		dlg = wx.TextEntryDialog(self, _("Enter new category name:"), _("Add Category"))
		if dlg.ShowModal() == wx.ID_OK:
			new_cat = dlg.GetValue().strip()
			if new_cat:
				if self.manager.add_category(new_cat):
					self._populateCategories()
					self.categoryCombo.SetStringSelection(new_cat)
				else:
					wx.MessageBox(_("Category already exists."), _("Error"), wx.OK | wx.ICON_ERROR)
		dlg.Destroy()

	def onSave(self, evt):
		category = self.categoryCombo.GetStringSelection()
		if not category:
			wx.MessageBox(_("Please select or add a category."), _("Error"), wx.OK | wx.ICON_ERROR)
			return
		url = self.urlCtrl.GetValue().strip()
		if not url:
			wx.MessageBox(_("URL cannot be empty."), _("Error"), wx.OK | wx.ICON_ERROR)
			return
		display_name = self.nameCtrl.GetValue().strip()
		if not display_name:
			wx.MessageBox(_("Display name cannot be empty."), _("Error"), wx.OK | wx.ICON_ERROR)
			return

		if self.edit_mode:
			if self.manager.update_site(
				self.old_category, self.old_display_name, self.old_url,
				category, display_name, url
			):
				self.EndModal(wx.ID_OK)
				nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager, category)
			else:
				wx.MessageBox(_("A site with this URL already exists in the target category."), _("Error"), wx.OK | wx.ICON_ERROR)
		else:
			if self.manager.add_site(category, display_name, url):
				self.EndModal(wx.ID_OK)
				nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager, category)
			else:
				wx.MessageBox(_("A site with this URL already exists in this category."), _("Error"), wx.OK | wx.ICON_ERROR)

	def onCharHook(self, evt):
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.EndModal(wx.ID_CANCEL)
		else:
			evt.Skip()