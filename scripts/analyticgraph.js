// This script generates a line chart using Chart.js to visualize the total guess time for each round in a game.
  const allRounds = Array.from({ length: 120 }, (_, i) => `Round ${i + 1}`);
  const allGuessTimes = Array.from({ length: 120 }, () => Math.floor(Math.random() * 100));

  const maxPoints = 100;
  const labels = allRounds.slice(0, maxPoints);
  const data = allGuessTimes.slice(0, maxPoints);

  const ctx = document.getElementById('guessTimeChart').getContext('2d');
  const guessTimeChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total Guess Time (seconds)',
        data: data,
        backgroundColor: 'rgba(0, 123, 255, 0.1)',
        borderColor: '#007bff',
        borderWidth: 2,
        pointBackgroundColor: '#007bff',
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Seconds'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Rounds'
          }
        }
      }
    }
  });
