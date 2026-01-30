/**
 * CaptionFoundry - Electron Preload Script
 * 
 * This script runs in the renderer process before the web page loads.
 * It safely exposes select Node.js/Electron APIs to the frontend
 * using contextBridge for security.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Platform info
    platform: process.platform,
    isElectron: true,
    
    // Native dialogs
    selectFolder: (title) => ipcRenderer.invoke('select-folder', title),
    selectFile: (title, filters) => ipcRenderer.invoke('select-file', title, filters),
    selectSaveLocation: (title, defaultPath, filters) => 
        ipcRenderer.invoke('select-save-location', title, defaultPath, filters),
    
    // Logging
    log: (level, module, message, data) => 
        ipcRenderer.send('log', level, module, message, data),
    
    // Get path from dropped files (Electron adds .path to File objects)
    // This is called from the renderer after a drop event
    getDroppedPaths: (files) => {
        // In Electron, File objects have a .path property
        // This function is just for documentation - the actual .path
        // is accessed directly in the renderer
        return Array.from(files).map(f => f.path).filter(Boolean);
    }
});

console.log('[Preload] CaptionFoundry Electron API exposed');
