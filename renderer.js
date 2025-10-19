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
      this.generateInitialRecommendations();
    }, 20000);

    // Update confidence scores every 5 seconds
    setInterval(() => {
      this.updateConfidenceScores();
    }, 5000);
  }

 

  generateInitialRecommendations() {
    const allRecommendations = [
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
      },
      {
        id: 6,
        type: 'warning',
        title: 'Brake Temperature Alert',
        description: 'Front-left brake temp exceeding optimal range. Consider adjusted brake balance for next sector.',
        confidence: 89,
        timestamp: new Date()
      },
      {
        id: 7,
        type: 'success',
        title: 'DRS Zone Efficiency',
        description: 'Excellent DRS usage detected. Maintaining 0.3s gain per activation compared to field average.',
        confidence: 93,
        timestamp: new Date()
      },
      {
        id: 8,
        type: 'brain',
        title: 'Sector Performance Analysis',
        description: 'Sector 3 times improving. Current pace suggests potential for purple sector in next 2 laps.',
        confidence: 85,
        timestamp: new Date()
      },
      {
        id: 9,
        type: 'fuel',
        title: 'Energy Deployment Optimization',
        description: 'ERS deployment pattern suboptimal in sector 1. Recommend full deployment on exit of turn 3.',
        confidence: 91,
        timestamp: new Date()
      },
      {
        id: 10,
        type: 'weather',
        title: 'Wind Direction Change',
        description: 'Wind shifted to tailwind in sector 2. Adjust downforce settings for maximum straight-line speed.',
        confidence: 88,
        timestamp: new Date()
      },
      {
        id: 11,
        type: 'warning',
        title: 'Gearbox Temperature Rising',
        description: 'Gearbox temp approaching upper limit. Recommend smoother gear changes for next 5 laps.',
        confidence: 86,
        timestamp: new Date()
      },
      {
        id: 12,
        type: 'brain',
        title: 'Traffic Management Strategy',
        description: 'Lapped car ahead in 2 laps. Optimal overtake location identified at turn 7 DRS zone.',
        confidence: 90,
        timestamp: new Date()
      },
      {
        id: 13,
        type: 'success',
        title: 'Lap Time Consistency',
        description: 'Outstanding consistency: last 5 laps within 0.2s variance. Maintain current rhythm.',
        confidence: 97,
        timestamp: new Date()
      },
      {
        id: 14,
        type: 'fuel',
        title: 'Fuel Load Advantage',
        description: 'Lighter fuel load than competitors. Consider pushing for 3 laps to build gap before pit stop.',
        confidence: 92,
        timestamp: new Date()
      },
      {
        id: 15,
        type: 'warning',
        title: 'Front Wing Vibration Detected',
        description: 'Sensor data indicates minor front wing vibration. Monitor for damage, consider inspection at pit stop.',
        confidence: 84,
        timestamp: new Date()
      },
      {
        id: 16,
        type: 'weather',
        title: 'Track Grip Evolution',
        description: 'Track grip improving as rubber builds up. Expect 0.3-0.5s lap time improvement over next 10 laps.',
        confidence: 89,
        timestamp: new Date()
      },
      {
        id: 17,
        type: 'brain',
        title: 'Undercut Window Opening',
        description: 'Competitor tire deg 15% higher than ours. Undercut opportunity available in next 2 laps.',
        confidence: 94,
        timestamp: new Date()
      },
      {
        id: 18,
        type: 'success',
        title: 'Power Unit Performance',
        description: 'PU operating at peak efficiency. Current deployment strategy optimal for race conditions.',
        confidence: 95,
        timestamp: new Date()
      },
      {
        id: 19,
        type: 'warning',
        title: 'Tire Pressure Adjustment Needed',
        description: 'Right-side tire pressures 0.5 PSI below target. Recommend adjustment at next pit stop.',
        confidence: 87,
        timestamp: new Date()
      },
      {
        id: 20,
        type: 'fuel',
        title: 'Lift and Coast Recommendation',
        description: 'Fuel margin tight for current pace. Implement lift and coast 50m earlier at turns 8 and 14.',
        confidence: 90,
        timestamp: new Date()
      },
      {
        id: 21,
        type: 'brain',
        title: 'Safety Car Probability',
        description: 'Historical data suggests 35% safety car probability in next 15 laps. Prepare alternate strategy.',
        confidence: 78,
        timestamp: new Date()
      },
      {
        id: 22,
        type: 'weather',
        title: 'Humidity Rising',
        description: 'Humidity increased 12% in last 10 minutes. May affect brake cooling and tire temps.',
        confidence: 83,
        timestamp: new Date()
      },
      {
        id: 23,
        type: 'success',
        title: 'Cornering Speed Optimal',
        description: 'Minimum corner speeds exceeding targets in all high-speed corners. Excellent car balance.',
        confidence: 94,
        timestamp: new Date()
      },
      {
        id: 24,
        type: 'warning',
        title: 'Battery Charge Cycle',
        description: 'Battery not reaching full charge on straights. Adjust harvesting settings to maximize deployment.',
        confidence: 88,
        timestamp: new Date()
      },
      {
        id: 25,
        type: 'brain',
        title: 'Fastest Lap Opportunity',
        description: 'Fresh tire advantage and fuel load create fastest lap window. Recommend push in next 3 laps.',
        confidence: 91,
        timestamp: new Date()
      }
    ];

    // Randomly select 5 recommendations
    this.recommendations = this.getRandomRecommendations(allRecommendations, 5);
  }

  getRandomRecommendations(array, count) {
    const shuffled = [...array].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
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

// renderer.js
// renderer.js




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

//3d track
// import * as THREE from "three";
// import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
// import { OrbitControls } from "three/addons/controls/OrbitControls.js";

class Track3DVisualization {
  constructor() {
    this.canvas = document.querySelector('.track-visualization');
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.track = null;
    this.init();
  }

  init() {
    this.setupScene();
    this.loadTrackModel();
    this.startAnimation();
    this.setupResizeHandler();
  }

  setupScene() {
    // Create placeholder canvas
    const canvas = document.createElement('canvas');
    canvas.className = 'track-3d-canvas';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.borderRadius = '12px';

    // Replace placeholder with canvas
    const placeholder = this.canvas.querySelector('.track-placeholder');
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

    this.camera.position.set(-1, 1, 1);

    // Orbit Controls
    const controls = new OrbitControls(this.camera, this.renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.enablePan = false;
    controls.maxPolarAngle = Math.PI / 2;
    controls.minPolarAngle = Math.PI / 4;
  }

  loadTrackModel() {
    const loader = new GLTFLoader();
    loader.load(
      "./assets/models/f1-track.gltf",
      (gltf) => {
        this.track = gltf.scene;
        // this.track.scale.set(1, 1, 1);
  
        const box = new THREE.Box3().setFromObject(this.track);
        const center = box.getCenter(new THREE.Vector3());
        this.track.position.sub(center);
  
        this.scene.add(this.track);
  
        // Setup Animation Mixer
        this.mixer = new THREE.AnimationMixer(this.track);
  
        gltf.animations.forEach((clip) => {
          this.mixer.clipAction(clip).play();
        });
  
      },
      undefined,
      (error) => {
        console.error("Error loading 3D model:", error);
        this.showFallbackVisualization();
      }
    );
  }
  

  

  showFallbackVisualization() {
    // Create a simple track representation if model fails to load
    const geometry = new THREE.BoxGeometry(2, 0.5, 4);
    const material = new THREE.MeshPhongMaterial({
      color: 0x1e40af,
      transparent: true,
      opacity: 0.8
    });
    this.track = new THREE.Mesh(geometry, material);
    this.scene.add(this.track);
  }

  startAnimation() {
    const clock = new THREE.Clock();
  
    const animate = () => {
      requestAnimationFrame(animate);
  
      const delta = clock.getDelta();
  
      // Update GLTF animations
      if (this.mixer) this.mixer.update(delta);
  
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
async function updateCarData() {
  try {
    // First API
    let response = await fetch("https://8000-fcdhxcev1.brevlab.com/api/v1/car-twin");
    let data = await response.json();
    let strategy = data.car_twin.strategy_metrics;

    document.getElementById("performanceDelta").textContent = `${strategy.performance_delta.toFixed(2)}%`;
    document.getElementById("tireRate").textContent = strategy.tire_degradation_rate.toFixed(4);
    document.getElementById("pitWindow").textContent = `${strategy.optimal_pit_window[0]} - ${strategy.optimal_pit_window[1]}`;
    document.getElementById("pitLap").textContent = strategy.predicted_pit_lap;

    // Second API
    let response1 = await fetch("https://8000-fcdhxcev1.brevlab.com/api/v1/environment");
    let data1 = await response1.json();
    let weather = data1.environment.weather.condition;
    document.getElementById("weather").textContent = weather;

    // Third API
    let response2 = await fetch("https://8000-fcdhxcev1.brevlab.com/api/v1/field-twin");
    let data2 = await response2.json();
    let first = data2.field_twin.competitors[0];

    document.getElementById("gap-leader").textContent = first.gap_to_leader;
    document.getElementById("strategy").textContent = first.predicted_strategy;
    document.getElementById("pitProbability").textContent = first.pit_probability.toFixed(3);

  } catch (error) {
    console.error("Failed to fetch car data:", error);
  }
}

updateCarData();
setInterval(updateCarData, 500);





// ============================================
// INITIALIZATION
// ============================================
let modalManager, driverManager, aiSystem, car3D, track3D;

document.addEventListener('DOMContentLoaded', () => {
  // Initialize all systems
  modalManager = new ModalManager();
  driverManager = new DriverParameterManager();
  aiSystem = new AIRecommendationSystem();
  car3D = new Car3DVisualization();
  track3D = new Track3DVisualization();

  // Add loading animation
  document.body.classList.add('loaded');

  // console.log('F1 Race Engineer Dashboard initialized successfully');
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
  track3D
};