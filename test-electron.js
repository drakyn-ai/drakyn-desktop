console.log('Loading electron...');
const electron = require('electron');
console.log('Electron object:', Object.keys(electron));
console.log('app:', typeof electron.app);
console.log('BrowserWindow:', typeof electron.BrowserWindow);

if (electron.app) {
  console.log('App ready! Exiting...');
  electron.app.quit();
} else {
  console.log('ERROR: app is undefined!');
  process.exit(1);
}
