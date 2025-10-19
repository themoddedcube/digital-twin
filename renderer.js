// ============================================
// F1 RACE ENGINEER DASHBOARD - ENHANCED FUNCTIONALITY
// ============================================

// ============================================
// MODAL MANAGEMENT
// ============================================
class ModalManager {
  constructor() {
    this.modal = document.getElementById('pre-race-modal');
    this.openBtn = document.getElementById('pre-race-config-btn');
    this.closeBtn = document.getElementById('modal-close');
    this.init();
  }

  init() {
    this.openBtn.addEventListener('click', () => this.openModal());
    this.closeBtn.addEventListener('click', () => this.closeModal());

    // Close modal when clicking outside
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.closeModal();
      }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal.classList.contains('active')) {
        this.closeModal();
      }
    });
  }

  openModal() {
    this.modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    this.modal.classList.add('fade-in');
  }

  closeModal() {
    this.modal.classList.remove('active');
    document.body.style.overflow = '';
    this.modal.classList.remove('fade-in');
  }
}

// ============================================
// DRIVER PARAMETER MANAGEMENT
// ============================================
class DriverParameterManager {
  constructor() {
    this.sliders = document.querySelectorAll('.slider');
    this.valueDisplays = document.querySelectorAll('.param-value');
    this.init();
  }

  init() {
    this.sliders.forEach(slider => {
      slider.addEventListener('input', (e) => this.updateSliderValue(e));
      // Set initial values
      this.updateSliderValue({ target: slider });
    });
  }

  updateSliderValue(event) {
    const slider = event.target;
    const value = parseInt(slider.value);
    const valueDisplay = slider.parentElement.querySelector('.param-value');

    // Determine level and text
    let level, text;
    if (value <= 3) {
      level = 'Low';
      text = `${level} ${value}`;
    } else if (value <= 7) {
      level = 'Medium';
      text = `${level} ${value}`;
    } else {
      level = value === 10 ? 'Expert' : 'High';
      text = `${level} ${value}`;
    }

    valueDisplay.textContent = text;

    // Update slider track color
    const percentage = (value / 10) * 100;
    slider.style.background = `linear-gradient(to right, #3b82f6 ${percentage}%, rgba(148, 163, 184, 0.2) ${percentage}%)`;
  }

  getDriverProfile() {
    const profile = {
      current: {},
      opponent: {}
    };

    // Get current driver parameters
    const currentSliders = document.querySelectorAll('.current-driver .slider');
    currentSliders.forEach(slider => {
      const paramName = slider.id.replace('current-', '');
      profile.current[paramName] = parseInt(slider.value);
    });

    // Get current driver notes
    const currentNotes = document.querySelector('.current-driver textarea');
    profile.current.notes = currentNotes.value;

    // Get opponent notes
    const opponentNotes = document.querySelector('.opponent-driver textarea');
    profile.opponent.notes = opponentNotes.value;

    return profile;
  }
}

// ============================================
// AI RECOMMENDATION SYSTEM
// ============================================
class AIRecommendationSystem {
  constructor() {
    this.recommendations = [];
    this.init();
  }

  init() {
    this.generateInitialRecommendations();
    this.startRealTimeUpdates();
  }

  generateInitialRecommendations() {
    this.recommendations = [
      {
        id: 1,
        type: 'warning',
        title: 'Tire Strategy Recommendation',
        description: 'Based on current tire degradation and track temperature rising to 42°C, recommend pit stop in 3-4 laps for medium compound.',
        confidence: 94,
        timestamp: new Date()
      },
      {
        id: 2,
        type: 'fuel',
        title: 'Fuel Management Alert',
        description: 'Current fuel consumption rate is 2% above optimal. Suggest adjusting engine mode to lean mix on straights.',
        confidence: 87,
        timestamp: new Date()
      },
      {
        id: 3,
        type: 'brain',
        title: 'Overtaking Opportunity',
        description: 'Opponent showing reduced pace in sector 2. DRS advantage presents overtaking window at turn 12 in next 2 laps.',
        confidence: 91,
        timestamp: new Date()
      },
      {
        id: 4,
        type: 'success',
        title: 'Strategy On Track',
        description: 'Current pace and tire management aligns perfectly with planned 2-stop strategy. Maintain current delta.',
        confidence: 96,
        timestamp: new Date()
      },
      {
        id: 5,
        type: 'weather',
        title: 'Weather Update Impact',
        description: 'Cloud cover increasing. Track temperature may drop 3-5°C in next 15 minutes. Monitor tire pressure adjustments.',
        confidence: 82,
        timestamp: new Date()
      }
    ];
  }

