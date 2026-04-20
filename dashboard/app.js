const API_URL = '/data';
//const API_URL = 'https://tzkfzt5af6.execute-api.us-east-1.amazonaws.com/prod/data';

// Chart Setup
const maxPoints = 20;

function makeChart(id, label, color) {
  const ctx = document.getElementById(id).getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: label,
        data: [],
        borderColor: color,
        backgroundColor: color + '22',
        borderWidth: 2,
        pointRadius: 3,
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: '#555', maxTicksLimit: 6 },
          grid: { color: '#2a2d3e' }
        },
        y: {
          ticks: { color: '#555' },
          grid: { color: '#2a2d3e' }
        }
      }
    }
  });
}

const charts = {
  vibration: makeChart('chartVibration', 'Vibration G', '#ff4444'),
  tilt:      makeChart('chartTilt',      'Tilt Deg',    '#ffaa00'),
  sound:     makeChart('chartSound',     'Sound dB',    '#00aaff'),
  battery:   makeChart('chartBattery',   'Battery %',   '#00ff88'),
};

function addPoint(chart, label, value) {
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  if (chart.data.labels.length > maxPoints) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}

// Fetch data from API Gateway
async function fetchData() {
  try {
    const response = await fetch(API_URL + '?t=' + Date.now());
    const data = await response.json();
    return data.items || [];
  } catch(e) {
    console.error('Fetch error:', e);
    return [];
  }
}

// Update dashboard with latest data
function updateDashboard(items) {
  if (!items.length) return;

  // Sort oldest first so charts build left to right
  items.sort((a, b) => {
    const ta = a.timestamp || '';
    const tb = b.timestamp || '';
    return ta.localeCompare(tb);
  });

  const latest = {};
  const events = [];
  let theftDetected = false;

  // Group by sensor type
  const byType = {};
  items.forEach(item => {
    const type = item.sensorType;
    if (!byType[type]) byType[type] = [];
    byType[type].push(item);
  });

  // Update charts for each sensor type
  if (byType.vibration) {
    byType.vibration.forEach(item => {
      const raw = JSON.parse(item.rawData || '{}');
      const date = new Date(item.timestamp);
      const time = date.toLocaleTimeString('en-IE', {timeZone: 'Europe/Dublin'});
      addPoint(charts.vibration, time, parseFloat(raw.vibration_g));
    });
    const last = byType.vibration[byType.vibration.length - 1];
    const raw = JSON.parse(last.rawData || '{}');
    document.getElementById('valVibration').textContent = (raw.vibration_g || '--') + ' G';
    document.getElementById('cardVibration').className =
      'status-card ' + (last.alertLevel === 'CRITICAL' ? 'alert' : 'good');
    latest.vibration = last;
  }

  if (byType.tilt) {
    byType.tilt.forEach(item => {
      const raw = JSON.parse(item.rawData || '{}');
      const date = new Date(item.timestamp);
      const time = date.toLocaleTimeString('en-IE', {timeZone: 'Europe/Dublin'});
      addPoint(charts.tilt, time, parseFloat(raw.angle_deg));
    });
    const last = byType.tilt[byType.tilt.length - 1];
    const raw = JSON.parse(last.rawData || '{}');
    document.getElementById('valTilt').textContent = (raw.angle_deg || '--') + '°';
    document.getElementById('cardTilt').className =
      'status-card ' + (last.alertLevel === 'CRITICAL' ? 'alert' : 'good');
    latest.tilt = last;
  }

  if (byType.sound) {
    byType.sound.forEach(item => {
      const raw = JSON.parse(item.rawData || '{}');
      const date = new Date(item.timestamp);
      const time = date.toLocaleTimeString('en-IE', {timeZone: 'Europe/Dublin'});
      addPoint(charts.sound, time, parseFloat(raw.decibels));
    });
    const last = byType.sound[byType.sound.length - 1];
    const raw = JSON.parse(last.rawData || '{}');
    document.getElementById('valSound').textContent = (raw.decibels || '--') + ' dB';
    document.getElementById('cardSound').className =
      'status-card ' + (last.alertLevel === 'CRITICAL' ? 'alert' : 'good');
    latest.sound = last;
  }

  if (byType.battery) {
    byType.battery.forEach(item => {
      const raw = JSON.parse(item.rawData || '{}');
      const date = new Date(item.timestamp);
      const time = date.toLocaleTimeString('en-IE', {timeZone: 'Europe/Dublin'});
      addPoint(charts.battery, time, parseFloat(raw.battery_percent));
    });
    const last = byType.battery[byType.battery.length - 1];
    const raw = JSON.parse(last.rawData || '{}');
    document.getElementById('valBattery').textContent = (raw.battery_percent || '--') + '%';
    document.getElementById('cardBattery').className =
      'status-card ' + (last.alertLevel === 'CRITICAL' ? 'alert' : 'good');
    latest.battery = last;
  }

  if (byType.gps) {
    const last = byType.gps[byType.gps.length - 1];
    const raw = JSON.parse(last.rawData || '{}');
    document.getElementById('valGps').textContent = raw.status || '--';
    document.getElementById('cardGps').className =
      'status-card ' + (raw.status === 'MOVING' ? 'alert' : 'good');
    latest.gps = last;
  }

  // Check for theft
  items.forEach(item => {
    if (item.alertLevel === 'CRITICAL') theftDetected = true;
  });

  // Theft alert banner
  document.getElementById('alertBanner').style.display =
    theftDetected ? 'block' : 'none';

  // Events log — newest first
  const sortedEvents = [...items].reverse().slice(0, 8);
  const logEl = document.getElementById('eventLog');
  logEl.innerHTML = sortedEvents.map(e => {
    const cls = e.alertLevel === 'CRITICAL' ? 'theft-item' : 'normal-item';
    const icon = e.alertLevel === 'CRITICAL' ? '🚨' : '✅';
    const date = new Date(e.timestamp);
    const time = date.toLocaleTimeString('en-IE', {timeZone: 'Europe/Dublin'});
    return `<div class="${cls}">
      ${icon} <strong>${e.sensorType}</strong> —
      ${e.alertLevel} — ${time}
    </div>`;
  }).join('');

  // Last updated
  document.getElementById('lastUpdate').textContent =
    new Date().toLocaleTimeString('en-IE', {timeZone: 'Europe/Dublin'});
}

// Main loop — refresh every 10 seconds
async function refresh() {
  // Clear all charts before redrawing
  Object.values(charts).forEach(chart => {
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.update();
  });
  const items = await fetchData();
  updateDashboard(items);
}

refresh();
setInterval(refresh, 10000);