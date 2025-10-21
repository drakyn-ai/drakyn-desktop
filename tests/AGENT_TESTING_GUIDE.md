# Agent Testing Guide

**Quick reference for coding agents writing E2E tests for drakyn-desktop**

## When to Write Tests

Write E2E tests for:
- ✅ New UI features (buttons, forms, pages)
- ✅ Navigation flows
- ✅ User workflows (multi-step processes)
- ✅ State changes (button enables/disables, visibility toggles)
- ✅ Form validation
- ✅ Error states

Don't write E2E tests for:
- ❌ Pure backend logic (use unit tests instead)
- ❌ Styling/layout (visual testing required)
- ❌ Performance benchmarks (use specialized tools)

## Quick Start: Adding a Test for New Feature

### Step 1: Create Test File

```bash
# File: tests/e2e/my-feature.spec.js
```

### Step 2: Copy Template

Use `tests/e2e/TEMPLATE.spec.js` as a starting point.

### Step 3: Write Test Cases

```javascript
const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp } = require('./helpers/electron');

test.describe('My Feature', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should work correctly', async () => {
    // Your test code
  });
});
```

### Step 4: Run Test

```bash
npm test -- tests/e2e/my-feature.spec.js
```

## Most Common Patterns

### Pattern 1: Test Element Exists
```javascript
test('should display the button', async () => {
  const button = window.locator('#my-button');
  await expect(button).toBeVisible();
});
```

### Pattern 2: Test Click Interaction
```javascript
test('should navigate when clicked', async () => {
  await window.locator('a[data-page="models"]').click();
  await expect(window.locator('#models-page')).toHaveClass(/active/);
});
```

### Pattern 3: Test Form Input
```javascript
test('should accept input', async () => {
  const input = window.locator('#model-path');
  await input.fill('test-model:latest');
  await expect(input).toHaveValue('test-model:latest');
});
```

### Pattern 4: Test Button State
```javascript
test('should enable button when ready', async () => {
  const button = window.locator('#send-button');
  await expect(button).toBeDisabled();  // Initially disabled

  // Do something that enables it
  await window.locator('#message-input').fill('test');

  await expect(button).toBeEnabled();  // Now enabled
});
```

### Pattern 5: Test Error Message
```javascript
test('should show error on failure', async () => {
  await window.locator('#load-model-btn').click();
  const status = window.locator('#load-status');
  await expect(status).toContainText('Error:');
});
```

## Locator Cheat Sheet

```javascript
// By ID
window.locator('#element-id')

// By class
window.locator('.class-name')

// By text content
window.locator('text=Button Text')

// By data attribute
window.locator('[data-page="chat"]')

// By tag and text
window.locator('button:has-text("Send")')

// Nested elements
window.locator('#parent .child')

// Multiple elements
window.locator('.list-item')  // All items
window.locator('.list-item').nth(0)  // First item
window.locator('.list-item').first()  // First item
window.locator('.list-item').last()  // Last item
```

## Assertion Cheat Sheet

```javascript
// Visibility
await expect(element).toBeVisible()
await expect(element).not.toBeVisible()

// Text
await expect(element).toHaveText('exact')
await expect(element).toContainText('partial')

// Count
await expect(elements).toHaveCount(5)

// State
await expect(element).toBeEnabled()
await expect(element).toBeDisabled()

// Value
await expect(input).toHaveValue('text')

// Class
await expect(element).toHaveClass(/active/)

// Attribute
await expect(element).toHaveAttribute('type', 'password')

// With custom timeout (default is 5000ms)
await expect(element).toBeVisible({ timeout: 10000 })
```

## Interaction Cheat Sheet

```javascript
// Click
await element.click()

// Type text
await input.fill('text')

// Clear input
await input.clear()

// Select dropdown
await select.selectOption('value')

// Checkbox
await checkbox.check()
await checkbox.uncheck()

// Hover
await element.hover()

// Wait for element
await element.waitFor({ state: 'visible' })
```

## Workflow for Adding Feature + Test

### Example: Adding a "Clear Chat" Button

**1. Implement the Feature**

