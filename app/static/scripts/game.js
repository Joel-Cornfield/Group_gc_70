// DOM Elements
const map = document.getElementById('guess-map');
const mapContent = document.getElementById('guess-map-content');
const feedback = document.getElementById('guess-feedback');
const timerElement = document.getElementById('timer');
const guessImage = document.getElementById('guess-image');
const revealButton = document.getElementById('reveal-button');
const hintText = document.getElementById('hint-text');
const hintSquares = [document.getElementById('guess-1'), document.getElementById('guess-2'), document.getElementById('guess-3')];
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
let gameId = null;
let secondsElapsed = 0;
let timerInterval = null;

// Functions

// Initialize Map Background
const img = new Image();
img.src = 'static/images/UWA_map.jpg';
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
    timerElement.textContent = formatTime(secondsElapsed);
  }, 1000);
}

// Reset the timer
function resetTimer() {
  clearInterval(timerInterval);
  secondsElapsed = 0;
  timerElement.textContent = '0:00';
}

function initializeMap(image) {
  mapContent.style.width = `${image.width}px`;
  mapContent.style.height = `${image.height}px`;
  mapContent.style.backgroundImage = `url('${image.src}')`;
  mapContent.style.backgroundSize = 'contain';
  mapContent.style.backgroundRepeat = 'no-repeat';
  updateTransform();
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

function getFeedback(distance) {
  if (distance < 25) return 'Got it!';
  if (distance < 50) return 'Hot';
  if (distance < 125) return 'Warm';
  return 'Cold';
}

// Fetch game state from the /play route
function fetchGameState() {
  fetch('/play')
    .then((response) => response.json())
    .then((data) => {
      // Update game state
      gameId = data.game_id;
      guessImage.src = data.guess_image;
      guessImage.classList.remove('hidden');
      revealButton.classList.add('hidden');

      // Reset timer
      resetTimer();
      startTimer();

      console.log('Game state loaded:', data);
    })
    .catch((error) => console.error('Error fetching game state:', error));
}

// Submit a guess to the /guess route
function submitGuess() {
  let guess_coords = imageCoordsToLatLng(guessX, guessY);
  const guessData = {
    game_id: gameId,
    guessed_latitude: guess_coords.lat,
    guessed_longitude: guess_coords.lng
  };

  fetch('/guess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(guessData)
  })
    .then((response) => response.json())
    .then((data) => {
      console.log('Guess response:', data);
      
      // Ensure guesses exist in the response
      if (!data.guesses || data.guesses.length === 0) {
        console.error('No guesses returned from the server.');
        return;
      }

      // Get the last guess
      const lastGuess = data.guesses[data.guesses.length - 1];
      const feedback = getFeedback(lastGuess.distance_error_meters);
      hintText.textContent = feedback;

      // Update guess squares
      const guesses = data.guesses.length;
      for (let i = 0; i < hintSquares.length; i++) {
        if (i < guesses) {
          if (feedback === 'Got it!') {
            hintSquares[i].textContent = '🟩';
          } else if (feedback === 'Hot') {
            hintSquares[i].textContent = '🟥';
          } else if (feedback === 'Warm') {
            hintSquares[i].textContent = '🟨';
          } else {
            hintSquares[i].textContent = '🟦';
          }
        }
      }

      // End game if necessary
      if (feedback === 'Got it!' || guesses >= 3) {
        endGame();
      }
    })
    .catch((error) => console.error('Error submitting guess:', error));
}

// End the game
function endGame() {
  submitButton.disabled = true;
  if (hintText.textContent !== 'Got it!') {
    hintText.textContent = 'Game Over!';
  }
  clearInterval(timerInterval); // Stop the timer

  // Dynamically create the "Start New Game" button
  const newGameButton = document.createElement('button');
  newGameButton.classList.add('btn', 'btn-success', 'mx-2');
  newGameButton.id = 'newGameButton';
  newGameButton.textContent = 'Start New Game';

  // Add click event listener to start a new game
  newGameButton.addEventListener('click', () => {
    resetGame();
    fetchGameState();
  });

  // Append the button next to the "Submit Guess" button
  submitButton.parentElement.appendChild(newGameButton);
}

// Reset the game state
function resetGame() {
  // Reset guess squares
  hintSquares.forEach((square) => {
    square.textContent = '⬛';
  });

  // Reset hint text
  hintText.textContent = 'Make your first guess to get a hint';

  // Enable the "Submit Guess" button
  submitButton.disabled = false;

  // Remove the "Start New Game" button if it exists
  const newGameButton = document.getElementById('newGameButton');
  if (newGameButton) {
    newGameButton.remove();
  }

  // Reset the timer
  resetTimer();
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
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

  revealButton.addEventListener('click', fetchGameState);
  submitButton.addEventListener('click', submitGuess);
});