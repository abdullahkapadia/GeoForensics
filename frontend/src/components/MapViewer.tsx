import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Layers } from 'lucide-react';
import type { CandidateLocation } from '../api';

interface MapViewerProps {
  candidates: CandidateLocation[];
  selectedCandidateId: string | null;
  onSelectCandidate: (candidateId: string) => void;
  previewUrl: string | null;
  onOpenImageModal: () => void;
}

type LayerType = 'street' | 'topo' | 'satellite';

const TILE_LAYERS: Record<LayerType, { url: string; minZoom: number; maxZoom: number; attribution: string }> = {
  street: {
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    minZoom: 2,
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  },
  topo: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    minZoom: 2,
    maxZoom: 19,
    attribution: '&copy; Esri &copy; OpenStreetMap',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    minZoom: 2,
    maxZoom: 19,
    attribution: '&copy; Esri, Maxar, Earthstar Geographics',
  },
};

export default function MapViewer({
  candidates,
  selectedCandidateId,
  onSelectCandidate,
  previewUrl,
  onOpenImageModal,
}: MapViewerProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const currentTileLayerRef = useRef<L.TileLayer | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());
  const circleRef = useRef<L.Circle | null>(null);
  const [activeLayer, setActiveLayer] = useState<LayerType>('street');

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [20, 0],
      zoom: 3,
      minZoom: 2,
      maxZoom: 19,
      zoomControl: false,
      attributionControl: false,
      worldCopyJump: true,
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Initial tile layer (Clean OSM Street map with crisp blue oceans & borders)
    const initialConfig = TILE_LAYERS.street;
    const tileLayer = L.tileLayer(initialConfig.url, {
      minZoom: initialConfig.minZoom,
      maxZoom: initialConfig.maxZoom,
      attribution: initialConfig.attribution,
    }).addTo(map);

    currentTileLayerRef.current = tileLayer;
    mapInstanceRef.current = map;

    // Ensure map tiles stretch to full container dimensions
    setTimeout(() => {
      map.invalidateSize();
    }, 100);

    const handleResize = () => map.invalidateSize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Switch tile layer
  const switchLayer = (type: LayerType) => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (currentTileLayerRef.current) {
      currentTileLayerRef.current.remove();
    }

    const config = TILE_LAYERS[type];
    const newLayer = L.tileLayer(config.url, {
      minZoom: config.minZoom,
      maxZoom: config.maxZoom,
      attribution: config.attribution,
    }).addTo(map);

    currentTileLayerRef.current = newLayer;
    setActiveLayer(type);
  };

  // Update markers and view when candidates or selection changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || candidates.length === 0) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current.clear();
    if (circleRef.current) {
      circleRef.current.remove();
      circleRef.current = null;
    }

    const bounds = L.latLngBounds([]);

    candidates.forEach((cand, index) => {
      if (typeof cand.lat !== 'number' || typeof cand.lng !== 'number') return;

      const isSelected = cand.id === selectedCandidateId;
      const isTop = index === 0;

      // Terracotta color palette for pins
      const pinColor = isTop
        ? '#c85a32'
        : isSelected
        ? '#a84520'
        : '#b5835a';

      const pulseEffect = (isTop || isSelected)
        ? `<div style="
            position: absolute;
            top: -6px; left: -6px; right: -6px; bottom: -6px;
            border-radius: 50%;
            border: 2px solid ${pinColor};
            opacity: 0.5;
            animation: pulse-dot 2s ease-in-out infinite;
          "></div>`
        : '';

      const iconHtml = `
        <div style="
          position: relative;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          ${pulseEffect}
          <div style="
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: ${pinColor};
            border: 2px solid #ffffff;
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(200, 90, 50, 0.4);
            cursor: pointer;
          ">
            #${index + 1}
          </div>
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-map-pin',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([cand.lat, cand.lng], { icon: customIcon }).addTo(map);

      // Popup
      const scoreDisplay = cand.score > 1 ? cand.score.toFixed(1) : (cand.score * 100).toFixed(1);
      const popupContent = `
        <div style="font-family: inherit; font-size: 12.5px; line-height: 1.4; color: #23201e;">
          <strong style="color: ${pinColor}; font-size: 13.5px;">#${index + 1} ${cand.name}</strong><br/>
          <span style="color: #57524e;">${cand.city ? cand.city + ', ' : ''}${cand.country}</span><br/>
          <span style="color: #7c756e; font-size: 11px;">Confidence: <strong style="color: #c85a32;">${scoreDisplay}%</strong></span>
          ${cand.resolved_address ? `<br/><span style="color: #8c827a; font-size: 10px;">${cand.resolved_address}</span>` : ''}
        </div>
      `;
      marker.bindPopup(popupContent, {
        className: 'offwhite-leaflet-popup',
      });

      marker.on('click', () => {
        onSelectCandidate(cand.id);
      });

      markersRef.current.set(cand.id, marker);
      bounds.extend([cand.lat, cand.lng]);
    });

    // If candidate selected, highlight uncertainty radius in terracotta
    const currentSelected = candidates.find((c) => c.id === selectedCandidateId) || candidates[0];
    if (currentSelected && typeof currentSelected.lat === 'number' && typeof currentSelected.lng === 'number') {
      const radiusKm = currentSelected.uncertainty_radius_km || 15;
      // Clamp visual radius to avoid covering the entire continent/screen in orange
      const visualRadiusKm = Math.min(radiusKm, 100);
      const radiusMeters = visualRadiusKm * 1000;
      const isLargeArea = radiusKm >= 20;

      circleRef.current = L.circle([currentSelected.lat, currentSelected.lng], {
        radius: radiusMeters,
        color: '#c25732',
        weight: isLargeArea ? 1.5 : 2,
        fillColor: '#c25732',
        fillOpacity: isLargeArea ? 0 : 0.08, // No fill for large country/regional areas
        dashArray: '5, 5',
      }).addTo(map);

      map.flyTo([currentSelected.lat, currentSelected.lng], Math.min(14, Math.max(9, Math.round(15 - Math.log2(radiusKm + 1)))), {
        duration: 1.2,
      });

      const selectedMarker = markersRef.current.get(currentSelected.id);
      if (selectedMarker) {
        selectedMarker.openPopup();
      }
    } else if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
    }

    setTimeout(() => {
      map.invalidateSize();
    }, 200);
  }, [candidates, selectedCandidateId, onSelectCandidate]);

  return (
    <div className="map-container">
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Layer Switcher Pill */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          left: 12,
          zIndex: 500,
          background: 'rgba(255, 255, 255, 0.95)',
          padding: '3px',
          borderRadius: 'var(--radius-full)',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--border-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
        }}
      >
        <span style={{ padding: '0 6px 0 8px', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center' }}>
          <Layers size={13} />
        </span>
        <button
          type="button"
          onClick={() => switchLayer('street')}
          style={{
            border: 'none',
            background: activeLayer === 'street' ? 'var(--accent-terracotta)' : 'transparent',
            color: activeLayer === 'street' ? '#ffffff' : 'var(--text-secondary)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          Street
        </button>
        <button
          type="button"
          onClick={() => switchLayer('topo')}
          style={{
            border: 'none',
            background: activeLayer === 'topo' ? 'var(--accent-terracotta)' : 'transparent',
            color: activeLayer === 'topo' ? '#ffffff' : 'var(--text-secondary)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          Topo
        </button>
        <button
          type="button"
          onClick={() => switchLayer('satellite')}
          style={{
            border: 'none',
            background: activeLayer === 'satellite' ? 'var(--accent-terracotta)' : 'transparent',
            color: activeLayer === 'satellite' ? '#ffffff' : 'var(--text-secondary)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '11px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          Satellite
        </button>
      </div>

      {previewUrl && (
        <div
          className="map-image-overlay"
          onClick={onOpenImageModal}
          title="Click to view full image & bounding boxes"
        >
          <img src={previewUrl} alt="Analyzed target" />
        </div>
      )}
    </div>
  );
}
