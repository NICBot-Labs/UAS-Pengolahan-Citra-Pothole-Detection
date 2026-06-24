function initReportMap() {
  const mapEl = document.getElementById("reportMap");
  if (!mapEl || typeof L === "undefined") return;

  const defaultCenter = [-6.2, 106.816666];
  const map = L.map(mapEl).setView(defaultCenter, 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  let marker = null;
  const roadNameInput = document.getElementById("roadName");
  const addressInput = document.getElementById("address");
  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");
  const selectedRoadText = document.getElementById("selectedRoadText");

  async function reverseGeocode(lat, lng) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`;
      const response = await fetch(url);
      const data = await response.json();
      const address = data.address || {};
      const road = address.road || address.neighbourhood || address.suburb || data.name || "Ruas jalan dipilih";
      roadNameInput.value = road;
      addressInput.value = data.display_name || road;
      selectedRoadText.textContent = `${road} (${Number(lat).toFixed(6)}, ${Number(lng).toFixed(6)})`;
    } catch (error) {
      roadNameInput.value = "Ruas jalan dipilih";
      selectedRoadText.textContent = `Ruas jalan dipilih (${Number(lat).toFixed(6)}, ${Number(lng).toFixed(6)})`;
    }
  }

  function chooseLocation(lat, lng) {
    latInput.value = lat;
    lngInput.value = lng;
    if (!marker) {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      marker.on("dragend", (event) => {
        const pos = event.target.getLatLng();
        chooseLocation(pos.lat, pos.lng);
      });
    } else {
      marker.setLatLng([lat, lng]);
    }
    map.setView([lat, lng], Math.max(map.getZoom(), 16));
    reverseGeocode(lat, lng);
  }

  map.on("click", (event) => chooseLocation(event.latlng.lat, event.latlng.lng));

  const locateBtn = document.getElementById("useMyLocation");
  locateBtn?.addEventListener("click", () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      chooseLocation(position.coords.latitude, position.coords.longitude);
    });
  });

  const searchInput = document.getElementById("roadSearch");
  searchInput?.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;
    const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(query)}&limit=1`;
    const response = await fetch(url);
    const results = await response.json();
    if (results.length) chooseLocation(Number(results[0].lat), Number(results[0].lon));
  });
}

function initDetailMap() {
  const mapEl = document.getElementById("detailMap");
  if (!mapEl || typeof L === "undefined") return;
  const lat = Number(mapEl.dataset.lat);
  const lng = Number(mapEl.dataset.lng);
  const road = mapEl.dataset.road || "Lokasi laporan";
  if (!lat || !lng) return;
  const map = L.map(mapEl).setView([lat, lng], 16);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  L.marker([lat, lng]).addTo(map).bindPopup(road).openPopup();
}

function initAdminMap() {
  const mapEl = document.getElementById("adminMap");
  if (!mapEl || typeof L === "undefined") return;
  const markers = window.SILAJAK_REPORT_MARKERS || [];
  const map = L.map(mapEl).setView([-6.2, 106.816666], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  const bounds = [];
  markers.forEach((item) => {
    const lat = Number(item.latitude);
    const lng = Number(item.longitude);
    if (!lat || !lng) return;
    bounds.push([lat, lng]);
    L.marker([lat, lng]).addTo(map).bindPopup(`<strong>${item.title}</strong><br>${item.road_name}<br>${item.status}`);
  });
  if (bounds.length) map.fitBounds(bounds, { padding: [30, 30] });
}

function initUploadPreview() {
  const input = document.getElementById("mediaInput");
  const preview = document.getElementById("mediaPreview");
  if (!input || !preview) return;
  input.addEventListener("change", () => {
    preview.innerHTML = "";
    const file = input.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    const element = file.type.startsWith("video/") ? document.createElement("video") : document.createElement("img");
    if (element.tagName === "VIDEO") element.controls = true;
    element.src = url;
    preview.appendChild(element);
  });
}

function renderReportCharts(data, ids) {
  if (typeof Chart === "undefined" || !data) return;
  const BRAND = "#7a1220";
  const PALETTE = ["#eab308", "#3b82f6", "#ef4444", "#8b5cf6", "#f97316", "#0891b2", "#16a34a"];
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.plugins.legend.display = false;

  const trendEl = ids.trend && document.getElementById(ids.trend);
  if (trendEl && data.trend.labels.length) {
    new Chart(trendEl, {
      type: "line",
      data: {
        labels: data.trend.labels,
        datasets: [{ data: data.trend.values, borderColor: BRAND, backgroundColor: "rgba(122, 18, 32, 0.12)", fill: true, tension: 0.3, pointRadius: 3 }],
      },
      options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });
  } else if (trendEl) {
    trendEl.replaceWith(Object.assign(document.createElement("p"), { className: "empty-state", textContent: "Belum ada data pada rentang ini." }));
  }

  const statusEl = ids.status && document.getElementById(ids.status);
  if (statusEl) {
    new Chart(statusEl, {
      type: "bar",
      data: { labels: data.status.labels, datasets: [{ data: data.status.values, backgroundColor: PALETTE }] },
      options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });
  }

  const damageEl = ids.damage && document.getElementById(ids.damage);
  if (damageEl) {
    new Chart(damageEl, {
      type: "doughnut",
      data: { labels: data.damage.labels, datasets: [{ data: data.damage.values, backgroundColor: ["#22c55e", "#eab308", "#ef4444", "#94a3b8"] }] },
      options: { responsive: true, plugins: { legend: { display: true, position: "bottom" } } },
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initReportMap();
  initDetailMap();
  initAdminMap();
  initUploadPreview();
  initFlashAutoDismiss();
});

function initFlashAutoDismiss() {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((flash) => {
    window.setTimeout(() => {
      flash.classList.add("flash-hiding");
      window.setTimeout(() => {
        flash.remove();
        const wrap = document.querySelector(".flash-wrap");
        if (wrap && !wrap.querySelector(".flash")) wrap.remove();
      }, 280);
    }, 1000);
  });
}

