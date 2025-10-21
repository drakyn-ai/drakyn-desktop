# Testing Documentation

Complete testing setup for drakyn-desktop Electron application.

## Quick Links

- **[TESTING.md](../TESTING.md)** - Comprehensive E2E testing guide for developers
- **[AGENT_TESTING_GUIDE.md](AGENT_TESTING_GUIDE.md)** - Quick reference for coding agents
- **[e2e/README.md](e2e/README.md)** - E2E setup notes and WSL limitations
- **[e2e/TEMPLATE.spec.js](e2e/TEMPLATE.spec.js)** - Template for new tests

## Running Tests

```bash
# Run all E2E tests
npm test

# Run with visible browser
npm run test:headed

# Interactive test runner
npm run test:ui

# Debug mode
npm run test:debug

# Run specific test file
npm test -- tests/e2e/my-test.spec.js
```

## Test Structure

```
tests/
├── README.md                       # This file
├── AGENT_TESTING_GUIDE.md          # Quick reference for agents
├── e2e/                            # End-to-end tests
│   ├── README.md                   # E2E setup notes
│   ├── TEMPLATE.spec.js            # Test template
│   ├── helpers/
│   │   └── electron.js             # Test utilities
│   ├── app-launch.spec.js          # App launch tests
│   ├── navigation.spec.js          # Navigation tests
│   ├── models-page.spec.js         # Model configuration tests
│   └── settings-page.spec.js       # Settings tests
└── [future: unit/, api/]           # Future test types
```

## Current Test Coverage

### 24 E2E Tests Across 4 Suites:

**App Launch (5 tests)**
- App launches successfully
- Header and logo display
- Navigation menu items
- Default page (Chat)
- Connection status indicator

**Navigation (4 tests)**
- Navigate to Models page
- Navigate to Settings page
- Navigate to Agents page
- Navigate back to Chat

**Models Page (8 tests)**
- Model configuration UI
- Dropdown with cloud/local options
- Custom model input
- Loaded models section
- Server status section
- Refresh models button
- Custom model entry
- Error handling

**Settings Page (7 tests)**
- Server control section
- Inference engine configuration
- OpenAI URL visibility toggle
- API keys section
- Current configuration display
- Gmail integration
- Input field functionality

## For Developers (Human)

See **[TESTING.md](../TESTING.md)** for:
- How to write tests
- Common patterns
- Best practices
- Debugging tips
- Full examples

## For Coding Agents

See **[AGENT_TESTING_GUIDE.md](AGENT_TESTING_GUIDE.md)** for:
- Quick patterns
- Cheat sheets
- Common workflows
- Troubleshooting

## Environment Notes

### WSL (Current Environment)
- E2E tests require display/GUI
- Tests may not run in WSL without X11
- **Recommended**: Run tests on native Windows

### Native Windows/Mac/Linux
- Tests should work out of the box
- No additional setup required

## Writing Your First Test

1. **Copy the template:**
   ```bash
   cp tests/e2e/TEMPLATE.spec.js tests/e2e/my-feature.spec.js
   ```

2. **Modify for your feature:**
   ```javascript
   test.describe('My Feature', () => {
     // ... see template for structure
   });
   ```

3. **Run the test:**
   ```bash
   npm test -- tests/e2e/my-feature.spec.js
   ```

## Philosophy

### What We Test

✅ **User-visible behavior**
- Does the button appear?
- Does clicking work?
- Does the form submit?
- Does the error show?

❌ **Implementation details**
- Internal function calls
- State management internals
- Specific algorithms

### Test Characteristics

- **Independent**: Each test can run alone
- **Repeatable**: Same result every time
- **Fast**: Complete in seconds
- **Clear**: Obvious what's being tested
- **Maintainable**: Easy to update when UI changes

## Integration with Development

### Workflow

1. Write/modify feature code
2. Write/update E2E test
3. Run test to verify
4. Commit both together

### CI/CD (Future)

Tests are configured for CI with:
- Automatic retries on failure
- Screenshot capture on errors
- HTML report generation
- Headless execution

## Future Enhancements

- [ ] API tests (test backend independently)
- [ ] Unit tests (test individual functions)
- [ ] Visual regression tests (screenshot comparison)
- [ ] Performance tests (load time monitoring)
- [ ] CI/CD integration (automated testing)
- [ ] Test coverage reports
- [ ] More E2E scenarios (chat, model loading workflows)

## Need Help?

- Check [TESTING.md](../TESTING.md) for detailed guide
- Look at existing tests in `e2e/*.spec.js` for patterns
- Use [TEMPLATE.spec.js](e2e/TEMPLATE.spec.js) as starting point
- See [AGENT_TESTING_GUIDE.md](AGENT_TESTING_GUIDE.md) for quick reference

## Tools & Frameworks

- **[Playwright](https://playwright.dev/)** - E2E testing framework
- **[@playwright/test](https://playwright.dev/docs/api/class-test)** - Test runner
- **Electron** - Via Playwright's Electron support

## Configuration

- **[playwright.config.js](../playwright.config.js)** - Test runner config
- Test timeout: 60 seconds
- Workers: 1 (sequential execution)
- Reports: HTML report in `playwright-report/`
- Screenshots: On failure only
- Trace: On first retry

---

**Last Updated**: October 2025
**Status**: ✅ Fully configured and ready to use
**Test Count**: 24 E2E tests
**Coverage**: Basic UI and navigation
