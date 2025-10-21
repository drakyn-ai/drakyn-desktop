# E2E Testing with Playwright

This project uses Playwright to perform end-to-end (E2E) testing of the Electron application.

## Overview

E2E tests launch the actual Electron app, interact with it programmatically, and verify that features work correctly. This allows automated testing without manual UI interaction.

## Running Tests

```bash
# Run all tests (headless)
npm test

# Run tests with visible browser (see the app while testing)
npm run test:headed

# Run tests with Playwright UI (interactive test runner)
npm run test:ui

# Debug tests (step through with debugger)
npm run test:debug
```

## Test Structure

Tests are located in `tests/e2e/` directory:

- **app-launch.spec.js** - Tests basic app launch and initial UI state
- **navigation.spec.js** - Tests navigation between pages
- **models-page.spec.js** - Tests model configuration UI
- **settings-page.spec.js** - Tests settings page functionality

## Helper Functions

`tests/e2e/helpers/electron.js` provides utilities:

- `launchElectronApp()` - Launches the Electron app for testing
- `closeElectronApp(app)` - Closes the app gracefully
- `waitForServerReady(window, timeout)` - Waits for backend server to be ready

## Writing New Tests

### Basic Test Template

```javascript
const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp } = require('./helpers/electron');

test.describe('Feature Name', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should do something', async () => {
    // Your test here
    const button = window.locator('#my-button');
    await expect(button).toBeVisible();
  });
});
```

### Common Patterns

#### Finding Elements

```javascript
// By ID
const button = window.locator('#send-button');

// By class
const message = window.locator('.chat-message');

// By text
const link = window.locator('text=Settings');

// By data attribute
const navLink = window.locator('a[data-page="chat"]');

// Multiple elements
const navItems = window.locator('.sidebar ul li a');
await expect(navItems).toHaveCount(4);
```

#### Interacting with Elements

```javascript
// Click
await button.click();

// Type text
await input.fill('Hello world');

// Select dropdown
await select.selectOption('option-value');

// Check visibility
await expect(element).toBeVisible();
await expect(element).not.toBeVisible();

// Check text content
await expect(element).toHaveText('Expected text');
await expect(element).toContainText('partial text');

// Check attributes
await expect(input).toHaveValue('input value');
await expect(element).toHaveClass(/active/);
await expect(element).toHaveAttribute('type', 'password');
```

#### Waiting for State

```javascript
// Wait for element to appear
await element.waitFor({ state: 'visible' });

// Wait for text to change
await expect(statusText).toHaveText('Connected', { timeout: 10000 });

// Wait for specific time (use sparingly)
await window.waitForTimeout(1000);

// Wait for server to be ready
await waitForServerReady(window);
```

#### Navigation

```javascript
// Click navigation link
await window.locator('a[data-page="models"]').click();

// Verify page is active
const modelsPage = window.locator('#models-page');
await expect(modelsPage).toHaveClass(/active/);
```

## What Can Be Tested

### ✅ Functional Testing (Good for Playwright)

- **UI Elements Exist**: Buttons, inputs, dropdowns are rendered
- **Navigation**: Clicking links shows correct pages
- **Form Interaction**: Typing in inputs, selecting dropdowns
- **Button States**: Enabled/disabled based on conditions
- **Text Content**: Correct labels, messages, status text
- **CSS Classes**: Elements have correct state classes (active, connected, error)
- **DOM Attributes**: Correct attributes on elements
- **Element Count**: Right number of items in lists
- **Workflow Logic**: Multi-step processes work correctly

### ❌ Visual Testing (Limited)

Playwright cannot easily verify:
- Layout and positioning (unless obviously broken)
- Colors and styling (unless checking CSS classes)
- Font sizes and spacing
- Responsive design
- Visual polish

For visual issues, manual testing is still required.

## Testing Best Practices

### DO:

1. **Test User Workflows**: Simulate real user interactions
   ```javascript
   test('user can select model and load it', async () => {
     await window.locator('a[data-page="models"]').click();
     await window.locator('#model-dropdown').selectOption('qwen2.5-coder:3b');
     await window.locator('#load-model-btn').click();
     await expect(window.locator('#load-status')).toContainText('Success');
   });
   ```

