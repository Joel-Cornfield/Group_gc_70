(() => {
  const labels = gameData.map((g, i) => `Game ${i + 1}`);
  const durations = gameData.map(g => g.duration);
  const pointColors = gameData.map(g => g.correct ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)');

  new Chart(document.getElementById('guessTimeChart'), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Guess duration (s)',
        data: durations,
        borderColor: 'rgba(54, 162, 235, 0.6)',
        backgroundColor: 'rgba(54, 162, 235, 0.1)',
        fill: true,
        pointBackgroundColor: pointColors,
        pointBorderColor: pointColors,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.2
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Seconds'
          }
        }
      },
      plugins: {
        legend: {
          display: true
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const isCorrect = gameData[context.dataIndex].correct;
              return `${context.dataset.label}: ${context.parsed.y}s (${isCorrect ? "Correct" : "Wrong"})`;
            }
          }
        }
      }
    }
  });
})();