  startRealTimeUpdates() {
    // Update recommendations every 30 seconds
    setInterval(() => {
      this.updateRecommendations();
    }, 30000);

    // Update confidence scores every 5 seconds
    setInterval(() => {
      this.updateConfidenceScores();
    }, 5000);
  }

  updateRecommendations() {
    // Simulate new recommendations based on driver profile
    const driverProfile = driverManager.getDriverProfile();

    // Generate personalized recommendations
    if (driverProfile.current.aggressiveness >= 8) {
      this.addRecommendation({
        type: 'brain',
        title: 'Aggressive Strategy Opportunity',
        description: 'Your high aggressiveness rating suggests an early pit stop could gain track position. Consider undercut strategy.',
        confidence: 88
      });
    }

    if (driverProfile.current.flexibility <= 5) {
      this.addRecommendation({
        type: 'warning',
        title: 'Strategy Flexibility Alert',
        description: 'Lower flexibility rating detected. Recommend sticking to planned strategy with minimal deviations.',
        confidence: 92
      });
    }
  }

  addRecommendation(recommendation) {
    const newRec = {
      id: Date.now(),
      ...recommendation,
      timestamp: new Date()
    };

    this.recommendations.unshift(newRec);

    // Keep only latest 5 recommendations
    if (this.recommendations.length > 5) {
      this.recommendations.pop();
    }

    this.renderRecommendations();
  }

  updateConfidenceScores() {
    this.recommendations.forEach(rec => {
      // Simulate confidence score fluctuations
      const variation = Math.random() * 6 - 3; // -3 to +3
      rec.confidence = Math.max(70, Math.min(99, rec.confidence + variation));
    });

    this.renderRecommendations();
  }

  renderRecommendations() {
    const container = document.querySelector('.recommendations-list');
    container.innerHTML = '';

    this.recommendations.forEach(rec => {
      const card = document.createElement('div');
      card.className = 'recommendation-card fade-in';
      card.innerHTML = `
        <div class="recommendation-icon ${rec.type}"></div>
        <div class="recommendation-content">
          <h3>${rec.title}</h3>
          <p>${rec.description}</p>
          <div class="confidence-score">${Math.round(rec.confidence)}%</div>
        </div>
      `;
      container.appendChild(card);
    });
  }
}

// ============================================
// 3D VISUALIZATION (CAR TWIN MODEL)
// ============================================
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

class Car3DVisualization {
  constructor() {
    this.canvas = document.querySelector('.car-visualization');
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.car = null;
    this.init();
  }

  init() {
    this.setupScene();
    this.loadCarModel();
    this.startAnimation();
    this.setupResizeHandler();
  }

  setupScene() {
    // Create placeholder canvas
    const canvas = document.createElement('canvas');
    canvas.className = 'car-3d-canvas';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.borderRadius = '12px';

    // Replace placeholder with canvas
    const placeholder = this.canvas.querySelector('.car-placeholder');
    this.canvas.replaceChild(canvas, placeholder);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });

    this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    this.renderer.setClearColor(0x000000, 0);

    // Enhanced lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 5, 5);
    this.scene.add(directionalLight);

    const pointLight = new THREE.PointLight(0x3b82f6, 0.5, 100);
    pointLight.position.set(-5, 5, 5);
    this.scene.add(pointLight);

    this.camera.position.set(-1, 1, 6);

    // Orbit Controls
    const controls = new OrbitControls(this.camera, this.renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.enablePan = false;
    controls.maxPolarAngle = Math.PI / 2;
    controls.minPolarAngle = Math.PI / 4;
  }

  loadCarModel() {
    const loader = new GLTFLoader();
    loader.load(
      "./assets/models/scene.gltf",
      (gltf) => {
        this.car = gltf.scene;

        // Scale & center car
        this.car.scale.set(1.5, 1.5, 1.5);
        const box = new THREE.Box3().setFromObject(this.car);
        const center = box.getCenter(new THREE.Vector3());
        this.car.position.sub(center);

        // Add subtle glow effect
        this.car.traverse((child) => {
          if (child.isMesh) {
            child.material.emissive = new THREE.Color(0x1e40af);
            child.material.emissiveIntensity = 0.1;
          }
        });

        this.scene.add(this.car);
      },
      undefined,
      (error) => {
        console.error("Error loading 3D model:", error);
        this.showFallbackVisualization();
      }
    );
  }

  showFallbackVisualization() {
    // Create a simple car representation if model fails to load
    const geometry = new THREE.BoxGeometry(2, 0.5, 4);
    const material = new THREE.MeshPhongMaterial({
      color: 0x1e40af,
      transparent: true,
      opacity: 0.8
    });
    this.car = new THREE.Mesh(geometry, material);
    this.scene.add(this.car);
  }

  startAnimation() {
    const animate = () => {
      requestAnimationFrame(animate);

      if (this.car) {
        this.car.rotation.y += 0.005;
      }

      this.renderer.render(this.scene, this.camera);
    };
    animate();
  }

  setupResizeHandler() {
    window.addEventListener("resize", () => {
      const canvas = this.renderer.domElement;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      this.renderer.setSize(width, height);
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
    });
  }
}

