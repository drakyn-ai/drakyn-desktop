const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp } = require('./helpers/electron');

test.describe('Settings Page', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;

    // Navigate to Settings page
    await window.locator('a[data-page="settings"]').click();
    await expect(window.locator('#settings-page')).toHaveClass(/active/);

    // Wait for settings to load
    await window.waitForTimeout(500);
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should display server control section', async () => {
    const settingsPage = window.locator('#settings-page');

    // Check for server control buttons
    const startBtn = settingsPage.locator('#start-server-btn');
    await expect(startBtn).toBeVisible();
    await expect(startBtn).toHaveText('Start Server');

    const stopBtn = settingsPage.locator('#stop-server-btn');
    await expect(stopBtn).toBeVisible();
    await expect(stopBtn).toHaveText('Stop Server');
  });

  test('should display inference engine configuration', async () => {
    const engineSelect = window.locator('#engine-select');
    await expect(engineSelect).toBeVisible();

    // Check for both engine options
    const vllmOption = engineSelect.locator('option[value="vllm"]');
    await expect(vllmOption).toBeVisible();

    const openaiOption = engineSelect.locator('option[value="openai_compatible"]');
    await expect(openaiOption).toBeVisible();
  });

  test('should show OpenAI URL field when openai_compatible is selected', async () => {
    const engineSelect = window.locator('#engine-select');
    const openaiUrlGroup = window.locator('#openai-url-group');

    // Initially might be hidden
    // Select openai_compatible
    await engineSelect.selectOption('openai_compatible');

    // URL field should become visible
    await expect(openaiUrlGroup).toBeVisible();

    const urlInput = window.locator('#openai-url');
    await expect(urlInput).toBeVisible();
  });

  test('should hide OpenAI URL field when vllm is selected', async () => {
    const engineSelect = window.locator('#engine-select');
    const openaiUrlGroup = window.locator('#openai-url-group');

    // First select openai_compatible
    await engineSelect.selectOption('openai_compatible');
    await expect(openaiUrlGroup).toBeVisible();

    // Then switch back to vllm
    await engineSelect.selectOption('vllm');

    // URL field should be hidden
    await expect(openaiUrlGroup).not.toBeVisible();
  });

  test('should display API keys section', async () => {
    const anthropicInput = window.locator('#anthropic-api-key');
    await expect(anthropicInput).toBeVisible();
    await expect(anthropicInput).toHaveAttribute('type', 'password');

    const openaiInput = window.locator('#openai-api-key');
    await expect(openaiInput).toBeVisible();
    await expect(openaiInput).toHaveAttribute('type', 'password');

    const saveBtn = window.locator('#save-api-keys-btn');
    await expect(saveBtn).toBeVisible();
  });

  test('should display current configuration', async () => {
    const configDiv = window.locator('#current-config');
    await expect(configDiv).toBeVisible();
  });

  test('should display Gmail integration section', async () => {
    const gmailSection = window.locator('#gmail-status');
    await expect(gmailSection).toBeVisible();

    const uploadBtn = window.locator('#upload-gmail-credentials-btn');
    await expect(uploadBtn).toBeVisible();
  });

  test('should have save settings button', async () => {
    const saveBtn = window.locator('#save-settings-btn');
    await expect(saveBtn).toBeVisible();
    await expect(saveBtn).toHaveText('Save Settings');
  });

  test('should allow typing in API key fields', async () => {
    const anthropicInput = window.locator('#anthropic-api-key');

    // Type a fake API key
    await anthropicInput.fill('sk-ant-test-key');
    await expect(anthropicInput).toHaveValue('sk-ant-test-key');
  });
});
