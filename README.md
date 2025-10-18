# F1 Data Visualization Dashboard

A transparent, floating Electron.js dashboard for F1 data visualization with resizable panels and 3D model integration points.

## Features

- **Transparent Overlay**: Frameless, semi-transparent window that floats above your desktop
- **Resizable Panels**: All four panels can be independently resized by dragging the resize handles
- **Dark Theme**: Modern dark aesthetic with blur effects and high contrast text
- **3D Ready**: Placeholder canvases ready for Three.js integration
- **Real-time Data**: Simulated live data updates for car telemetry

## Installation

1. Install dependencies:
\`\`\`bash
npm install
\`\`\`

2. Run the application:
\`\`\`bash
npm start
\`\`\`

3. For development with DevTools:
\`\`\`bash
npm run dev
\`\`\`

## Panel Layout

1. **LLM HPC Layer Outputs** (Large Left): AI-generated racing insights and recommendations
2. **F1 Car 3D Model** (Top Right): Placeholder for spinning 3D car model
3. **F1 Car Digital Twin Data** (Middle Right): Real-time telemetry data
4. **Track Digital Twin** (Bottom Right): Placeholder for track visualization with animated cars

## Adding 3D Models

To integrate Three.js 3D models:

1. Install Three.js:
\`\`\`bash
npm install three
\`\`\`

2. Uncomment the 3D initialization code in `renderer.js`
3. Add your F1 car model (`.glb` or `.gltf` format) to the project
4. Update the model paths in the loader functions

See the commented sections in `renderer.js` for detailed integration instructions.

## Customization

- **Colors**: Edit the CSS variables in `styles.css`
- **Panel Layout**: Modify the grid layout in `.panels-container`
- **Data Updates**: Adjust the `updateCarData()` function in `renderer.js`
- **Transparency**: Change the `rgba` values in `.app-container` background

## Requirements

- Node.js 16+
- Electron 28+
- Windows/macOS/Linux

## Notes

- The window is set to `alwaysOnTop: true` to float above other applications
- Resize handles are located in the top-right corner of each panel header
- The title bar is draggable to reposition the entire window
