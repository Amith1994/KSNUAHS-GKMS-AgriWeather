const { app, BrowserWindow, dialog, Menu, shell, ipcMain } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

// Disable hardware acceleration for older machines
// app.disableHardwareAcceleration();

let mainWindow;

// Register IPC handlers for local file access (needed for admin updates)
ipcMain.handle('read-file', async (event, fileName) => {
    try {
        const filePath = path.join(__dirname, fileName);
        return fs.readFileSync(filePath, 'utf-8');
    } catch (err) {
        throw new Error(`Failed to read file ${fileName}: ${err.message}`);
    }
});

ipcMain.handle('write-file', async (event, fileName, content) => {
    try {
        const filePath = path.join(__dirname, fileName);
        fs.writeFileSync(filePath, content, 'utf-8');
        return true;
    } catch (err) {
        throw new Error(`Failed to write file ${fileName}: ${err.message}`);
    }
});

ipcMain.handle('git-publish', async (event) => {
    return new Promise((resolve, reject) => {
        const shellPath = process.platform === 'win32'
            ? path.join(process.env.SystemRoot || process.env.windir || 'C:\\Windows', 'System32', 'cmd.exe')
            : '/bin/sh';

        // Run git commands: stage both files, commit, and push
        const command = 'git add 1st_updated.html index.html && git commit -m "Auto-update weather data via Admin Portal" && git push';
        exec(command, { cwd: __dirname, shell: shellPath }, (error, stdout, stderr) => {
            if (error) {
                // Check if the error is just 'nothing to commit'
                if (stdout.includes('nothing to commit') || stderr.includes('nothing to commit') || error.message.includes('nothing to commit')) {
                    resolve('Nothing to commit, working tree clean.');
                    return;
                }
                reject(new Error(stderr || error.message));
                return;
            }
            resolve(stdout || 'Successfully committed and pushed changes to GitHub!');
        });
    });
});

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1360,
        height: 900,
        minWidth: 800,
        minHeight: 600,
        title: 'GKMS Karnataka — Weather Forecast',
        icon: path.join(__dirname, 'assets', 'icon.png'),
        backgroundColor: '#FFF8F0',
        show: false, // Show after ready-to-show for smooth startup
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            spellcheck: false,
            webSecurity: false,
        }
    });

    // Load the main weather app
    mainWindow.loadFile('1st_updated.html');

    // Show window when content is ready (avoids white flash)
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Handle external links — open in default browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Intercept navigation to index.html (map page) — open in same window
    mainWindow.webContents.on('will-navigate', (event, url) => {
        // Allow local file navigation (map page, admin page)
        if (url.startsWith('file://')) return;
        // External URLs open in browser
        event.preventDefault();
        shell.openExternal(url);
    });
}

// ═══════════════════════════════════════════════════════
//  SIMPLE MENU
// ═══════════════════════════════════════════════════════
function createMenu() {
    const template = [
        {
            label: 'GKMS',
            submenu: [
                { label: 'Weather App', click: () => mainWindow.loadFile('1st_updated.html') },
                { label: 'Map Dashboard', click: () => mainWindow.loadFile('index.html') },
                { label: 'Admin Portal', click: () => mainWindow.loadFile('admin.html') },
                { type: 'separator' },
                { label: 'Check for Updates', click: () => checkForUpdates(true) },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { role: 'resetZoom' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        }
    ];
    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ═══════════════════════════════════════════════════════
//  AUTO-UPDATE (from GitHub Releases — 100% free)
// ═══════════════════════════════════════════════════════
let manualCheck = false;

function checkForUpdates(manual = false) {
    manualCheck = manual;
    autoUpdater.checkForUpdates().catch(err => {
        if (manual) {
            dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Update Check',
                message: 'Could not check for updates. Please check your internet connection.',
            });
        }
        console.log('Update check failed:', err.message);
    });
}

function setupAutoUpdater() {
    // Don't auto-download — let user decide
    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;

    autoUpdater.on('checking-for-update', () => {
        console.log('Checking for updates...');
    });

    autoUpdater.on('update-available', (info) => {
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: '🆕 Update Available',
            message: `A new version (v${info.version}) is available!\n\nCurrent: v${app.getVersion()}\nNew: v${info.version}\n\nDownload now?`,
            buttons: ['Download', 'Later'],
            defaultId: 0,
        }).then(result => {
            if (result.response === 0) {
                autoUpdater.downloadUpdate();
            }
        });
    });

    autoUpdater.on('update-not-available', () => {
        if (manualCheck) {
            dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: '✅ Up to Date',
                message: `You're running the latest version (v${app.getVersion()}).`,
            });
        }
        manualCheck = false;
    });

    autoUpdater.on('download-progress', (progress) => {
        const msg = `Downloading update: ${Math.round(progress.percent)}%`;
        mainWindow.setProgressBar(progress.percent / 100);
        console.log(msg);
    });

    autoUpdater.on('update-downloaded', () => {
        mainWindow.setProgressBar(-1); // Remove progress bar
        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: '✅ Update Ready',
            message: 'The update has been downloaded.\nRestart the app to apply the update.',
            buttons: ['Restart Now', 'Later'],
            defaultId: 0,
        }).then(result => {
            if (result.response === 0) {
                autoUpdater.quitAndInstall();
            }
        });
    });

    autoUpdater.on('error', (err) => {
        console.log('Auto-update error:', err.message);
    });

    // Check for updates 5 seconds after launch (silent)
    setTimeout(() => checkForUpdates(false), 5000);
}

// ═══════════════════════════════════════════════════════
//  APP LIFECYCLE
// ═══════════════════════════════════════════════════════
app.whenReady().then(() => {
    createWindow();
    createMenu();
    setupAutoUpdater();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});
