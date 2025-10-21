# Playwright E2E Testing Setup Summary

## What Was Installed

1. **Playwright Testing Framework**
   - `@playwright/test` - Core testing library
   - `playwright` - Browser automation (includes Electron support)

2. **Configuration**
   - [playwright.config.js](../playwright.config.js) - Test runner configuration
   - Test directory: `tests/e2e/`
   - Timeout: 60 seconds per test
   - Sequential execution (1 worker)
   - Screenshots on failure
   - HTML report generation

## Test Scripts Added to package.json

```bash
npm test              # Run all tests (headless)
npm run test:headed   # Run with visible UI
npm run test:ui       # Interactive test runner
npm run test:debug    # Debug mode with breakpoints
```

## Test Files Created

### Test Suites
1. **[tests/e2e/app-launch.spec.js](../tests/e2e/app-launch.spec.js)**
   - Tests app launches successfully
   - Verifies header and logo display
   - Checks navigation menu items
   - Confirms chat page is default
   - Validates connection status indicator

2. **[tests/e2e/navigation.spec.js](../tests/e2e/navigation.spec.js)**
   - Tests navigation between Chat, Models, Agents, Settings pages
   - Verifies active page states
   - Ensures only one page is active at a time

3. **[tests/e2e/models-page.spec.js](../tests/e2e/models-page.spec.js)**
   - Tests model selection dropdown
   - Verifies cloud and local model options
   - Tests custom model input
   - Checks model loading UI elements
   - Validates server status display

4. **[tests/e2e/settings-page.spec.js](../tests/e2e/settings-page.spec.js)**
   - Tests server control buttons
   - Verifies inference engine selection
   - Tests OpenAI URL visibility toggling
   - Validates API key input fields
   - Checks Gmail integration UI

### Helper Utilities
**[tests/e2e/helpers/electron.js](../tests/e2e/helpers/electron.js)**
- `launchElectronApp()` - Launches Electron with proper config
- `closeElectronApp()` - Gracefully closes the app
- `waitForServerReady()` - Waits for backend to be ready

## Documentation Created

1. **[TESTING.md](../TESTING.md)** - Comprehensive testing guide
   - How to run tests
   - How to write new tests
   - Common patterns and examples
   - Best practices
   - Debugging tips
   - Example of testing a new feature

2. **[tests/e2e/README.md](../tests/e2e/README.md)** - Setup notes
   - WSL limitations
   - Alternative testing approaches
   - When to run tests

## How Tests Work

### Test Pattern
Every test follows this structure:

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
    // Test code using DOM selectors and assertions
  });
});
```

### What Can Be Tested

✅ **Functional Testing** (automated):
- Element existence and visibility
- Button states (enabled/disabled)
- Text content
- Form interactions
- Navigation flows
- CSS class states
- DOM attributes
- User workflows

❌ **Visual Testing** (still manual):
- Layout and positioning
- Colors and styling
- Font sizes
- Responsive design

## Integration with Development Workflow

### For Coding Agents (Like Me)

When adding a new feature:

1. **Write the test first** (optional, TDD):
   ```bash
   npm run test:debug
   ```

2. **Implement the feature**

3. **Run tests to verify**:
   ```bash
   npm test
   ```

4. **Document what was tested** in commit message

### For Manual Testing

You (Chanh) should run tests:
- On native Windows (not WSL) for best results
- After pulling new changes
- Before deploying
- When fixing bugs

## Example Usage

### Running a Specific Test
```bash
npm test -- tests/e2e/navigation.spec.js
```

### Running Tests with UI
```bash
npm run test:ui
```

### Debugging a Failing Test
```bash
npm run test:debug -- tests/e2e/app-launch.spec.js
```

## Common Test Patterns

### Finding Elements
```javascript
// By ID
const button = window.locator('#send-button');

// By class
const messages = window.locator('.chat-message');

// By text
const link = window.locator('text=Settings');

// By data attribute
const navLink = window.locator('a[data-page="chat"]');
```

### Assertions
```javascript
// Visibility
await expect(button).toBeVisible();
await expect(button).not.toBeVisible();

// Text content
await expect(heading).toHaveText('Drakyn');
await expect(status).toContainText('Connected');

// State
await expect(input).toBeEnabled();
await expect(input).toBeDisabled();

// Attributes
await expect(input).toHaveValue('test');
await expect(element).toHaveClass(/active/);
```

### Interactions
```javascript
// Click
await button.click();

// Type
await input.fill('Hello world');

// Select dropdown
await select.selectOption('option-value');

// Navigate
await window.locator('a[data-page="models"]').click();
```

## Future Enhancements

Consider adding:

1. **API Tests** - Test backend endpoints directly (works in WSL)
2. **Visual Regression Tests** - Screenshot comparison
3. **Performance Tests** - Measure load times
4. **CI Integration** - Run tests automatically on PR
5. **More Test Coverage** - Chat functionality, model loading, etc.

## Known Limitations

1. **WSL Environment**: Tests may not run in WSL due to display requirements
   - Solution: Run tests on native Windows

2. **Server Dependencies**: Some tests require the Python backend to be running
   - Tests wait for server to be ready
   - Timeout set to 30 seconds

3. **Async Operations**: Chat and model loading are async
   - Tests use proper waits and timeouts
   - May need adjustment based on actual timing

## Total Test Coverage

Currently: **24 test cases** across 4 test suites covering:
- App initialization
- Navigation system
- Model management UI
- Settings configuration

All following consistent patterns and best practices.
