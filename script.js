// DOM Elements
const map = document.getElementById('guess-map');
const guessImage = document.getElementById('guess-image');
const mapContent = document.getElementById('guess-map-content');
const feedback = document.getElementById('guess-feedback');
const hint_squares = [document.getElementById("guess-1"), document.getElementById("guess-2"), document.getElementById("guess-3")];
const hint_text = document.getElementById("hint-text");
const revealButton = document.getElementById('reveal-button');
const timerElement = document.getElementById('timer');
const submitButton = document.getElementById('submitGuess');


// State Variables
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
let answerLat = 0;
let answerLong = 0;
let guesses = 0;
let timerInterval;
let secondsElapsed = 0;

// Functions

// Initialize Map Background
const img = new Image();
img.src = 'images/UWA_map.jpg';
img.onload = () => {
  initializeMap(img);
};

// Convert image coordinates to latitude and longitude
function imageCoordsToLatLng(x, y) {
  // Known reference coordinates
  const latTop = -31.973510;
  const lngLeft = 115.812859;
  const latBottom = -31.98694544764;
  const lngRight = 115.8239020763047;

  // Image dimensions
  const imgWidth = 1000;
  const imgHeight = 1400;

  // Linear interpolation
  const lat = latTop + (y / imgHeight) * (latBottom - latTop);
  const lng = lngLeft + (x / imgWidth) * (lngRight - lngLeft);

  return { lat, lng };
}

// Format time as MM:SS
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const secondsLeft = seconds % 60;
  return `${minutes.toString().padStart(1, '0')}:${secondsLeft.toString().padStart(2, '0')}`;
}

function startTimer() {
  timerInterval = setInterval(() => {
    secondsElapsed++;
    timerElement.textContent = `${formatTime(secondsElapsed)}`;
  }, 1000);
}

// Calculates Haversine (direct) distance between two lat/lng points
function haversineDistance(lat1, lon1, lat2, lon2) {
  const toRad = (x) => x * Math.PI / 180;

  const R = 6371000; // Earth radius in meters
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);

  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

// Returns score based on the distance from the target location
function getGuessHint(guessX, guessY, targetLat, targetLng) {
  const { lat: guessLat, lng: guessLng } = imageCoordsToLatLng(guessX, guessY);

  // Calculate the distance
  const distance = haversineDistance(guessLat, guessLng, targetLat, targetLng);
  console.log(`Distance: ${distance} meters`);

  // Return hint based on distance
  if (distance <= 25) return "Got it!";
  if (distance <= 75) return "Hot";
  if (distance <= 125) return "Warm";
  return "Cold";
}


function initializeMap(image) {
  mapContent.style.width = `${image.width}px`;
  mapContent.style.height = `${image.height}px`;
  mapContent.style.backgroundImage = `url('${image.src}')`;
  mapContent.style.backgroundSize = 'contain';
  mapContent.style.backgroundRepeat = 'no-repeat';
  updateTransform();
}

function loadRandomLocation() {
  fetch('locations.json')
    .then((response) => response.json())
    .then((locations) => {
      const randomLocation = locations[Math.floor(Math.random() * locations.length)];
      guessImage.src = `images/${randomLocation.name.split(' ').join('_')}.jpg`;
      console.log(`Loaded location: ${randomLocation.name}`);
      answerLat = randomLocation.latitude;
      answerLong = randomLocation.longitude;
    })
    .catch((error) => console.error('Error loading locations:', error));
}

function updateTransform() {
  // Constrain offsets to keep the map within bounds
  const mapRect = map.getBoundingClientRect();
  const contentWidth = mapContent.offsetWidth * zoom;
  const contentHeight = mapContent.offsetHeight * zoom;

  const minX = Math.min(0, mapRect.width - contentWidth);
  const maxX = 0;
  const minY = Math.min(0, mapRect.height - contentHeight);
  const maxY = 0;

  offsetX = Math.max(minX, Math.min(maxX, offsetX));
  offsetY = Math.max(minY, Math.min(maxY, offsetY));

  // Apply transform
  mapContent.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${zoom})`;

  // Update pin position
  if (lastPin) {
    lastPin.style.left = `${guessX}px`;
    lastPin.style.top = `${guessY}px`;
  }
}

function placePin(x, y) {
  if (lastPin) lastPin.remove();

  const pin = document.createElement('div');
  pin.classList.add('pin');
  pin.style.left = `${x}px`;
  pin.style.top = `${y}px`;
  pin.textContent = '📍';
  mapContent.appendChild(pin);
  lastPin = pin;

  feedback.classList.add('show');
  setTimeout(() => feedback.classList.remove('show'), 600);
}

function endGame() {
  map.style.pointerEvents = 'none';
  clearInterval(timerInterval); // Stop the timer
  submitButton.style.pointerEvents = 'none'; // Disable the button
  submitButton.style.opacity = '0.5'; // Dim the button
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  loadRandomLocation();
});

map.addEventListener('wheel', (e) => {
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

map.addEventListener('click', (e) => {
  const rect = map.getBoundingClientRect();
  const tempX = (e.clientX - rect.left - offsetX) / zoom;
  const tempY = (e.clientY - rect.top - offsetY) / zoom;
  if (tempX > 0 && tempX < 1000 && tempY > 0 && tempY < 1400) {
    guessX = tempX;
    guessY = tempY;
    console.log(`Guess coordinates: x=${guessX}, y=${guessY}`);
    placePin(guessX, guessY);
  }
});

document.getElementById('submitGuess').addEventListener('click', () => {
  let hint = getGuessHint(guessX, guessY, answerLat, answerLong);
  alert(`Guess submitted! (dummy function)\nCoordinates: x=${guessX}, y=${guessY}\nLat/Lng: ${JSON.stringify(imageCoordsToLatLng(guessX, guessY))}\nScore: ${hint}`);
  
  if (guesses < 3) {
    switch (hint) {
      case "Got it!":
        hint_squares[guesses].textContent = '🟩';
        endGame();
        break;
      case "Hot":
        hint_squares[guesses].textContent = '🟥';
        break;
      case "Warm":
        hint_squares[guesses].textContent = '🟧';
        break;
      case "Cold":
        hint_squares[guesses].textContent = '🟦';
        break;
    }
    hint_text.textContent = hint;
    guesses++;
    if (guesses >= 3) {
      endGame();
    }
  }
});

revealButton.addEventListener('click', () => {
  guessImage.classList.remove('hidden');
  guessImage.style.pointerEvents = 'auto'; // Enable interaction
  revealButton.classList.add('hidden'); // Hide the button
  startTimer(); // Start the timer
});
