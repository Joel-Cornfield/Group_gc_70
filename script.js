const map = document.getElementById('guess-map');
const guessImage = document.getElementById('guess-image');
const mapContent = document.getElementById('guess-map-content');
const feedback = document.getElementById('guess-feedback');

let zoom = 0.5;
let offsetX = 0;
let offsetY = 0;
const minZoom = 0.5;
const maxZoom = 3;
let isDragging = false;
let startX, startY;
let lastPin = null;
let guessX = 0;
let guessY = 0;

const img = new Image();
img.src = 'images/UWA_map.jpg';
img.onload = () => {
  mapContent.style.width = `${img.width}px`;
  mapContent.style.height = `${img.height}px`;
  updateTransform();
};

// Load random location from locations.json
document.addEventListener('DOMContentLoaded', () => {
  fetch('locations.json')
    .then((response) => response.json())
    .then((locations) => {
      const randomLocation = locations[Math.floor(Math.random() * locations.length)];
      guessImage.src = `images/${randomLocation.name.split(' ').join('_')}.jpg`;
      console.log(`Loaded location: ${randomLocation.name}`);
    })
    .catch((error) => console.error('Error loading locations:', error));
});




function updateTransform() {
  mapContent.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${zoom})`;
}

map.addEventListener('wheel', function (e) {
  e.preventDefault();
  const rect = map.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  const prevZoom = zoom;
  const delta = e.deltaY > 0 ? -0.1 : 0.1;
  zoom = Math.min(maxZoom, Math.max(minZoom, zoom + delta));
  const zoomRatio = zoom / prevZoom;
  offsetX -= (mouseX - offsetX) * (zoomRatio - 1);
  offsetY -= (mouseY - offsetY) * (zoomRatio - 1);
  updateTransform();
});

map.addEventListener('mousedown', (e) => {
  isDragging = true;
  startX = e.clientX - offsetX;
  startY = e.clientY - offsetY;
  map.style.cursor = 'grabbing';
});

map.addEventListener('mouseup', () => {
  isDragging = false;
  map.style.cursor = 'grab';
});

map.addEventListener('mouseleave', () => {
  isDragging = false;
  map.style.cursor = 'grab';
});

map.addEventListener('mousemove', (e) => {
  if (isDragging) {
    offsetX = e.clientX - startX;
    offsetY = e.clientY - startY;
    updateTransform();
  }
});

let lastTouchDistance = null;

map.addEventListener('touchstart', (e) => {
  if (e.touches.length === 2) {
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    lastTouchDistance = Math.sqrt(dx * dx + dy * dy);
  } else if (e.touches.length === 1) {
    startX = e.touches[0].clientX - offsetX;
    startY = e.touches[0].clientY - offsetY;
  }
});

map.addEventListener('touchmove', (e) => {
  e.preventDefault();
  if (e.touches.length === 2) {
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    const newDistance = Math.sqrt(dx * dx + dy * dy);
    if (lastTouchDistance) {
      const zoomDelta = (newDistance - lastTouchDistance) / 200;
      const prevZoom = zoom;
      zoom = Math.min(maxZoom, Math.max(minZoom, zoom + zoomDelta));
      const zoomRatio = zoom / prevZoom;
      const rect = map.getBoundingClientRect();
      const centerX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
      const centerY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;
      offsetX -= (centerX - offsetX) * (zoomRatio - 1);
      offsetY -= (centerY - offsetY) * (zoomRatio - 1);
      updateTransform();
    }
    lastTouchDistance = newDistance;
  } else if (e.touches.length === 1 && isDragging) {
    offsetX = e.touches[0].clientX - startX;
    offsetY = e.touches[0].clientY - startY;
    updateTransform();
  }
}, { passive: false });

map.addEventListener('click', function (e) {
  const rect = map.getBoundingClientRect();
  let tempX = (e.clientX - rect.left - offsetX) / zoom;
  let tempY = (e.clientY - rect.top - offsetY) / zoom;
  if ((tempX > 0) && (tempX < 1000) && (tempY > 0) && (tempY < 1400)) {     
    guessX = tempX;
    guessY = tempY;

    console.log(`Guess coordinates: x=${guessX}, y=${guessY}`);

    if (lastPin) lastPin.remove();

    const pin = document.createElement('div');
    pin.classList.add('pin');
    pin.style.left = `${guessX}px`;
    pin.style.top = `${guessY}px`;
    pin.textContent = '📍';
    mapContent.appendChild(pin);
    lastPin = pin;

    feedback.classList.add('show');
    setTimeout(() => feedback.classList.remove('show'), 600);
  } 
});

document.getElementById('submitGuess').addEventListener('click', () => {
  alert("Guess submitted! (dummy function) \nCoordinates: " + `x=${guessX}, y=${guessY}`);
});