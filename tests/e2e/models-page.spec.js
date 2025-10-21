const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp, waitForServerReady } = require('./helpers/electron');

test.describe('Models Page', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;

    // Navigate to Models page
    await window.locator('a[data-page="models"]').click();
    await expect(window.locator('#models-page')).toHaveClass(/active/);
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should display model configuration UI', async () => {
    const modelsPage = window.locator('#models-page');

    // Check for model selection dropdown
    const modelDropdown = modelsPage.locator('#model-dropdown');
    await expect(modelDropdown).toBeVisible();

    // Check for custom model input
    const modelPath = modelsPage.locator('#model-path');
    await expect(modelPath).toBeVisible();

    // Check for load model button
    const loadBtn = modelsPage.locator('#load-model-btn');
    await expect(loadBtn).toBeVisible();
    await expect(loadBtn).toHaveText('Set Model');
  });

  test('should show model dropdown with cloud and local options', async () => {
    const modelDropdown = window.locator('#model-dropdown');

    // Check that dropdown has optgroups
    const cloudModels = modelDropdown.locator('optgroup[label="Cloud Models (Require API Keys)"]');
    await expect(cloudModels).toBeVisible();

    const localModels = modelDropdown.locator('optgroup[label="Local Models (Ollama)"]');
    await expect(localModels).toBeVisible();

    // Check for some specific model options
    const claudeOption = modelDropdown.locator('option[value="claude-sonnet-4-5"]');
    await expect(claudeOption).toBeVisible();

    const qwenOption = modelDropdown.locator('option[value="qwen2.5-coder:3b"]');
    await expect(qwenOption).toBeVisible();
  });

  test('should display loaded models section', async () => {
    const loadedModelsSection = window.locator('#loaded-models-list');
    await expect(loadedModelsSection).toBeVisible();
  });

  test('should display server status section', async () => {
    const serverStatus = window.locator('#server-status');
    await expect(serverStatus).toBeVisible();

    const inferenceStatus = window.locator('#inference-status');
    await expect(inferenceStatus).toBeVisible();
  });

  test('should have refresh models button', async () => {
    const refreshBtn = window.locator('#refresh-models-btn');
    await expect(refreshBtn).toBeVisible();
    await expect(refreshBtn).toHaveText('Refresh Available Models');
  });

  test('should allow entering custom model name', async () => {
    const modelPathInput = window.locator('#model-path');

    // Type a custom model name
    await modelPathInput.fill('custom-model:latest');

    // Verify the value
    await expect(modelPathInput).toHaveValue('custom-model:latest');
  });

  test('should show error when trying to load without model selection', async () => {
    const loadBtn = window.locator('#load-model-btn');
    const statusEl = window.locator('#load-status');

    // Click load without selecting a model
    await loadBtn.click();

    // Should show error message
    await expect(statusEl).toBeVisible();
    // Note: The actual error checking will depend on server response
  });
});