2. **Test Error States**: Verify error handling
   ```javascript
   test('shows error when loading model without selection', async () => {
     await window.locator('#load-model-btn').click();
     await expect(window.locator('#load-status')).toContainText('Please select');
   });
   ```

3. **Test State Changes**: Verify UI updates correctly
   ```javascript
   test('disables chat input when server is not ready', async () => {
     const input = window.locator('#message-input');
     await expect(input).toBeDisabled();
   });
   ```

4. **Use Descriptive Test Names**: Make failures easy to understand
   ```javascript
   test('should show OpenAI URL field when openai_compatible is selected')
   ```

### DON'T:

1. **Don't test implementation details**: Test behavior, not internal code
2. **Don't test external APIs directly**: Mock or stub them
3. **Don't make tests depend on each other**: Each test should be independent
4. **Don't use arbitrary waits**: Use `waitFor` and `expect` with timeouts instead of `waitForTimeout`

## Running Tests During Development

When building a new feature:

1. **Write the test first** (optional, TDD approach):
   ```bash
   npm run test:debug
   ```

2. **Implement the feature**

3. **Run tests to verify**:
   ```bash
   npm test
   ```

4. **Fix any failures and iterate**

## CI/CD Integration

Tests can run automatically in CI:

```bash
# In CI environment
npm test
```

The configuration in `playwright.config.js` automatically:
- Retries failed tests in CI (2 retries)
- Takes screenshots on failure
- Generates HTML reports

## Debugging Failed Tests

When a test fails:

1. **Check the error message**: Often tells you exactly what's wrong
2. **Look at screenshots**: `playwright-report/` folder has failure screenshots
3. **Run in headed mode**: `npm run test:headed` to see what's happening
4. **Use debug mode**: `npm run test:debug` to step through test
5. **Add console logs**: `console.log()` in tests to debug state

## Example: Testing a New Feature

Let's say you add a "Clear Chat" button. Here's how to test it:

```javascript
test.describe('Clear Chat Feature', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;

    // Wait for server to be ready
    await waitForServerReady(window);
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should clear all messages when clear button is clicked', async () => {
    // Navigate to chat page (should already be there)
    const chatPage = window.locator('#chat-page');
    await expect(chatPage).toHaveClass(/active/);

    // Send a message
    const input = window.locator('#message-input');
    const sendBtn = window.locator('#send-button');

    await input.fill('Test message');
    await sendBtn.click();

    // Wait for message to appear
    const messages = window.locator('#chat-messages > div');
    await expect(messages).toHaveCount(1, { timeout: 5000 });

    // Click clear button
    const clearBtn = window.locator('#clear-chat-btn');
    await clearBtn.click();

    // Verify messages are cleared
    await expect(messages).toHaveCount(0);
  });

  test('clear button should be disabled when no messages', async () => {
    const clearBtn = window.locator('#clear-chat-btn');

    // Should be disabled initially
    await expect(clearBtn).toBeDisabled();

    // Send a message
    const input = window.locator('#message-input');
    await input.fill('Test');
    await window.locator('#send-button').click();

    // Should be enabled now
    await expect(clearBtn).toBeEnabled();
  });
});
```

## Tips for Agent Testing

Since you (the coding agent) will be running these tests:

1. **Always run tests after making changes**:
   ```bash
   npm test
   ```

2. **If tests fail, investigate before continuing**:
   - Read the error message carefully
   - Check which assertion failed
   - Run in headed mode to see what's happening

3. **Update tests when changing UI**:
   - If you change an ID, update the test locators
   - If you change behavior, update the assertions

4. **Write tests for new features**:
   - Follow the patterns in existing tests
   - Test both success and error cases
   - Test user workflows, not just individual components

5. **Use tests to verify fixes**:
   - If you're fixing a bug, write a test that reproduces it first
   - Then fix the bug
   - The test should now pass

## Further Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Playwright Electron API](https://playwright.dev/docs/api/class-electron)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
