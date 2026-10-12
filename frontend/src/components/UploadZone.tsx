import { useState, useCallback, useRef } from 'react';
import { Upload, X, ArrowRight, Shield, Layers, FileImage } from 'lucide-react';

interface UploadZoneProps {
  onFileSelected: (file: File | null) => void;
  selectedFile: File | null;
  previewUrl: string | null;
  cues: string;
  onCuesChange: (val: string) => void;
  onUpload: () => void;
  uploading: boolean;
}

interface BenchmarkCase {
  id: string;
  ref: string;
  title: string;
  region: string;
  signatures: string;
  path: string;
  filename: string;
  cues: string;
}

const BENCHMARK_CASES: BenchmarkCase[] = [
  {
    id: 'case-stepwell',
    ref: '#CASE-01',
    title: 'Chand Baori Stepwell',
    region: 'Rajasthan, India',
    signatures: 'Symmetric sandstone stair terraces, arid sunlight profile, 9th c. architecture',
    path: '/samples/stepwell_india.jpg',
    filename: 'stepwell_india.jpg',
    cues: 'Chand Baori, Abhaneri, Rajasthan, stepwell, sandstone, arid climate',
  },
  {
    id: 'case-kedarnath',
    ref: '#CASE-02',
    title: 'Kedarnath Temple Shrine',
    region: 'Uttarakhand, India',
    signatures: 'Himalayan snow massif, grey stone sanctum, high altitude alpine valley',
    path: '/samples/kedarnath_temple.jpg',
    filename: 'kedarnath_temple.jpg',
    cues: 'Kedarnath temple, Garhwal Himalayas, Mandakini river valley, Uttarakhand',
  },
  {
    id: 'case-tokyo',
    ref: '#CASE-03',
    title: 'Akihabara Chuo-dori',
    region: 'Tokyo, Japan',
    signatures: 'High-density Kanji/Kana commercial signage, left-hand asphalt corridor',
    path: '/samples/tokyo_street.jpg',
    filename: 'tokyo_street.jpg',
    cues: 'Akihabara, Chiyoda, Tokyo, Japanese signage, left-hand traffic, electronics district',
  },
  {
    id: 'case-village',
    ref: '#CASE-04',
    title: 'Rural Roadway & Utility Grid',
    region: 'India (Rural Corridor)',
    signatures: 'Concrete multi-hole utility poles, unpaved red/brown dirt track, tropical flora',
    path: '/samples/indian_village.jpg',
    filename: 'indian_village.jpg',
    cues: 'Rural India, concrete utility poles with holes, dirt road, village settlement',
  },
];

