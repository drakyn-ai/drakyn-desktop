/**
 * TEST TEMPLATE
 *
 * Copy this file and rename it to match your feature.
 * Example: chat-functionality.spec.js
 *
 * This template provides a starting point for writing new E2E tests.
 */

const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp, waitForServerReady } = require('./helpers/electron');

test.describe('Feature Name Here', () => {
  let app, window;

  // Runs before each test - launches the app
  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;

    // Optional: Wait for server to be ready if your test needs it
    // await waitForServerReady(window);

    // Optional: Navigate to a specific page
    // await window.locator('a[data-page="models"]').click();
    // await expect(window.locator('#models-page')).toHaveClass(/active/);
  });

  // Runs after each test - closes the app
  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  // Example Test 1: Check element exists
  test('should display the main component', async () => {
    const element = window.locator('#my-element');
    await expect(element).toBeVisible();
  });

  // Example Test 2: Check text content
  test('should show correct title', async () => {
    const title = window.locator('h2');
    await expect(title).toHaveText('Expected Title');
  });

  // Example Test 3: Test interaction
  test('should enable button when input is filled', async () => {
    const input = window.locator('#my-input');
    const button = window.locator('#my-button');

    // Button should be disabled initially
    await expect(button).toBeDisabled();

    // Type in input
    await input.fill('test value');

    // Button should now be enabled
    await expect(button).toBeEnabled();
  });

  // Example Test 4: Test click interaction
  test('should update status when button is clicked', async () => {
    const button = window.locator('#my-button');
    const status = window.locator('#status-message');

    // Click the button
    await button.click();

    // Check status updates
    await expect(status).toContainText('Success');
  });

  // Example Test 5: Test navigation
  test('should navigate to correct page', async () => {
    const navLink = window.locator('a[data-page="settings"]');
    await navLink.click();

    const settingsPage = window.locator('#settings-page');
    await expect(settingsPage).toHaveClass(/active/);
  });

  // Example Test 6: Test form submission
  test('should submit form with correct data', async () => {
    const input = window.locator('#form-input');
    const submitBtn = window.locator('#submit-btn');
    const result = window.locator('#result');

    // Fill form
    await input.fill('test data');
    await submitBtn.click();

    // Wait for result
    await expect(result).toContainText('Submitted', { timeout: 5000 });
  });

  // Example Test 7: Test error state
  test('should show error when operation fails', async () => {
    const button = window.locator('#error-trigger');
    const errorMsg = window.locator('#error-message');

    await button.click();

    // Error message should appear
    await expect(errorMsg).toBeVisible();
    await expect(errorMsg).toContainText('Error:');
  });

  // Example Test 8: Test dropdown selection
  test('should select option from dropdown', async () => {
    const dropdown = window.locator('#my-dropdown');

    // Select an option
    await dropdown.selectOption('option-value');

    // Verify selection
    await expect(dropdown).toHaveValue('option-value');
  });

  // Example Test 9: Test multiple elements
  test('should display all list items', async () => {
    const listItems = window.locator('.list-item');

    // Check count
    await expect(listItems).toHaveCount(5);

    // Check specific items
    await expect(listItems.nth(0)).toContainText('First Item');
    await expect(listItems.nth(1)).toContainText('Second Item');
  });

  // Example Test 10: Test conditional visibility
  test('should hide element based on condition', async () => {
    const checkbox = window.locator('#toggle-checkbox');
    const conditionalElement = window.locator('#conditional-element');

    // Initially visible
    await expect(conditionalElement).toBeVisible();

    // Toggle checkbox
    await checkbox.check();

    // Should now be hidden
    await expect(conditionalElement).not.toBeVisible();
  });
});

/**
 * COMMON LOCATOR PATTERNS
 *
 * By ID:        window.locator('#element-id')
 * By class:     window.locator('.class-name')
 * By text:      window.locator('text=Button Text')
 * By role:      window.locator('button:has-text("Submit")')
 * By attribute: window.locator('[data-page="chat"]')
 * Nested:       window.locator('#parent .child')
 * Multiple:     window.locator('.item')  // Returns all matches
 * Nth item:     window.locator('.item').nth(0)
 */

/**
 * COMMON ASSERTIONS
 *
 * Visibility:
 *   await expect(element).toBeVisible()
 *   await expect(element).not.toBeVisible()
 *   await expect(element).toBeHidden()
 *
 * Text:
 *   await expect(element).toHaveText('exact text')
 *   await expect(element).toContainText('partial text')
 *
 * Count:
 *   await expect(elements).toHaveCount(5)
 *
 * State:
 *   await expect(element).toBeEnabled()
 *   await expect(element).toBeDisabled()
 *   await expect(element).toBeChecked()
 *
 * Attributes:
 *   await expect(element).toHaveAttribute('type', 'password')
 *   await expect(element).toHaveClass(/active/)
 *   await expect(element).toHaveValue('input value')
 *
 * With timeout:
 *   await expect(element).toBeVisible({ timeout: 10000 })
 */

/**
 * COMMON INTERACTIONS
 *
 * Click:
 *   await element.click()
 *
 * Type:
 *   await input.fill('text')
 *   await input.type('text', { delay: 100 })  // Slower typing
 *   await input.clear()
 *
 * Select:
 *   await select.selectOption('value')
 *   await select.selectOption({ label: 'Label' })
 *
 * Checkbox/Radio:
 *   await checkbox.check()
 *   await checkbox.uncheck()
 *
 * Hover:
 *   await element.hover()
 *
 * Wait:
 *   await element.waitFor({ state: 'visible' })
 *   await window.waitForTimeout(1000)  // Use sparingly
 */

/**
 * DEBUGGING TIPS
 *
 * 1. Run in headed mode to see what's happening:
 *    npm run test:headed
 *
 * 2. Use debug mode to step through:
 *    npm run test:debug
 *
 * 3. Add console.log for debugging:
 *    const text = await element.textContent();
 *    console.log('Element text:', text);
 *
 * 4. Take screenshots manually:
 *    await window.screenshot({ path: 'debug.png' });
 *
 * 5. Check what's in the DOM:
 *    const html = await window.content();
 *    console.log(html);
 *
 * 6. Use page.pause() to pause execution:
 *    await window.pause();
 */
