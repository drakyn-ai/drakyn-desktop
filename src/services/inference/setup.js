/**
 * Python environment setup utility
 * Automatically creates venv and installs dependencies
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Find Python executable on the system
 */
function findPython() {
  const candidates = ['python', 'python3', 'py'];

  for (const candidate of candidates) {
    try {
      const result = execSync(`${candidate} --version`, { encoding: 'utf8' });
      if (result.includes('Python 3.')) {
        console.log(`Found Python: ${candidate} - ${result.trim()}`);
        return candidate;
      }
    } catch (e) {
      // Try next candidate
    }
  }

  throw new Error('Python 3 not found. Please install Python 3.10 or later.');
}

/**
 * Check if virtual environment exists
 */
function venvExists(venvPath) {
  const activateScript = process.platform === 'win32'
    ? path.join(venvPath, 'Scripts', 'python.exe')
    : path.join(venvPath, 'bin', 'python');

  return fs.existsSync(activateScript);
}

/**
 * Create virtual environment
 */
function createVenv(pythonCmd, venvPath, onProgress) {
  return new Promise((resolve, reject) => {
    onProgress('Creating Python virtual environment...');

    const venv = spawn(pythonCmd, ['-m', 'venv', venvPath], {
      stdio: 'pipe'
    });

    venv.stdout.on('data', (data) => {
      console.log(data.toString());
    });

    venv.stderr.on('data', (data) => {
      console.error(data.toString());
    });

    venv.on('close', (code) => {
      if (code === 0) {
        onProgress('Virtual environment created successfully');
        resolve();
      } else {
        reject(new Error(`Failed to create venv, exit code: ${code}`));
      }
    });

    venv.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Install Python dependencies
 */
function installDependencies(venvPath, requirementsPath, onProgress) {
  return new Promise((resolve, reject) => {
    const pipCmd = process.platform === 'win32'
      ? path.join(venvPath, 'Scripts', 'pip.exe')
      : path.join(venvPath, 'bin', 'pip');

    onProgress('Installing Python dependencies (this may take several minutes)...');

    const pip = spawn(pipCmd, ['install', '-r', requirementsPath], {
      stdio: 'pipe'
    });

    pip.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(output);

      // Extract package names for progress feedback
      if (output.includes('Collecting')) {
        const match = output.match(/Collecting (.+)/);
        if (match) {
          onProgress(`Installing ${match[1]}...`);
        }
      }
    });

    pip.stderr.on('data', (data) => {
      console.error(data.toString());
    });

    pip.on('close', (code) => {
      if (code === 0) {
        onProgress('Dependencies installed successfully');
        resolve();
      } else {
        reject(new Error(`Failed to install dependencies, exit code: ${code}`));
      }
    });

    pip.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Main setup function
 */
async function setupPythonEnvironment(serviceDir, onProgress = console.log) {
  const venvPath = path.join(serviceDir, 'venv');
  const requirementsPath = path.join(serviceDir, 'requirements.txt');

  try {
    // Check if venv already exists
    if (venvExists(venvPath)) {
      onProgress('Python environment already exists, skipping setup');
      return { venvPath, alreadyExists: true };
    }

    // Find Python
    onProgress('Looking for Python installation...');
    const pythonCmd = findPython();

    // Create venv
    await createVenv(pythonCmd, venvPath, onProgress);

    // Install dependencies
    await installDependencies(venvPath, requirementsPath, onProgress);

    onProgress('Python environment setup complete!');
    return { venvPath, alreadyExists: false };

  } catch (error) {
    onProgress(`Setup failed: ${error.message}`);
    throw error;
  }
}

module.exports = {
  setupPythonEnvironment,
  venvExists,
  findPython
};
