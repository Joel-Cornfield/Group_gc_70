<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
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
</script>
