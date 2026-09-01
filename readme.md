<div align="center">

<img src="https://www.nvaccess.org/files/nvda/documentation/userGuide/images/nvda.ico" alt="NVDA Logo" width="120">

# Absolute Site

Your ultimate centralized hub for managing, categorizing, and rapidly accessing your favorite websites directly from NVDA.

</div>

<br>

<div align="center">

**author:** chai chaimee  
**url:** https://github.com/chaichaimee/AbsoluteSite

</div>

<br>

### Introduction

The **Absolute Site** add-on provides a fully accessible, keyboard-driven environment to manage and organize your bookmarks without relying on your browser's built-in tools. It allows you to create custom categories, save URLs on the fly, and assign preferred browsers to specific categories. Furthermore, it automatically tracks your most visited sites, supports advanced pinning and reordering, and features an integrated Google web search dialogue. This tool streamlines web navigation for power users who want maximum efficiency straight from NVDA.

<br>

### Hot Keys

**NVDA+Alt+Backspace** (Requires multi-tap execution within 0.4 seconds)  
Single Tap : Open Absolute Site Manager Dialog  
Double Tap : Capture the current URL and open the "Add Site" Dialog  
Triple Tap : Open the "Most Visited" Sites Dialog  

**NVDA+Windows+Alt+Backspace**  
Single Tap : Open Web Search Dialog  

<br>

### Features

#### 1. Comprehensive Site & Category Management

Pressing the main hotkey once opens the core **Absolute Site Manager**. Here, you can:

* Create, rename, and delete custom categories (e.g., "Work", "Entertainment", "News").
* Add, edit, or delete websites within those categories.
* Assign a specific web browser (Default, Brave, Chrome, Edge, Firefox) to an entire category. When you open a site from that category, it will automatically launch in the chosen browser.

*Context Menu Actions:* While focused on a site in the list, press the Applications key to Pin/Unpin the site to the top of the category, move it up or down, move it to an entirely different category, or manually choose which installed browser to open it with.

#### 2. Smart URL Capture

While browsing a webpage, you can quickly save it without manually copying the link. By double-tapping the main hotkey, the add-on attempts to read the current document URL directly from the browser's accessibility tree (supporting UIA, IAccessible, and standard browse mode).

*Step-by-step logic:*

1. You double-tap **NVDA+Alt+Backspace** while focused in a browser.
2. The add-on captures the active URL and parses the domain name.
3. It opens the "Add Site" dialog, automatically pre-filling the URL field and generating a clean, capitalized Display Name based on the website's domain (e.g., capturing "https://www.wikipedia.org/..." will set the display name to "Wikipedia").
4. You simply select your desired category and press Save.

#### 3. Most Visited Tracker

Every time you open a URL via the add-on, it logs the visit (storing up to 50 recent unique sites). Triple-tapping the main hotkey opens the **Most Visited** dialog.

* This list aggregates your frequent browsing habits across all categories.
* You can press the Applications key on any entry to Pin it to the top of the history, manually reorder items (Move Up/Move Down), or remove it from the tracking history altogether.

#### 4. Universal Quick Web Search

Pressing **NVDA+Windows+Alt+Backspace** opens a streamlined search dialog. Simply type a query, select your preferred installed browser from the dropdown list, and press Enter. The add-on immediately passes your query to Google and launches the results in the chosen browser, eliminating the need to open a browser and navigate to a search engine manually.

#### 5. Automatic Browser Window Maximization

To ensure optimal accessibility and screen reader performance, the add-on monitors the system for a few seconds after launching a URL. If it detects that Chrome, Firefox, Edge, or Brave was launched, it programmatically forces the browser window to maximize via Windows API calls, announcing "Maximized" when successful.

<br><br>

## Support Me

If this tool has made your life easier, consider fueling the next update with a small donation.

<br>

[![Support me](https://img.shields.io/badge/Donate-Support%20Me-blue?style=for-the-badge&logo=stripe)](https://buy.stripe.com/dRm9AU1xQ3Ds22N6VK1VK01)

<br>

Your support means the world. Let's build something great together

<br>

© 2026 Chai Chaimee NVDA Add-on Released under GNU GPL