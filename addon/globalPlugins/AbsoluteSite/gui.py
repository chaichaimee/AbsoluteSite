# gui.py

import wx
import addonHandler
import ui
import gui as nvdaGui
import os
import re
from .siteManager import SiteManager

addonHandler.initTranslation()

class MainDialog(wx.Dialog):
	def __init__(self, parent, manager):
		super().__init__(parent, title=_("Absolute Site"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
		self.manager = manager
		self._initUI()
		self._bindEvents()
		self._populateCategories()
		if self.categoryCombo.GetCount() > 0:
			self.categoryCombo.SetSelection(0)
		self._updateSiteList()
		wx.CallAfter(self.siteList.SetFocus)

	def _initUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		# Category selection
		catSizer = wx.BoxSizer(wx.HORIZONTAL)
		catSizer.Add(wx.StaticText(self, label=_("Category:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.categoryCombo = wx.ComboBox(self, choices=[], style=wx.CB_READONLY)
		catSizer.Add(self.categoryCombo, 1, wx.EXPAND)
		mainSizer.Add(catSizer, 0, wx.EXPAND | wx.ALL, 5)

		# Site list
		self.siteList = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN)
		self.siteList.InsertColumn(0, _("Name"), width=250)
		self.siteList.InsertColumn(1, _("URL"), width=400)
		mainSizer.Add(self.siteList, 1, wx.EXPAND | wx.ALL, 5)

		# Show paths checkbox
		self.showPathsCheck = wx.CheckBox(self, label=_("Show paths"))
		self.showPathsCheck.SetValue(False)  # default unchecked
		mainSizer.Add(self.showPathsCheck, 0, wx.ALL, 5)

		# Buttons
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.openBtn = wx.Button(self, label=_("&Open URL"))
		self.editBtn = wx.Button(self, label=_("&Edit Site"))
		self.deleteBtn = wx.Button(self, label=_("&Delete Site"))
		self.addCategoryBtn = wx.Button(self, label=_("&Add Category"))
		self.exitBtn = wx.Button(self, wx.ID_CLOSE, label=_("E&xit"))
		btnSizer.Add(self.openBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.editBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.deleteBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.addCategoryBtn, 0, wx.RIGHT, 5)
		btnSizer.Add(self.exitBtn, 0)
		mainSizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

		self.SetSizer(mainSizer)
		self.SetMinSize((700, 500))
		self.Fit()

	def _bindEvents(self):
		self.categoryCombo.Bind(wx.EVT_COMBOBOX, self.onCategoryChange)
		self.siteList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onOpenUrl)  # Enter or double-click opens URL
		self.siteList.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
		self.siteList.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.showPathsCheck.Bind(wx.EVT_CHECKBOX, self.onShowPathsChanged)
		self.openBtn.Bind(wx.EVT_BUTTON, self.onOpenUrl)
		self.editBtn.Bind(wx.EVT_BUTTON, self.onEdit)
		self.deleteBtn.Bind(wx.EVT_BUTTON, self.onDelete)
		self.addCategoryBtn.Bind(wx.EVT_BUTTON, self.onAddCategory)
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
		sites = self.manager.get_sites_by_category(category)
		sites.sort(key=lambda s: s[0].lower())
		show_paths = self.showPathsCheck.GetValue()
		for i, (name, url) in enumerate(sites):
			if show_paths:
				self.siteList.InsertItem(i, f"{name}; URL: {url}")
			else:
				self.siteList.InsertItem(i, name)
			# Store full data as item data for later retrieval
			self.siteList.SetItemData(i, i)  # index mapping, we'll store separately
			# We'll keep a mapping from index to (name, url) in memory
		# Store sites list for this category for later access
		self.current_sites = sites
		if self.siteList.GetItemCount() > 0:
			self.siteList.Select(0)
			self.siteList.Focus(0)
		self._updateButtons()

	def _updateButtons(self):
		has_selection = self.siteList.GetFirstSelected() != -1
		self.openBtn.Enable(has_selection)
		self.editBtn.Enable(has_selection)
		self.deleteBtn.Enable(has_selection)

	def onShowPathsChanged(self, evt):
		self._updateSiteList()

	def onCategoryChange(self, evt):
		self._updateSiteList()

	def onContextMenu(self, evt):
		idx = self.siteList.GetFirstSelected()
		if idx == -1:
			return
		menu = wx.Menu()
		openItem = menu.Append(wx.ID_ANY, _("&Open URL"))
		editItem = menu.Append(wx.ID_ANY, _("&Edit"))
		deleteItem = menu.Append(wx.ID_ANY, _("&Delete"))
		self.Bind(wx.EVT_MENU, self.onOpenUrl, openItem)
		self.Bind(wx.EVT_MENU, self.onEdit, editItem)
		self.Bind(wx.EVT_MENU, self.onDelete, deleteItem)
		self.siteList.PopupMenu(menu)
		menu.Destroy()

	def onKeyDown(self, evt):
		if evt.GetKeyCode() == wx.WXK_DELETE:
			self.onDelete(None)
		else:
			evt.Skip()

	def onCharHook(self, evt):
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.Close()
		else:
			evt.Skip()

	def _get_selected_site(self):
		idx = self.siteList.GetFirstSelected()
		if idx == -1:
			return None
		category = self.categoryCombo.GetStringSelection()
		sites = self.manager.get_sites_by_category(category)
		sites.sort(key=lambda s: s[0].lower())
		if idx < len(sites):
			return sites[idx]
		return None

	def onOpenUrl(self, evt):
		site = self._get_selected_site()
		if site:
			_, url = site
			try:
				os.startfile(url)
			except Exception as e:
				wx.MessageBox(_("Failed to open URL: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)
			# Close dialog after opening
			self.Close()

	def onEdit(self, evt):
		site = self._get_selected_site()
		if not site:
			return
		name, url = site
		category = self.categoryCombo.GetStringSelection()
		dlg = AddSiteDialog(self, self.manager, category=category, display_name=name, url=url, edit_mode=True)
		if dlg.ShowModal() == wx.ID_OK:
			self._updateSiteList()
		dlg.Destroy()

	def onDelete(self, evt):
		site = self._get_selected_site()
		if not site:
			return
		name, url = site
		category = self.categoryCombo.GetStringSelection()
		if wx.MessageBox(_("Are you sure you want to delete '{}'?").format(name),
						 _("Confirm Delete"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			self.manager.remove_site(category, name, url)
			self._updateSiteList()

	def onAddCategory(self, evt):
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
			# Auto-generate display name from URL
			self.nameCtrl.SetValue(self._generate_display_name(url))
		if url:
			self.urlCtrl.SetValue(url)
		# Focus: if new site, focus on display name; if editing, focus on name as well
		wx.CallAfter(self.nameCtrl.SetFocus)

	def _initUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		# Category
		catSizer = wx.BoxSizer(wx.HORIZONTAL)
		catSizer.Add(wx.StaticText(self, label=_("Category:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.categoryCombo = wx.ComboBox(self, choices=[], style=wx.CB_READONLY)
		catSizer.Add(self.categoryCombo, 1, wx.EXPAND)
		self.addCategoryBtn = wx.Button(self, label=_("&Add Category"))
		catSizer.Add(self.addCategoryBtn, 0, wx.LEFT, 5)
		mainSizer.Add(catSizer, 0, wx.EXPAND | wx.ALL, 5)

		# Display name (now above URL)
		nameSizer = wx.BoxSizer(wx.HORIZONTAL)
		nameSizer.Add(wx.StaticText(self, label=_("Display name:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.nameCtrl = wx.TextCtrl(self)
		nameSizer.Add(self.nameCtrl, 1, wx.EXPAND)
		mainSizer.Add(nameSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

		# URL
		urlSizer = wx.BoxSizer(wx.HORIZONTAL)
		urlSizer.Add(wx.StaticText(self, label=_("Site URL:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.urlCtrl = wx.TextCtrl(self)
		urlSizer.Add(self.urlCtrl, 1, wx.EXPAND)
		mainSizer.Add(urlSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

		# Buttons
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
			# Extract domain
			if "://" in url:
				url = url.split("://", 1)[1]
			domain = url.split("/")[0]
			if domain.startswith("www."):
				domain = domain[4:]
			# Remove port if present
			domain = domain.split(":")[0]
			# Return the first part before any dot
			parts = domain.split('.')
			if parts:
				return parts[0].capitalize()
			return domain.capitalize()
		except:
			# Fallback
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
				# After saving, open main dialog
				nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager)
			else:
				wx.MessageBox(_("Failed to update site. URL might already exist."), _("Error"), wx.OK | wx.ICON_ERROR)
		else:
			if self.manager.add_site(category, display_name, url):
				self.EndModal(wx.ID_OK)
				# After adding, open main dialog
				nvdaGui.mainFrame.popupSettingsDialog(MainDialog, self.manager)
			else:
				wx.MessageBox(_("Failed to add site. URL might already exist."), _("Error"), wx.OK | wx.ICON_ERROR)

	def onCharHook(self, evt):
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.EndModal(wx.ID_CANCEL)
		else:
			evt.Skip()