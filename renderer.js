// Electron window controls
// window.minimizeWindow = function() {
//   const { remote } = require("electron");
//   const window = remote.getCurrentWindow();
//   window.minimize();
// }

// window.closeWindow = function() {
//   const { remote } = require("electron");
//   const window = remote.getCurrentWindow();
//   window.close();
// }

// Panel resizing functionality
class PanelResizer {
  constructor() {
    this.panels = document.querySelectorAll(".panel")
    this.activePanel = null
    this.startX = 0
    this.startY = 0
    this.startWidth = 0
    this.startHeight = 0

    this.init()
  }

  init() {
    this.panels.forEach((panel) => {
      const resizeHandle = panel.querySelector(".resize-handle")
      const header = panel.querySelector(".panel-header")

      // Resize functionality
      if (resizeHandle) {
        resizeHandle.addEventListener("mousedown", (e) => this.startResize(e, panel))
      }

      // Drag functionality for panel headers
      if (header) {
        header.addEventListener("mousedown", (e) => {
          if (e.target === resizeHandle || resizeHandle.contains(e.target)) return
          this.startDrag(e, panel)
        })
      }
    })

    document.addEventListener("mousemove", (e) => this.onMouseMove(e))
    document.addEventListener("mouseup", () => this.stopResize())
  }

  startResize(e, panel) {
    e.preventDefault()
    e.stopPropagation()

    this.activePanel = panel
    this.startX = e.clientX
    this.startY = e.clientY
    this.startWidth = panel.offsetWidth
    this.startHeight = panel.offsetHeight

    panel.classList.add("resizing")
    document.body.style.cursor = "nwse-resize"
  }

  startDrag(e, panel) {
    // Note: Full drag implementation would require converting from grid to absolute positioning
    // This is a simplified version that shows the concept
    panel.classList.add("dragging")
  }

  onMouseMove(e) {
    if (!this.activePanel) return

    const deltaX = e.clientX - this.startX
    const deltaY = e.clientY - this.startY

    const newWidth = Math.max(200, this.startWidth + deltaX)
    const newHeight = Math.max(150, this.startHeight + deltaY)

    this.activePanel.style.width = `${newWidth}px`
    this.activePanel.style.height = `${newHeight}px`
    this.activePanel.style.minWidth = `${newWidth}px`
    this.activePanel.style.minHeight = `${newHeight}px`
  }

  stopResize() {
    if (this.activePanel) {
      this.activePanel.classList.remove("resizing")
      this.activePanel.classList.remove("dragging")
      this.activePanel = null
      document.body.style.cursor = "default"
    }
  }
}

// Initialize panel resizer
const resizer = new PanelResizer()


// ============================================
// 3D VISUALIZATION INTEGRATION POINTS
// ============================================

// Panel 2: F1 Car 3D Model
// Import Three.js library
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

console.log('Three.js loaded:', THREE);
console.log('GLTFLoader loaded:', GLTFLoader);



function initCar3D() {
  
  const canvas = document.getElementById('car-3d-canvas');
  
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setClearColor(0x000000, 0); // Transparent background
  
  
  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(5, 5, 5);
  scene.add(directionalLight);
  
  
  // Load F1 car model
  const loader = new GLTFLoader();

  loader.load('./assets/models/scene.gltf', 
    (gltf) => {
      const car = gltf.scene;
      
      // Scale the car
      car.scale.set(1.5, 1.5, 1.5);
      
      // Center the car by calculating its bounding box
      const box = new THREE.Box3().setFromObject(car);
      const center = box.getCenter(new THREE.Vector3());
      car.position.sub(center);
      
      scene.add(car);
      
      // Auto-rotate animation
      function animate() {
        requestAnimationFrame(animate);
        car.rotation.y += 0.01;
        renderer.render(scene, camera);
      }
      animate();
    });
  
  camera.position.z = 6;
  camera.position.x = -1;
  camera.position.y = 1;
  
  // Optional: Add OrbitControls for manual rotation
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
}

// Call when ready
initCar3D();

// Panel 4: Track Digital Twin with Animated Cars
// Uncomment and implement when adding track visualization
/*
function initTrack3D() {
  const canvas = document.getElementById('track-3d-canvas');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setClearColor(0x000000, 0);
  
  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);
  
  // Load track model
  const loader = new GLTFLoader();
  loader.load('assets/models/f1-track.glb', (gltf) => {
    const track = gltf.scene;
    scene.add(track);
  });
  
  // Create animated cars
  const cars = [];
  const carGeometry = new THREE.BoxGeometry(0.2, 0.1, 0.4);
  const carMaterials = [
    new THREE.MeshStandardMaterial({ color: 0xff0000 }),
    new THREE.MeshStandardMaterial({ color: 0x0000ff }),
    new THREE.MeshStandardMaterial({ color: 0x00ff00 })
  ];
  
  for (let i = 0; i < 3; i++) {
    const car = new THREE.Mesh(carGeometry, carMaterials[i]);
    cars.push({
      mesh: car,
      progress: i * 0.33, // Stagger starting positions
      speed: 0.005 + Math.random() * 0.003
    });
    scene.add(car);
  }
  
  // Define track path (simplified circular path)
  function getTrackPosition(progress) {
    const angle = progress * Math.PI * 2;
    const radius = 3;
    return {
      x: Math.cos(angle) * radius,
      z: Math.sin(angle) * radius,
      rotation: angle + Math.PI / 2
    };
  }
  
  // Animation loop
  function animate() {
    requestAnimationFrame(animate);
    
    // Update car positions along track
    cars.forEach(carData => {
      carData.progress = (carData.progress + carData.speed) % 1;
      const pos = getTrackPosition(carData.progress);
      carData.mesh.position.x = pos.x;
      carData.mesh.position.z = pos.z;
      carData.mesh.rotation.y = pos.rotation;
    });
    
    renderer.render(scene, camera);
  }
  
  camera.position.set(0, 5, 8);
  camera.lookAt(0, 0, 0);
  
  animate();
}

// Call when ready
// initTrack3D();
*/

// ============================================
// DYNAMIC DATA UPDATES
// ============================================

// Simulate real-time data updates
function updateCarData() {
  const speedElement = document.getElementById("speed")
  const rpmElement = document.getElementById("rpm")
  const fuelElement = document.getElementById("fuel")

  setInterval(() => {
    // Simulate changing values
    const speed = 300 + Math.floor(Math.random() * 50)
    const rpm = 17000 + Math.floor(Math.random() * 2000)
    const temp = 90 + Math.floor(Math.random() * 10)
    const fuelPercent = 75 + Math.floor(Math.random() * 10)
    const fuelLiters = Math.floor((fuelPercent / 100) * 60)

    speedElement.textContent = `${speed} km/h`
    rpmElement.innerHTML = `${rpm.toLocaleString()} <span class="temp">(temp ${temp}°C)</span>`
    fuelElement.innerHTML = `${fuelPercent}% <span class="temp">(${fuelLiters}/60L)</span>`
  }, 2000)
}

// Start data updates
updateCarData()

// Handle window resize
window.addEventListener("resize", () => {
  // Recalculate canvas sizes if 3D is implemented
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  camera.aspect = canvas.clientWidth / canvas.clientHeight;
  camera.updateProjectionMatrix();
})

// console.log("[v0] F1 Dashboard initialized")
// console.log("[v0] Panel resizing enabled - drag resize handles to adjust panel sizes")
// console.log("[v0] 3D integration points ready - see comments in renderer.js for Three.js implementation")