export default function UploadZone({
  onFileSelected,
  selectedFile,
  previewUrl,
  cues,
  onCuesChange,
  onUpload,
  uploading,
}: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      const dropped = e.dataTransfer.files?.[0];
      if (dropped) onFileSelected(dropped);
    },
    [onFileSelected]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) onFileSelected(selected);
    },
    [onFileSelected]
  );

  const loadBenchmarkCase = async (item: BenchmarkCase) => {
    try {
      setLoadingSample(item.filename);
      const res = await fetch(item.path);
      const blob = await res.blob();
      const loadedFile = new File([blob], item.filename, { type: 'image/jpeg' });
      onFileSelected(loadedFile);
      onCuesChange(item.cues);
    } catch (err) {
      console.error('Failed to load benchmark case', err);
    } finally {
      setLoadingSample(null);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="ingestion-console">
      {/* Editorial Header */}
      <div className="ingestion-header">
        <div className="ingestion-header__tag">
          <Shield size={12} /> OSINT INVESTIGATIVE WORKSTATION // GEOSPATIAL INTELLIGENCE
        </div>
        <h1 className="ingestion-header__title">Forensic Evidence Ingestion & Spatial Triangulation</h1>
        <p className="ingestion-header__desc">
          Ingest raw investigative photography for multimodal infrastructure forensics, utility pole hole patterns,
          road demarcation analysis, multilingual script identification, and live OpenStreetMap road-node geocoding.
        </p>
      </div>

      {/* Ingestion Split Grid */}
      <div className="ingestion-grid">
        {/* Left Column: Intake Card */}
        <div className="intake-card">
          <div className="intake-card__header">
            <div className="intake-card__title">
              <FileImage size={15} style={{ color: 'var(--accent-terracotta)' }} />
              Evidence Acquisition
            </div>
            <div className="intake-card__badge">EXIF + MULTIMODAL INGEST</div>
          </div>

          {!selectedFile ? (
            <div
              className={`intake-dropzone ${dragActive ? 'intake-dropzone--active' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <div className="intake-dropzone__icon-circle">
                <Upload size={20} />
              </div>
              <div className="intake-dropzone__main-text">
                Drop investigative imagery here or <span>browse local drive</span>
              </div>
              <div className="intake-dropzone__sub-text">
                SUPPORTS JPEG, PNG, WEBP, TIFF — UP TO 25 MB
              </div>
              <input
                ref={inputRef}
                type="file"
                accept=".jpg,.jpeg,.png,.webp,.tiff"
                onChange={handleFileChange}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          ) : (
            <div className="intake-dossier">
              {previewUrl && (
                <img
                  src={previewUrl}
                  alt={selectedFile.name}
                  className="intake-dossier__thumb"
                />
              )}
              <div className="intake-dossier__meta">
                <div className="intake-dossier__filename">{selectedFile.name}</div>
                <div className="intake-dossier__size">
                  {formatFileSize(selectedFile.size)} • {selectedFile.type || 'image/jpeg'}
                </div>
              </div>
              <button
                type="button"
                className="intake-dossier__remove"
                onClick={() => {
                  if (inputRef.current) inputRef.current.value = '';
                  onFileSelected(null);
                }}
                title="Remove evidence"
              >
                <X size={16} />
              </button>
            </div>
          )}

          {/* Contextual Cues Field */}
          <div className="intake-field">
            <label className="intake-field__label" htmlFor="cues-field">
              Contextual Priors / Analyst Notes
              <span className="intake-field__helper">Optional</span>
            </label>
            <input
              id="cues-field"
              className="intake-field__input"
              type="text"
              placeholder="e.g. India, utility pole holes, dirt road, left-hand traffic, temple..."
              value={cues}
              onChange={(e) => onCuesChange(e.target.value)}
            />
          </div>

          {/* Primary Action Button */}
          <button
            type="button"
            className="execute-btn"
            disabled={!selectedFile || uploading}
            onClick={onUpload}
          >
            {uploading ? (
              'Executing Forensic Pipeline…'
            ) : (
              <>
                Initiate Forensic Triangulation
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>

        {/* Right Column: Curated Benchmark Cases */}
        <div className="cases-deck">
          <div className="cases-deck__header">
            <div className="cases-deck__title">
              <Layers size={14} style={{ color: 'var(--accent-terracotta)' }} />
              Archival Benchmark Cases
            </div>
            <div className="cases-deck__desc">
              Pre-indexed forensic scenarios across distinct infrastructure & biomes. Click any case to mount:
            </div>
          </div>

          <div className="cases-list">
            {BENCHMARK_CASES.map((item) => {
              const isSelected = selectedFile?.name === item.filename;
              return (
                <div
                  key={item.id}
                  className={`case-card ${isSelected ? 'case-card--selected' : ''}`}
                  onClick={() => loadBenchmarkCase(item)}
                  style={{
                    borderColor: isSelected ? 'var(--accent-terracotta)' : undefined,
                    background: isSelected ? '#fffcf9' : undefined,
                  }}
                >
                  <img
                    src={item.path}
                    alt={item.title}
                    className="case-card__thumb"
                  />
                  <div className="case-card__content">
                    <div className="case-card__top">
                      <span className="case-card__ref">{item.ref}</span>
                      <span className="case-card__region">{item.region}</span>
                    </div>
                    <div className="case-card__title">
                      {loadingSample === item.filename ? 'Mounting Evidence…' : item.title}
                    </div>
                    <div className="case-card__cues">{item.signatures}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