// ============================================
// REAL-TIME DATA SIMULATION
// ============================================
class DataSimulator {
  constructor() {
    this.carData = {
      speed: 325,
      rpm: 18000,
      fuel: 80,
      temperature: 95
    };
    this.init();
  }

  init() {
    this.startCarDataUpdates();
    this.startFieldDataUpdates();
  }

  startCarDataUpdates() {
    setInterval(() => {
      // Simulate realistic F1 data variations
      this.carData.speed = 300 + Math.floor(Math.random() * 50);
      this.carData.rpm = 17000 + Math.floor(Math.random() * 2000);
      this.carData.temperature = 90 + Math.floor(Math.random() * 10);
      this.carData.fuel = Math.max(60, this.carData.fuel - Math.random() * 0.5);

      this.updateCarDisplay();
    }, 2000);
  }

  startFieldDataUpdates() {
    setInterval(() => {
      // Simulate field data updates
      this.updateFieldDisplay();
    }, 5000);
  }

  updateCarDisplay() {
    // Update car data elements
    const speedElement = document.getElementById('speed');
    const rpmElement = document.getElementById('rpm');
    const fuelElement = document.getElementById('fuel');
    const temperatureElement = document.getElementById('temperature');
    const gearElement = document.getElementById('gear');
    const throttleElement = document.getElementById('throttle');
    const brakeElement = document.getElementById('brake');
    const drsElement = document.getElementById('drs');

    if (speedElement) speedElement.textContent = `${this.carData.speed} km/h`;
    if (rpmElement) rpmElement.textContent = this.carData.rpm.toLocaleString();
    if (fuelElement) fuelElement.textContent = `${Math.round(this.carData.fuel)}%`;
    if (temperatureElement) temperatureElement.textContent = `${this.carData.temperature}°C`;
    if (gearElement) gearElement.textContent = `${Math.floor(Math.random() * 8) + 1}th`;
    if (throttleElement) throttleElement.textContent = `${Math.floor(Math.random() * 30) + 70}%`;
    if (brakeElement) brakeElement.textContent = `${Math.floor(Math.random() * 20)}%`;
    if (drsElement) drsElement.textContent = Math.random() > 0.5 ? 'Available' : 'Not Available';
  }

  updateFieldDisplay() {
    // Update field data elements
    const trackTempElement = document.getElementById('track-temp');
    const gapLeaderElement = document.getElementById('gap-leader');
    const positionElement = document.getElementById('position');
    const flagsElement = document.getElementById('flags');
    const lapTimeElement = document.getElementById('lap-time');
    const sector1Element = document.getElementById('sector1');
    const sector2Element = document.getElementById('sector2');
    const sector3Element = document.getElementById('sector3');

    if (trackTempElement) trackTempElement.textContent = `${42 + Math.floor(Math.random() * 5)}°C`;
    if (gapLeaderElement) gapLeaderElement.textContent = `+${(Math.random() * 2).toFixed(2)}s`;
    if (positionElement) positionElement.textContent = `P${3 + Math.floor(Math.random() * 5)}`;
    if (flagsElement) flagsElement.textContent = Math.random() > 0.8 ? 'Yellow' : 'Green';
    if (lapTimeElement) lapTimeElement.textContent = `1:${23 + Math.floor(Math.random() * 5)}.${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
    if (sector1Element) sector1Element.textContent = `${28 + Math.random() * 2}`.substring(0, 6);
    if (sector2Element) sector2Element.textContent = `${32 + Math.random() * 2}`.substring(0, 6);
    if (sector3Element) sector3Element.textContent = `${22 + Math.random() * 2}`.substring(0, 6);
  }
}

// ============================================
// INITIALIZATION
// ============================================
let modalManager, driverManager, aiSystem, car3D, dataSimulator;

document.addEventListener('DOMContentLoaded', () => {
  // Initialize all systems
  modalManager = new ModalManager();
  driverManager = new DriverParameterManager();
  aiSystem = new AIRecommendationSystem();
  car3D = new Car3DVisualization();
  dataSimulator = new DataSimulator();

  // Add loading animation
  document.body.classList.add('loaded');

  console.log('F1 Race Engineer Dashboard initialized successfully');
});

// ============================================
// UTILITY FUNCTIONS
// ============================================
function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString();
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Export for potential external use
window.F1Dashboard = {
  modalManager,
  driverManager,
  aiSystem,
  car3D,
  dataSimulator
};