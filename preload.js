// Preload script for F1 Dashboard
// This script runs in the renderer process before the web content begins loading

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Add any IPC communication methods here if needed in the future
  // For now, this is just a placeholder to prevent errors
});

console.log('F1 Dashboard preload script loaded');