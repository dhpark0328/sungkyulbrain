const DEFAULT_CENTER = [window.BLACKICE_BOOTSTRAP.schoolLat, window.BLACKICE_BOOTSTRAP.schoolLon];
const DEFAULT_ZOOM = 16;

const map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const markers = new Map();
let nodeCache = [];
let selectedDeviceId = null;

function badge(status) {
  return `<span class="badge ${status || 'safe'}">${status || 'unknown'}</span>`;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function statusColor(status) {
  if (status === 'danger') return '#dc2626';
  if (status === 'caution') return '#f59e0b';
  return '#16a34a';
}

function goToSchool() {
  map.setView(DEFAULT_CENTER, DEFAULT_ZOOM, { animate: true });
}

function fitAllNodes() {
  if (!nodeCache.length) {
    goToSchool();
    return;
  }
  const bounds = L.latLngBounds(nodeCache.map((node) => [node.latitude, node.longitude]));
  bounds.extend(DEFAULT_CENTER);
  map.fitBounds(bounds.pad(0.2), { animate: true });
}

function updateSummary(nodes) {
  const counts = { safe: 0, caution: 0, danger: 0 };
  nodes.forEach((node) => {
    const key = ['safe', 'caution', 'danger'].includes(node.road_status) ? node.road_status : 'safe';
    counts[key] += 1;
  });
  document.getElementById('node-count').textContent = `${nodes.length}개`;
  document.getElementById('node-summary').innerHTML = `
    <div class="summary-box safe"><div class="summary-label">안전</div><div class="summary-value">${counts.safe}</div></div>
    <div class="summary-box caution"><div class="summary-label">주의</div><div class="summary-value">${counts.caution}</div></div>
    <div class="summary-box danger"><div class="summary-label">위험</div><div class="summary-value">${counts.danger}</div></div>
  `;
}

function renderNodeList(nodes) {
  const list = document.getElementById('node-list');
  list.innerHTML = nodes.map((node) => `
    <button class="node-list-item ${selectedDeviceId === node.device_id ? 'active' : ''}" data-device-id="${escapeHtml(node.device_id)}">
      <div class="node-list-top">
        <strong>${escapeHtml(node.device_id)}</strong>
        ${badge(node.road_status)}
      </div>
      <div class="node-list-name">${escapeHtml(node.name || '학교 주변 노드')}</div>
      <div class="node-list-actions">
        <span>${Number(node.latitude).toFixed(4)}, ${Number(node.longitude).toFixed(4)}</span>
        <span class="link-like">지도에서 보기</span>
      </div>
    </button>
  `).join('');

  list.querySelectorAll('.node-list-item').forEach((button) => {
    button.addEventListener('click', () => {
      const { deviceId } = button.dataset;
      focusNode(deviceId);
      loadNodeDetail(deviceId);
    });
  });
}

function focusNode(deviceId) {
  const node = nodeCache.find((item) => item.device_id === deviceId);
  const marker = markers.get(deviceId);
  if (node) {
    map.setView([node.latitude, node.longitude], 17, { animate: true });
  }
  if (marker) {
    marker.openPopup();
  }
  selectedDeviceId = deviceId;
  renderNodeList(nodeCache);
}

async function loadNodes() {
  const res = await fetch('/api/map/nodes');
  const data = await res.json();
  nodeCache = data.nodes || [];

  nodeCache.forEach((node) => {
    let marker = markers.get(node.device_id);
    if (!marker) {
      marker = L.circleMarker([node.latitude, node.longitude], {
        radius: 10,
        color: '#ffffff',
        weight: 2,
        fillColor: statusColor(node.road_status),
        fillOpacity: 0.95,
      }).addTo(map);
      markers.set(node.device_id, marker);
    } else {
      marker.setLatLng([node.latitude, node.longitude]);
      marker.setStyle({ fillColor: statusColor(node.road_status) });
    }
    
    if (selectedDeviceId !== node.device_id) {
        marker.bindPopup(`
          <div class="map-popup">
            <strong>${escapeHtml(node.name || node.device_id)}</strong><br>
            ID: ${escapeHtml(node.device_id)}<br>
            ${badge(node.road_status)}
          </div>
        `);
    }

    marker.off('click');
    marker.on('click', () => {
      selectedDeviceId = node.device_id;
      renderNodeList(nodeCache);
      loadNodeDetail(node.device_id);
    });
  });

  updateSummary(nodeCache);
  renderNodeList(nodeCache);

  if (selectedDeviceId) {
    loadNodeDetail(selectedDeviceId);
  } else if (nodeCache.length) {
    selectedDeviceId = nodeCache[0].device_id;
    loadNodeDetail(selectedDeviceId);
  }
}

async function loadNodeDetail(deviceId) {
  // web.py가 로컬 위치 데이터와 AWS 측정 데이터를 결합해 주므로 기존 API 경로를 유지합니다.
  const res = await fetch(`/api/map/node/${deviceId}`); 
  const node = await res.json();
  
  if (node.error) return; 

  selectedDeviceId = deviceId;
  renderNodeList(nodeCache);
  
  // 우측 패널 상세 정보 업데이트
  const detailContainer = document.getElementById('node-detail');
  if (detailContainer) {
      detailContainer.innerHTML = `
        <div class="detail-head">
          <div>
            <div class="detail-id">${escapeHtml(node.device_id)}</div>
            <div class="detail-name">${escapeHtml(node.name || '학교 주변 노드')}</div>
          </div>
          ${badge(node.road_status)}
        </div>
        <div class="item">측정시간: ${escapeHtml(node.measured_at || '-')}</div>
        <div class="item">온도: ${node.temperature_c ?? '-'} °C</div>
        <div class="item">습도: ${node.humidity_pct ?? '-'} %</div>
        <div class="item">주파수: ${node.conductivity ?? '-'}</div>
        <div class="item">위험 점수: ${node.risk_score ?? '-'} / 100</div>
        <div class="item">위치: ${Number(node.latitude).toFixed(5)}, ${Number(node.longitude).toFixed(5)}</div>
        <div class="item">판단 사유: ${escapeHtml(node.reason || '-')}</div>
      `;
  }

  // 클릭 시 나타나는 지도 팝업 내용 업데이트
  const marker = markers.get(deviceId);
  if (marker) {
      marker.setPopupContent(`
        <div class="map-popup" style="min-width: 180px; padding: 5px;">
          <strong style="font-size: 1.1em;">${escapeHtml(node.name || '학교 주변 노드')}</strong><br>
          <span style="font-size: 0.85em; color: gray;">ID: ${escapeHtml(node.device_id)}</span><br>
          <div style="margin: 8px 0;">${badge(node.road_status)}</div>
          <hr style="margin: 8px 0; border: none; border-top: 1px solid #ccc;">
          <div style="font-size: 0.95em; line-height: 1.6;">
            <strong>측정시간:</strong> ${escapeHtml(node.measured_at || '-')} <br>
            <strong>온도:</strong> ${node.temperature_c ?? '-'} °C<br>
            <strong>습도:</strong> ${node.humidity_pct ?? '-'} %<br>
            <strong>주파수:</strong> ${node.conductivity ?? '-'}
          </div>
        </div>
      `);
  }
}

async function loadRecent() {
  const res = await fetch('/api/readings/recent?limit=10');
  const data = await res.json();
  
  if (!data.items) return;

  document.getElementById('recent-list').innerHTML = data.items.map((item) => `
    <div class="item recent-item" data-device-id="${escapeHtml(item.device_id)}">
      <div><strong>${escapeHtml(item.device_id)}</strong> ${badge(item.road_status)}</div>
      <div>${escapeHtml(item.measured_at)}</div>
      <div>${item.temperature_c} °C / ${item.humidity_pct} % / ${item.conductivity ?? item.frequency_hz}</div>
    </div>
  `).join('');

  document.querySelectorAll('.recent-item').forEach((item) => {
    item.addEventListener('click', () => {
      const { deviceId } = item.dataset;
      focusNode(deviceId);
      loadNodeDetail(deviceId);
    });
  });
}

async function refresh() {
  await loadNodes();
  await loadRecent();
}

document.getElementById('reset-view-btn').addEventListener('click', goToSchool);
document.getElementById('fit-nodes-btn').addEventListener('click', fitAllNodes);

refresh();
setInterval(refresh, 5000);