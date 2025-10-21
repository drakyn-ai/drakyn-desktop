# E2E Testing Setup Notes

## WSL Limitations

**Important**: E2E tests with Playwright require launching the actual Electron app with a display. This has limitations on WSL:

### On WSL (Current Environment)

Electron GUI apps don't work well in WSL without X11 server setup. The tests are configured but may not run successfully in WSL without additional setup.

**Options for running tests in WSL:**

1. **Use Windows Node directly** (Recommended for WSL users):
   ```bash
   # From Windows PowerShell/CMD (not WSL)
   cd C:\Users\chanh\drakyn\drakyn-desktop
   npm test
   ```

2. **Set up X11 server** (Advanced):
   - Install VcXsrv or X410 on Windows
   - Configure DISPLAY environment variable in WSL
   - May still have issues with GPU

### On Native Windows/Mac/Linux

Tests should work out of the box:
```bash
npm test
```

## Alternative: API Testing

For testing on WSL, consider testing the backend API directly without launching the Electron GUI:

```javascript
// tests/api/server.spec.js
const { test, expect } = require('@playwright/test');

test('health endpoint responds', async ({ request }) => {
  const response = await request.get('http://localhost:8000/health');
  expect(response.ok()).toBeTruthy();
});
```

This tests the Python server independently without needing the Electron GUI.

## When to Run E2E Tests

As the coding agent, you should:

1. **Write E2E tests** for all new features (following patterns in existing tests)
2. **Run tests on native Windows** when possible (not WSL)
3. **Document what you tested** if you can't run tests yourself
4. **Let Chanh know** to run tests manually on his Windows system

## Test Files Created

- `tests/e2e/app-launch.spec.js` - App launch and basic UI
- `tests/e2e/navigation.spec.js` - Page navigation
- `tests/e2e/models-page.spec.js` - Model configuration
- `tests/e2e/settings-page.spec.js` - Settings functionality

All tests follow the same pattern and are ready to run on a system with proper display support.
