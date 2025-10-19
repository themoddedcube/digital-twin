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

      if (resizeHandle) {
        resizeHandle.addEventListener("mousedown", (e) => this.startResize(e, panel))
      }

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

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

function initCar3D() {
  const canvas = document.getElementById('car-3d-canvas');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });

  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setClearColor(0x000000, 0);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(5, 5, 5);
  scene.add(directionalLight);

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

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
}

initCar3D();

function updateCarData() {
  const speedElement = document.getElementById("speed")
  const rpmElement = document.getElementById("rpm")
  const fuelElement = document.getElementById("fuel")

  setInterval(() => {
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

updateCarData()