Add button to [public/index.html](../public/index.html):
```html
<button id="clear-chat-btn">Clear Chat</button>
```

Add handler to [public/app.js](../public/app.js):
```javascript
document.getElementById('clear-chat-btn').addEventListener('click', () => {
  document.getElementById('chat-messages').innerHTML = '';
});
```

**2. Write the Test**

Create `tests/e2e/clear-chat.spec.js`:
```javascript
const { test, expect } = require('@playwright/test');
const { launchElectronApp, closeElectronApp } = require('./helpers/electron');

test.describe('Clear Chat', () => {
  let app, window;

  test.beforeEach(async () => {
    const launched = await launchElectronApp();
    app = launched.app;
    window = launched.window;
  });

  test.afterEach(async () => {
    await closeElectronApp(app);
  });

  test('should clear messages when clicked', async () => {
    // Add a message first
    const messagesContainer = window.locator('#chat-messages');

    // Assume there's a way to add messages (adjust to your implementation)
    // For this example, let's say we manually add one via DOM manipulation
    await window.evaluate(() => {
      const div = document.createElement('div');
      div.textContent = 'Test message';
      document.getElementById('chat-messages').appendChild(div);
    });

    // Verify message exists
    const messages = window.locator('#chat-messages > div');
    await expect(messages).toHaveCount(1);

    // Click clear button
    await window.locator('#clear-chat-btn').click();

    // Verify messages cleared
    await expect(messages).toHaveCount(0);
  });
});
```

**3. Run the Test**

```bash
npm test -- tests/e2e/clear-chat.spec.js
```

**4. Document What Was Tested**

In your commit message or PR description, mention:
- "Added E2E test for clear chat functionality"
- "Test verifies messages are cleared when button is clicked"

## Common Issues & Solutions

### Issue: Element not found
```
Error: locator.click: Target closed
```

**Solution**: Wait for element to exist
```javascript
await element.waitFor({ state: 'visible' });
await element.click();
```

### Issue: Timing issues
```
Error: Timeout exceeded
```

**Solution**: Increase timeout or wait for specific state
```javascript
await expect(element).toBeVisible({ timeout: 10000 });
```

### Issue: Element exists but can't interact
```
Error: Element is not visible
```

**Solution**: Check if element is actually visible in the UI
```javascript
const isVisible = await element.isVisible();
console.log('Is visible:', isVisible);
```

### Issue: Wrong element selected
```
Error: Expected "X" but got "Y"
```

**Solution**: Use more specific locator
```javascript
// Instead of:
window.locator('button')

// Use:
window.locator('#specific-button-id')
// or
window.locator('button:has-text("Specific Text")')
```

## Testing Checklist

Before considering a feature complete:

- [ ] Feature implemented
- [ ] E2E test written
- [ ] Test passes locally (or documented if can't run in WSL)
- [ ] Test covers happy path
- [ ] Test covers error cases
- [ ] Test is descriptive (good test name)
- [ ] Test is independent (doesn't depend on other tests)
- [ ] Test is documented (comments for complex logic)

## Remember

1. **Always write tests for new UI features** - This is the main goal
2. **Follow existing patterns** - Look at `tests/e2e/*.spec.js` for examples
3. **Test behavior, not implementation** - Test what users see/do
4. **Keep tests simple** - One concept per test
5. **Use descriptive names** - "should enable send button when message is typed"
6. **Don't worry if you can't run in WSL** - Document what you tested

## Quick Commands

```bash
# Run all tests
npm test

# Run specific test file
npm test -- tests/e2e/my-test.spec.js

# Run with UI visible
npm run test:headed

# Interactive test runner
npm run test:ui

# Debug mode
npm run test:debug
```

## When Tests Fail in WSL

Since you're running in WSL, tests may not run due to display requirements. When this happens:

1. **Still write the tests** - Follow patterns from existing tests
2. **Document in commit message**: "Added E2E tests (not verified in WSL)"
3. **Let Chanh know**: "Tests need to be run on Windows to verify"
4. **Trust the patterns**: If you followed existing test patterns, they should work

The tests are valuable even if you can't run them immediately. Chanh can run them on native Windows to verify.
