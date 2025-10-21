const { _electron: electron } = require('playwright');
const path = require('path');

/**
 * Launch Electron app for testing
 * @returns {Promise<{app: ElectronApplication, window: Page}>}
 */
async function launchElectronApp() {
  try {
    const app = await electron.launch({
      args: [path.join(__dirname, '../../../src/electron/main.js'), '--dev'],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        // Disable GPU on WSL
        ELECTRON_DISABLE_GPU: '1'
      },
      timeout: 30000
    });

    // Wait for the first window
    const window = await app.firstWindow();

    // Wait for app to be ready
    await window.waitForLoadState('domcontentloaded');

    return { app, window };
  } catch (error) {
    console.error('Failed to launch Electron:', error);
    throw error;
  }
}

/**
 * Close Electron app gracefully
 */
async function closeElectronApp(app) {
  if (app) {
    try {
      await app.close();
    } catch (error) {
      console.error('Error closing app:', error);
    }
  }
}

/**
 * Wait for server to be ready by checking connection status
 */
async function waitForServerReady(window, timeout = 30000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      const statusText = await window.locator('#connection-text').textContent();

      // Check if we're in a ready state
      if (statusText.includes('Ready') || statusText.includes('Set a model')) {
        return true;
      }

      // Wait a bit before checking again
      await window.waitForTimeout(1000);
    } catch (error) {
      // Element might not be ready yet
      await window.waitForTimeout(1000);
    }
  }

  throw new Error(`Server not ready after ${timeout}ms`);
}

module.exports = {
  launchElectronApp,
  closeElectronApp,
  waitForServerReady
};
