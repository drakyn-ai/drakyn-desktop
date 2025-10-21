const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp, waitForServerReady } = require('./helpers/electron');

test.describe('App Launch', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should launch successfully and show main window', async () => {
    // Check that window is visible
    expect(await window.isVisible()).toBe(true);

    // Check title
    const title = await window.title();
    expect(title).toBe('Drakyn');
  });

  test('should display header with logo and title', async () => {
    // Check for header elements
    const logo = window.locator('.logo');
    await expect(logo).toBeVisible();

    const heading = window.locator('h1');
    await expect(heading).toHaveText('Drakyn');

    const subtitle = window.locator('.header-text p');
    await expect(subtitle).toHaveText('Local AI Agent');
  });

  test('should show all navigation menu items', async () => {
    const navItems = window.locator('.sidebar ul li a');

    // Check that all 4 nav items exist
    await expect(navItems).toHaveCount(4);

    // Check each nav item
    await expect(navItems.nth(0)).toHaveText('Chat');
    await expect(navItems.nth(1)).toHaveText('Agents');
    await expect(navItems.nth(2)).toHaveText('Models');
    await expect(navItems.nth(3)).toHaveText('Settings');
  });

  test('should start with Chat page active', async () => {
    const chatPage = window.locator('#chat-page');
    await expect(chatPage).toHaveClass(/active/);
  });

  test('should show connection status indicator', async () => {
    const connectionIndicator = window.locator('#connection-indicator');
    const connectionText = window.locator('#connection-text');

    await expect(connectionIndicator).toBeVisible();
    await expect(connectionText).toBeVisible();
  });
});
