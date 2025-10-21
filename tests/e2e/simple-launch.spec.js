/**
 * Simplified launch test to verify Playwright + Electron setup works
 * This test doesn't rely on backend servers being ready
 */

const { test, expect } = require('@playwright/test');
const { _electron: electron } = require('playwright');
const path = require('path');

test.describe('Simple App Launch', () => {
  let electronApp;
  let window;

  test.beforeEach(async () => {
    // Launch Electron app
    electronApp = await electron.launch({
      args: [path.join(__dirname, '../../src/electron/main.js')],
      timeout: 30000,
      env: {
        ...process.env,
        NODE_ENV: 'test'
      }
    });

    // Wait for the first BrowserWindow to open
    window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded', { timeout: 30000 });
  });

  test.afterEach(async () => {
    if (electronApp) {
      await electronApp.close();
    }
  });

  test('Electron app should launch', async () => {
    expect(electronApp).toBeTruthy();
  });

  test('should have a window', async () => {
    expect(window).toBeTruthy();
    const title = await window.title();
    expect(title).toBe('Drakyn');
  });

  test('should show the header', async () => {
    const header = window.locator('header');
    await expect(header).toBeVisible({ timeout: 10000 });
  });
});
