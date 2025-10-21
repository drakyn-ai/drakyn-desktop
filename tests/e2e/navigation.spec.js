const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp } = require('./helpers/electron');

test.describe('Navigation', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should navigate to Models page', async () => {
    // Click on Models nav item
    await window.locator('a[data-page="models"]').click();

    // Wait for page to be visible
    const modelsPage = window.locator('#models-page');
    await expect(modelsPage).toHaveClass(/active/);

    // Check that Chat page is not active
    const chatPage = window.locator('#chat-page');
    await expect(chatPage).not.toHaveClass(/active/);

    // Verify Models page content
    await expect(modelsPage.locator('h2')).toHaveText('Model Configuration');
  });

  test('should navigate to Settings page', async () => {
    // Click on Settings nav item
    await window.locator('a[data-page="settings"]').click();

    // Wait for page to be visible
    const settingsPage = window.locator('#settings-page');
    await expect(settingsPage).toHaveClass(/active/);

    // Verify Settings page content
    await expect(settingsPage.locator('h2')).toHaveText('Settings');
  });

  test('should navigate to Agents page', async () => {
    // Click on Agents nav item
    await window.locator('a[data-page="agents"]').click();

    // Wait for page to be visible
    const agentsPage = window.locator('#agents-page');
    await expect(agentsPage).toHaveClass(/active/);

    // Verify Agents page content
    await expect(agentsPage.locator('h2')).toHaveText('Manage Agents');
  });

  test('should navigate back to Chat page', async () => {
    // First go to another page
    await window.locator('a[data-page="models"]').click();
    await expect(window.locator('#models-page')).toHaveClass(/active/);

    // Navigate back to Chat
    await window.locator('a[data-page="chat"]').click();

    // Verify Chat page is active
    const chatPage = window.locator('#chat-page');
    await expect(chatPage).toHaveClass(/active/);
  });
});
