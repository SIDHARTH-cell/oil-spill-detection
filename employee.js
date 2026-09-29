/**
 * ============================================================================
 * MARITIME SURVEILLANCE & COMPLIANCE SYSTEM
 * Live Oil Spill Analysis
 *
 * Frontend:
 *   Leaflet
 *
 * Backend:
 *   FastAPI
 *
 * Data:
 *   Sentinel-1 spill GeoJSON
 *   AIS trajectories
 *   Backward drift
 *   Monte Carlo source uncertainty
 *   Candidate vessel ranking
 * ============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {

  const mapElement =
    document.getElementById("tactical-leaflet-map");

  if (!mapElement || typeof L === "undefined") {
    return;
  }


  // =========================================================================
  // BACKEND
  // =========================================================================

  const API_URL =
    "https://oil-spill-backend-a8if.onrender.com/api/dashboard";


  // =========================================================================
  // TELEMETRY
  // =========================================================================

  const coordTelemetry =
    document.querySelector(
      "#map-footer-telemetry .coord-label"
    );


  // =========================================================================
  // MAP
  // =========================================================================

  const map = L.map(
    "tactical-leaflet-map",
    {
      center: [19.68805, -92.07878],
      zoom: 12,

      zoomControl: false,

      minZoom: 3,
      maxZoom: 18
    }
  );


  L.control.zoom({
    position: "bottomright"
  }).addTo(map);


  // =========================================================================
  // BASE MAPS
  // =========================================================================


  const satelliteLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution:
        "Tiles &copy; Esri &mdash; Sentinel / NASA / USGS / Maxar",

      maxZoom: 18
    }
  );


  const osmLayer = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',

      maxZoom: 19
    }
  );


  // Default map
  satelliteLayer.addTo(map);


  // =========================================================================
  // MAP LAYERS
  // =========================================================================

  const spillLayer =
    L.layerGroup().addTo(map);

  const vesselLayer =
    L.layerGroup().addTo(map);

  const driftLayer =
    L.layerGroup().addTo(map);

  const sourceLayer =
    L.layerGroup().addTo(map);

  const uncertaintyLayer =
    L.layerGroup().addTo(map);


  // =========================================================================
  // LAYER SWITCHER
  // =========================================================================

  L.control.layers(

    {
      "Satellite Imagery":
        satelliteLayer,

      "Maritime Standard":
        osmLayer
    },

    {
      "Oil Spill":
        spillLayer,

      "AIS Vessel Tracks":
        vesselLayer,

      "Backward Drift":
        driftLayer,

      "Estimated Source":
        sourceLayer,

      "Source Uncertainty":
        uncertaintyLayer
    },

    {
      position: "topright",
      collapsed: true
    }

  ).addTo(map);


  // =========================================================================
  // TELEMETRY
  // =========================================================================

  map.on("mousemove", (event) => {

    if (!coordTelemetry) {
      return;
    }


    coordTelemetry.textContent =
      `LAT ${event.latlng.lat.toFixed(4)}°N • ` +
      `LON ${event.latlng.lng.toFixed(4)}°E ` +
      `(ZOOM: ${map.getZoom()})`;

  });


  // =========================================================================
  // HELPERS
  // =========================================================================

  function getField(
    object,
    possibleNames
  ) {

    if (!object) {
      return null;
    }


    for (const name of possibleNames) {

      if (
        Object.prototype.hasOwnProperty.call(
          object,
          name
        )
      ) {

        return object[name];

      }

    }


    return null;
  }


  function numberValue(value) {

    const number =
      Number(value);

    return Number.isFinite(number)
      ? number
      : null;

  }


  function getLat(row) {

    return numberValue(
      getField(
        row,
        [
          "latitude",
          "lat",
          "LAT",
          "Latitude"
        ]
      )
    );

  }


  function getLon(row) {

    return numberValue(
      getField(
        row,
        [
          "longitude",
          "lon",
          "lng",
          "LON",
          "Longitude"
        ]
      )
    );

  }


  function getVesselName(row) {

    return (
      getField(
        row,
        [
          "vessel_name",
          "name",
          "Vessel_Name",
          "ship_name"
        ]
      ) ||
      "Unknown Vessel"
    );

  }


  // =========================================================================
  // LOAD DASHBOARD
  // =========================================================================

  async function loadDashboard() {

    try {

      console.log(
        "Connecting to oil-spill analysis backend..."
      );


      const response =
        await fetch(API_URL);


      if (!response.ok) {

        throw new Error(
          `Backend returned HTTP ${response.status}`
        );

      }


      const data =
        await response.json();


      console.log(
        "Oil-spill analysis data received:",
        data
      );


      // =====================================================================
      // 1. OIL SPILL GEOJSON
      // =====================================================================

      drawSpill(
        data.spill?.geojson
      );


      // =====================================================================
      // 2. BACKWARD DRIFT
      // =====================================================================

      drawBackwardDrift(
        data.source?.backward_drift || []
      );


      // =====================================================================
      // 3. SOURCE UNCERTAINTY
      // =====================================================================

      drawSourceUncertainty(
        data.source?.uncertainty || []
      );


      // =====================================================================
      // 4. AIS VESSEL TRAJECTORIES
      // =====================================================================

      drawAIS(
        data.ais || [],
        data.vessels || []
      );


      // =====================================================================
      // 5. FIT MAP
      // =====================================================================

      fitMapToAnalysis(
        data
      );


      // Make sure Leaflet recalculates its size
      setTimeout(
        () => map.invalidateSize(),
        400
      );


      console.log(
        "Oil-spill analysis successfully loaded."
      );


    } catch (error) {

      console.error(
        "Oil-spill backend connection failed:",
        error
      );

      showBackendError(
        error
      );

    }

  }


  // =========================================================================
  // DRAW OIL SPILL
  // =========================================================================

  function drawSpill(
    geojson
  ) {

    if (!geojson) {

      console.warn(
        "No spill GeoJSON received."
      );

      return;

    }


    const layer =
      L.geoJSON(
        geojson,
        {

          style: {

            color: "#ef4444",

            weight: 2,

            opacity: 0.95,

            fillColor: "#ef4444",

            fillOpacity: 0.25

          },


          onEachFeature:
            function (
              feature,
              layer
            ) {

              layer.bindPopup(
                `
                <div style="min-width:180px">
                  <strong>Detected Oil Spill</strong>
                  <br><br>
                  Detection source:
                  Sentinel-1 SAR
                  <br>
                  Segmentation:
                  U-Net
                </div>
                `
              );

            }

        }
      );


    layer.addTo(
      spillLayer
    );


    console.log(
      "Oil spill polygon added."
    );

  }


  // =========================================================================
  // DRAW BACKWARD DRIFT
  // =========================================================================

  function drawBackwardDrift(
    rows
  ) {

    if (!rows.length) {

      console.warn(
        "No backward drift data."
      );

      return;

    }


    const coordinates =
      rows
        .map(
          row => {

            const lat =
              getLat(row);

            const lon =
              getLon(row);


            if (
              lat === null ||
              lon === null
            ) {

              return null;

            }


            return [
              lat,
              lon
            ];

          }
        )
        .filter(
          Boolean
        );


    if (
      coordinates.length < 2
    ) {

      return;

    }


    const line =
      L.polyline(
        coordinates,
        {

          color: "#f59e0b",

          weight: 3,

          opacity: 0.9

        }
      );


    line.bindPopup(
      `
      <strong>Backward Drift Estimate</strong>
      <br><br>
      Estimated movement of the oil-spill
      source backwards through the environment.
      `
    );


    line.addTo(
      driftLayer
    );


    console.log(
      "Backward drift path added."
    );

  }


  // =========================================================================
  // SOURCE UNCERTAINTY
  // =========================================================================

  function drawSourceUncertainty(
    rows
  ) {

    if (!rows.length) {

      return;

    }


    const points =
      rows
        .map(
          row => {

            const lat =
              getLat(row);

            const lon =
              getLon(row);


            if (
              lat === null ||
              lon === null
            ) {

              return null;

            }


            return [
              lat,
              lon
            ];

          }
        )
        .filter(
          Boolean
        );


    if (!points.length) {

      return;

    }


    // -------------------------------------------------------------
    // Calculate approximate bounding region
    // -------------------------------------------------------------

    const lats =
      points.map(
        p => p[0]
      );

    const lons =
      points.map(
        p => p[1]
      );


    const minLat =
      Math.min(...lats);

    const maxLat =
      Math.max(...lats);

    const minLon =
      Math.min(...lons);

    const maxLon =
      Math.max(...lons);


    const rectangle =
      L.rectangle(
        [
          [minLat, minLon],
          [maxLat, maxLon]
        ],
        {

          color: "#8b5cf6",

          weight: 2,

          fillColor: "#8b5cf6",

          fillOpacity: 0.08

        }
      );


    rectangle.bindPopup(
      `
      <strong>Estimated Source Region</strong>
      <br><br>
      Region generated from Monte Carlo
      backward-drift simulations.
      `
    );


    rectangle.addTo(
      uncertaintyLayer
    );


    // -------------------------------------------------------------
    // Mean estimated source
    // -------------------------------------------------------------

    const meanLat =
      lats.reduce(
        (a, b) => a + b,
        0
      ) / lats.length;


    const meanLon =
      lons.reduce(
        (a, b) => a + b,
        0
      ) / lons.length;


    const sourceMarker =
      L.circleMarker(
        [
          meanLat,
          meanLon
        ],
        {

          radius: 7,

          color: "#ffffff",

          weight: 2,

          fillColor: "#8b5cf6",

          fillOpacity: 0.95

        }
      );


    sourceMarker.bindPopup(
      `
      <strong>Estimated Spill Source</strong>
      <br><br>
      Latitude:
      ${meanLat.toFixed(5)}
      <br>
      Longitude:
      ${meanLon.toFixed(5)}
      `
    );


    sourceMarker.addTo(
      sourceLayer
    );


    console.log(
      "Source uncertainty region added."
    );

  }


  // =========================================================================
  // DRAW AIS TRAJECTORIES
  // =========================================================================

  function drawAIS(
    rows,
    rankedVessels
  ) {

    if (!rows.length) {

      console.warn(
        "No AIS data received."
      );

      return;

    }


    const tracks = {};


    // -------------------------------------------------------------
    // Group positions by vessel
    // -------------------------------------------------------------

    rows.forEach(
      row => {

        const name =
          getVesselName(row);

        const lat =
          getLat(row);

        const lon =
          getLon(row);


        if (
          lat === null ||
          lon === null
        ) {

          return;

        }


        if (
          !tracks[name]
        ) {

          tracks[name] = [];

        }


        tracks[name].push(
          {
            lat,
            lon,
            row
          }
        );

      }
    );


    // -------------------------------------------------------------
    // Determine highest priority vessel
    // -------------------------------------------------------------

    let selectedVessel =
      null;


    if (
      rankedVessels.length
    ) {

      const sorted =
        [...rankedVessels]
          .sort(
            (a, b) =>
              Number(
                b.priority_score || 0
              ) -
              Number(
                a.priority_score || 0
              )
          );


      selectedVessel =
        sorted[0]?.vessel_name ||
        null;

    }


    const colors = [

      "#4C78A8",

      "#72B7B2",

      "#F2A65A",

      "#8E9AAF",

      "#6C8E7B",

      "#B07AA1",

      "#7F8C7D",

      "#C17C74"

    ];


    // -------------------------------------------------------------
    // Draw each vessel
    // -------------------------------------------------------------

    Object.entries(
      tracks
    ).forEach(
      ([name, positions], index) => {

        if (
          positions.length < 2
        ) {

          return;

        }


        const coordinates =
          positions.map(
            p => [
              p.lat,
              p.lon
            ]
          );


        const selected =
          name === selectedVessel;


        const color =
          colors[
            index % colors.length
          ];


        const line =
          L.polyline(
            coordinates,
            {

              color:

                selected
                  ? "#ffffff"
                  : color,

              weight:

                selected
                  ? 4
                  : 2,

              opacity:

                selected
                  ? 1
                  : 0.65

            }
          );


        line.bindPopup(
          `
          <strong>${name}</strong>
          <br><br>
          AIS trajectory
          ${
            selected
              ? "<br><strong>Highest priority candidate</strong>"
              : ""
          }
          `
        );


        line.addTo(
          vesselLayer
        );

      }
    );


    console.log(
      "AIS vessel trajectories added."
    );


    if (selectedVessel) {

      console.log(
        "Selected candidate:",
        selectedVessel
      );

    }

  }


  // =========================================================================
  // FIT MAP
  // =========================================================================

  function fitMapToAnalysis(
    data
  ) {

    const bounds = [];


    // Spill
    if (
      data.spill?.geojson
    ) {

      try {

        const spillLayerTemp =
          L.geoJSON(
            data.spill.geojson
          );


        const spillBounds =
          spillLayerTemp.getBounds();


        if (
          spillBounds.isValid()
        ) {

          bounds.push(
            spillBounds.getSouthWest()
          );

          bounds.push(
            spillBounds.getNorthEast()
          );

        }

      } catch (error) {

        console.warn(
          "Could not calculate spill bounds.",
          error
        );

      }

    }


    // AIS
    const ais =
      data.ais || [];


    ais.forEach(
      row => {

        const lat =
          getLat(row);

        const lon =
          getLon(row);


        if (
          lat !== null &&
          lon !== null
        ) {

          bounds.push(
            [lat, lon]
          );

        }

      }
    );


    if (
      bounds.length > 0
    ) {

      map.fitBounds(
        bounds,
        {
          padding: [
            30,
            30
          ]
        }
      );

    }

  }


  // =========================================================================
  // ERROR DISPLAY
  // =========================================================================

  function showBackendError(
    error
  ) {

    console.error(
      error
    );


    if (!coordTelemetry) {
      return;
    }


    coordTelemetry.textContent =
      "ANALYSIS BACKEND OFFLINE";

  }


  // =========================================================================
  // START
  // =========================================================================

  loadDashboard();

  // =========================================================================
  // EXPAND MAP / OPEN ANALYSIS DASHBOARD
  // =========================================================================

  const attributionForm =
    document.getElementById(
      "attribution-search-form"
    );

  const workspace =
    document.getElementById(
      "workspace-container"
    );


  if (
    attributionForm &&
    workspace
  ) {

    attributionForm.addEventListener(
      "submit",
      (event) => {

        // Prevent the browser from reloading/submitting the form
        event.preventDefault();


        // Expand the GIS dashboard
        workspace.classList.add(
          "map-expanded"
        );


        // Give Leaflet time to receive the new size
        setTimeout(
          () => {

            map.invalidateSize();

          },
          500
        );


        console.log(
          "Oil Spill Analysis Dashboard expanded."
        );

      }
    );

  }
    // =========================================================================
  // CLOSE EXPANDED MAP
  // =========================================================================

  const closeMapDashboard =
    document.getElementById(
      "close-map-dashboard"
    );


  if (closeMapDashboard) {

    closeMapDashboard.addEventListener(
      "click",
      () => {

        workspace.classList.remove(
          "map-expanded"
        );


        setTimeout(
          () => {

            map.invalidateSize();

          },
          500
        );

      }
    );

  }

  // ============================================================
  // OPEN STREAMLIT DASHBOARD INSIDE EMPLOYEE PAGE
  // ============================================================

  const dashboardOverlay = document.createElement("div");

  dashboardOverlay.id = "streamlit-dashboard-overlay";

  dashboardOverlay.innerHTML = `
    <div id="streamlit-dashboard-header">
      <span>OIL SPILL SOURCE ANALYSIS</span>
      <button
        id="close-streamlit-dashboard"
        type="button"
        onclick="document.getElementById('streamlit-dashboard-overlay').classList.remove('active');">
        BACK TO MAP
      </button>
    </div>

    <iframe
      id="streamlit-dashboard-frame"
      src="https://oilspillculprit.streamlit.app/?embed=true"
      title="Oil Spill Source Analysis Dashboard">
    </iframe>
  `;

  document.body.appendChild(dashboardOverlay);


  // ============================================================
  // DASHBOARD STYLE
  // ============================================================

  const dashboardStyle = document.createElement("style");

  dashboardStyle.textContent = `
    #streamlit-dashboard-overlay {
      position: fixed;
      inset: 0;
      z-index: 999999;
      background: #06101e;
      display: none;
      flex-direction: column;
    }

    #streamlit-dashboard-overlay.active {
      display: flex !important;
    }

    #streamlit-dashboard-header {
      height: 52px;
      min-height: 52px;
      background: #071525;
      border-bottom: 1px solid rgba(56,189,248,0.35);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      color: #e5f3ff;
      font-family: Arial, sans-serif;
      font-size: 14px;
      font-weight: 600;
      letter-spacing: 1px;
      box-sizing: border-box;
    }

    #close-streamlit-dashboard {
      background: #10263b;
      color: #dff4ff;
      border: 1px solid rgba(56,189,248,0.5);
      border-radius: 5px;
      padding: 8px 16px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
    }

    #close-streamlit-dashboard:hover {
      background: #2563eb;
      color: white;
    }

    #streamlit-dashboard-frame {
      width: 100%;
      height: calc(100vh - 52px);
      flex: 1;
      border: none;
      display: block;
      background: #06101e;
    }
  `;

  document.head.appendChild(dashboardStyle);


  // ============================================================
  // OPEN DASHBOARD
  // ============================================================

  function openStreamlitDashboard() {
    console.log("OPENING STREAMLIT DASHBOARD");

    dashboardOverlay.classList.add("active");
  }


  // ============================================================
  // CLOSE DASHBOARD
  // ============================================================

  const closeStreamlitDashboard =
    document.getElementById("close-streamlit-dashboard");

  if (closeStreamlitDashboard) {
    closeStreamlitDashboard.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();

      dashboardOverlay.classList.remove("active");

      setTimeout(() => {
        map.invalidateSize();
      }, 300);
    });
  }


  // ============================================================
  // CLICK LEAFLET MAP -> OPEN STREAMLIT
  // ============================================================

  map.on("click", function () {
    console.log("MAP CLICK DETECTED");

    openStreamlitDashboard();
  });


});
