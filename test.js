fetch("/test/test")
  .then(res => res.json())
  .then(data => {
    const tireDegradationRate = data?.car_twin?.predictions?.tire_degradation_rate ?? 0;
    const performanceDelta = data?.car_twin?.predictions?.performance_delta ?? 0;
    const optimalPitWindow = data?.car_twin?.strategy_metrics?.optimal_pit_window ?? [];
    const predictedPitLap = data?.car_twin?.predictions?.predicted_pit_lap ?? 0;

    // Insert into HTML
    document.getElementById("tireRate").textContent = tireDegradationRate.toFixed(6);
    document.getElementById("performanceDelta").textContent = performanceDelta.toFixed(3);
    document.getElementById("pitWindow").textContent = optimalPitWindow.join(" - ");
    document.getElementById("pitLap").textContent = predictedPitLap;
  })
  .catch(err => {
    console.error("Error fetching data:", err);
    document.body.innerHTML += `<p style="color:red;">Failed to load data.</p>`;
  });