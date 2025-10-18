const { app, BrowserWindow } = require("electron")
const path = require("path")

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    frame: false, // Frameless window
    transparent: true, // Enable transparency
    alwaysOnTop: true, // Float above other windows
    resizable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      backgroundThrottling: false, // Keep animations running
    },
  })

  // Enable click-through for transparent areas (Windows/Linux)
  if (process.platform === "win32" || process.platform === "linux") {
    mainWindow.setIgnoreMouseEvents(false)
  }

  mainWindow.loadFile("index.html")

  // Open DevTools in development mode
  if (process.argv.includes("--dev")) {
    mainWindow.webContents.openDevTools()
  }

  mainWindow.on("closed", () => {
    mainWindow = null
  })
}

app.whenReady().then(createWindow)

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit()
  }
})

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
