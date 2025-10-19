# F1 Race Engineer - AI-Powered Strategy Dashboard

A modern, glassmorphism-inspired Electron.js dashboard for F1 race engineering with AI-driven strategy recommendations and driver behavioral analysis.

## ✨ Features

### 🧠 AI Strategy Assistant
- **Real-time Recommendations**: AI-generated insights with confidence scores
- **Personalized Strategy**: Driver behavioral parameters influence AI recommendations
- **Live Updates**: Dynamic recommendation updates every 30 seconds
- **Visual Indicators**: Color-coded icons for different recommendation types

### 🚗 Car Digital Twin
- **3D Visualization**: Interactive F1 car model with Three.js
- **Live Telemetry**: Real-time speed, RPM, fuel, and temperature data
- **Orbit Controls**: Mouse-controlled camera for 360° car inspection
- **Enhanced Lighting**: Professional lighting setup with blue accent lighting

### 🗺️ Field Digital Twin
- **Track Overview**: Real-time track conditions and competitor analysis
- **Position Tracking**: Live gap analysis and position updates
- **Environmental Data**: Track temperature and weather impact monitoring

### ⚙️ Pre-Race Configuration
- **Driver Profiling**: Behavioral parameter configuration for current and opponent drivers
- **Interactive Sliders**: Aggressiveness, Steering Ability, Flexibility, and Accuracy settings
- **Notes System**: Detailed driver analysis and strategy notes
- **Real-time Integration**: Parameters immediately influence AI recommendations

### 🎨 Modern Design
- **Glassmorphism UI**: Frosted glass effects with subtle transparency
- **Smooth Animations**: Hover effects, transitions, and micro-interactions
- **Responsive Layout**: Adapts to different screen sizes
- **Professional Aesthetics**: Clean, modern interface inspired by fintech dashboards

## 🚀 Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Run the application:**
```bash
npm start
```

3. **For development with DevTools:**
```bash
npm run dev
```

## 📊 Dashboard Layout

### Main Interface
- **Left Panel**: AI Strategy Assistant with scrollable recommendation cards
- **Top Right**: Car Digital Twin with 3D visualization and telemetry
- **Bottom Right**: Field Digital Twin with track and competitor data

### Pre-Race Configuration Modal
- **Current Driver Section**: Your driver's behavioral parameters and notes
- **Opponent Driver Section**: Competitor analysis and strategy notes
- **Interactive Controls**: Sliders for aggressiveness, steering, flexibility, and accuracy

## 🔧 Technical Features

### AI Integration
- **Driver Behavior Analysis**: Slider-based parameter input (0-10 scale)
- **Confidence Scoring**: Real-time confidence percentage updates
- **Personalized Recommendations**: AI adapts suggestions based on driver profile
- **Dynamic Updates**: Recommendations refresh based on current race conditions

### 3D Visualization
- **Three.js Integration**: Professional 3D car model rendering
- **GLTF Support**: Loads F1 car models from `/assets/models/` directory
- **Interactive Controls**: Mouse orbit controls for model inspection
- **Fallback Rendering**: Simple geometric representation if model fails to load

### Real-time Data
- **Simulated Telemetry**: Realistic F1 data updates every 2 seconds
- **Field Updates**: Track conditions and competitor data every 5 seconds
- **Confidence Fluctuations**: Dynamic confidence score variations
- **Performance Optimized**: Efficient data updates without UI blocking

## 🎯 Usage

### Basic Operation
1. **Launch the dashboard** - The main interface loads with live data
2. **Configure drivers** - Click "Pre-Race Config" to set driver parameters
3. **Monitor recommendations** - AI provides real-time strategy insights
4. **Inspect car model** - Use mouse controls to rotate the 3D car view

### Driver Configuration
1. **Open Pre-Race Config** - Click the gear icon in the header
2. **Set Current Driver Parameters**:
   - Aggressiveness: Risk-taking and defensive driving
   - Steering Ability: Cornering precision and smoothness
   - Flexibility: Adaptation to strategy changes
   - Accuracy: Optimal racing line adherence
3. **Add Driver Notes** - Detailed analysis and preferences
4. **Configure Opponent Analysis** - Competitor characteristics and strategies

### AI Recommendations
- **Tire Strategy**: Pit stop timing and compound selection
- **Fuel Management**: Consumption optimization and engine modes
- **Overtaking Opportunities**: DRS zones and timing windows
- **Weather Impact**: Track temperature and condition changes
- **Strategy Validation**: Confirmation of planned race strategy

## 🛠️ Customization

### Visual Customization
- **Colors**: Edit CSS variables in `styles.css` for brand colors
- **Glass Effects**: Adjust transparency and blur values
- **Animations**: Modify transition durations and easing functions
- **Layout**: Change grid proportions in `.dashboard-container`

### Data Integration
- **API Endpoints**: Replace simulated data with real telemetry APIs
- **Model Paths**: Update GLTF model locations in `renderer.js`
- **Recommendation Engine**: Integrate with external AI/ML services
- **Driver Profiles**: Connect to driver database or configuration files

### Performance Tuning
- **Update Intervals**: Adjust data refresh rates in `DataSimulator`
- **3D Quality**: Modify Three.js renderer settings
- **Memory Management**: Optimize recommendation history limits
- **Responsive Breakpoints**: Customize mobile/tablet layouts

## 📋 Requirements

- **Node.js**: 16+ (recommended: 18+)
- **Electron**: 28+
- **Platform**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Graphics**: WebGL support for 3D visualization

## 🔮 Future Enhancements

- **Multi-driver Support**: Configure multiple drivers and opponents
- **Race Simulation**: Full race scenario modeling and prediction
- **Data Export**: Save driver profiles and race analysis
- **Team Collaboration**: Multi-user dashboard sharing
- **Advanced Analytics**: Machine learning model integration
- **Mobile Companion**: iOS/Android app for remote monitoring

## 📝 Development Notes

- **Modular Architecture**: Clean separation of concerns with class-based components
- **Event-driven Updates**: Efficient real-time data handling
- **Error Handling**: Graceful fallbacks for 3D model loading
- **Accessibility**: Keyboard navigation and screen reader support
- **Performance**: Optimized rendering and memory management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for F1 Race Engineers and Motorsport Enthusiasts**