from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import joblib
import os
import numpy as np

app = FastAPI(title="Antarctica Ice Edge Visualizer")


MODEL_PATH = 'rf_ice_model.joblib'
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    if hasattr(model, 'n_jobs'):
        model.n_jobs = 1
    print("Model załadowany!")
else:
    model = None


@app.get("/predict_all")
def predict_all(day: int):
    if model is None: return {"error": "Brak modelu"}
    
    angles = list(range(0, 361, 5)) # co 5 stopni dla szybkości
    input_data = np.array([[day, a] for a in angles])
    preds = model.predict(input_data)
    
    return {
        "angles": angles,
        "lats": [float(p) for p in preds]
    }

# (html na szybko najprostszy zalezy mi na dzialaniu)
@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Antarktyda Ice Tracker</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: white; text-align: center; }
            .container { max-width: 800px; margin: auto; padding: 20px; }
            .card { background: #16213e; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
            input[type=range] { width: 80%; margin: 20px 0; }
            .stats { display: flex; justify-content: space-around; margin-top: 20px; font-weight: bold; color: #4ecca3; }
            canvas { background: #1a1a2e; border-radius: 50%; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>❄️ Antarctica Ice Visualizer</h1>
                <p>Przesuń suwak, aby zmienić dzień roku:</p>
                <input type="range" id="daySlider" min="1" max="365" value="150" oninput="updateChart()">
                <div class="stats">
                    <span>DZIEŃ ROKU: <span id="dayVal">150</span></span>
                </div>
                <div style="width: 100%;"><canvas id="iceChart"></canvas></div>
            </div>
        </div>

        <script>
            let chart;
            async function updateChart() {
                const day = document.getElementById('daySlider').value;
                document.getElementById('dayVal').innerText = day;
                
                const response = await fetch(`/predict_all?day=${day}`);
                const data = await response.json();
                
                const chartData = {
                    labels: data.angles,
                    datasets: [{
                        label: 'Granica Lodu (Szerokość geograficzna)',
                        data: data.lats,
                        fill: true,
                        backgroundColor: 'rgba(78, 204, 163, 0.2)',
                        borderColor: '#4ecca3',
                        pointRadius: 0
                    }]
                };

                if (chart) { chart.destroy(); }
                
                const ctx = document.getElementById('iceChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'polarArea',
                    data: chartData,
                    options: {
                        scales: {
                            r: {
                                min: -90,
                                max: -50,
                                ticks: { display: false }
                            }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            }
            updateChart();
        </script>
    </body>
    </html>
    """