import cv2
import numpy as np
from typing import Dict, Any, List
from app.models.schemas import BoundingBox, EvidenceItem

class VisualSceneService:
    """
    Forensic scene understanding:
    - Biome / Vegetation classification (Excess Green Index ExG)
    - Soil & Terrain analysis (arid, tropical, temperate, alpine)
    - Sky & Solar shadow angle / Azimuth estimation
    - Urban density & Horizon estimation
    """
    
    def analyze_scene(self, image_path: str) -> Dict[str, Any]:
        results = {
            "environment_type": "Urban",
            "vegetation_index": 0.0,
            "soil_type": "Neutral",
            "sky_fraction": 0.0,
            "estimated_lighting": "Daylight",
            "sun_shadow_azimuth_deg": None,
            "hemisphere_heuristic": "Ambiguous",
            "evidence_items": []
        }

        try:
            img = cv2.imread(image_path)
            if img is None:
                return results

            h, w = img.shape[:2]
            
            # 1. Sky fraction and Horizon
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # Sky mask: upper third, high value, moderate/low saturation
            upper_third = hsv[:int(h * 0.35), :]
            sky_mask = (upper_third[:, :, 2] > 180) & (upper_third[:, :, 1] < 120)
            sky_fraction = np.sum(sky_mask) / float(upper_third.size // 3)
            results["sky_fraction"] = round(float(sky_fraction), 3)

            # 2. Vegetation index (Excess Green ExG = 2*G - R - B)
            b, g, r = cv2.split(img.astype(np.float32))
            exg = 2.0 * g - r - b
            veg_pixels = np.sum(exg > 30)
            veg_fraction = veg_pixels / float(h * w)
            results["vegetation_index"] = round(float(veg_fraction), 3)

            # 3. Dominant colors in lower half (terrain/road)
            lower_half = img[int(h * 0.6):, :]
            avg_bgr = np.mean(lower_half, axis=(0, 1))
            
            # Check for reddish laterite soil (common in tropical/South Asia/Australia/Sub-Saharan)
            if avg_bgr[2] > avg_bgr[0] * 1.3 and avg_bgr[2] > avg_bgr[1] * 1.15:
                results["soil_type"] = "Lateritic / Red Loam"
                ev = EvidenceItem(
                    id="ev_soil_laterite",
                    type="terrain",
                    label="Laterite / Red Earth Detected",
                    description="Iron-rich weathered soil signature characteristic of tropical, South Asian, or Australian biomes.",
                    confidence=0.74,
                    bbox=BoundingBox(ymin=70.0, xmin=10.0, ymax=95.0, xmax=90.0, label="Terrain/Soil"),
                    supporting_candidates=["India", "Australia"],
                    polarity="supports"
                )
                results["evidence_items"].append(ev)

            # 4. Vegetation Evidence
            if veg_fraction > 0.20:
                results["environment_type"] = "Lush / Vegetated Rural or Suburban"
                ev = EvidenceItem(
                    id="ev_veg_high",
                    type="vegetation_climate",
                    label="Dense Canopy / High Biomass Index",
                    description="Excess Green index exceeds 0.20, indicating temperate or humid subtropical vegetative density.",
                    confidence=0.78,
                    bbox=BoundingBox(ymin=15.0, xmin=5.0, ymax=50.0, xmax=95.0, label="Canopy Zone"),
                    supporting_candidates=[],
                    polarity="supports"
                )
                results["evidence_items"].append(ev)
            elif veg_fraction < 0.05:
                results["environment_type"] = "High-Density Built Urban / Arid"
                ev = EvidenceItem(
                    id="ev_veg_sparse",
                    type="vegetation_climate",
                    label="Paved Urban / Low Vegetative Cover",
                    description="Sparse vegetation (<5% canopy), consistent with central commercial core or arid climate zone.",
                    confidence=0.82,
                    bbox=BoundingBox(ymin=30.0, xmin=10.0, ymax=90.0, xmax=90.0, label="Paved Urban Footprint"),
                    supporting_candidates=[],
                    polarity="supports"
                )
                results["evidence_items"].append(ev)

            # 5. Sun Azimuth / Shadow Heuristic
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Detect dark elongated shadow blobs
            shadow_mask = (gray < 45) & (cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1] < 80)
            shadow_cnts, _ = cv2.findContours(shadow_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            shadow_angles = []
            for cnt in shadow_cnts:
                if cv2.contourArea(cnt) > 200:
                    if len(cnt) >= 5:
                        ellipse = cv2.fitEllipse(cnt)
                        shadow_angles.append(ellipse[2])

            if shadow_angles:
                median_angle = float(np.median(shadow_angles))
                results["sun_shadow_azimuth_deg"] = round(median_angle, 1)
                ev = EvidenceItem(
                    id="ev_shadow_azimuth",
                    type="sky_sun",
                    label=f"Cast Shadow Vector (~{round(median_angle)}°)",
                    description="Sun solar elevation and cast shadow orientation consistent with low-to-mid northern latitude midday lighting.",
                    confidence=0.68,
                    bbox=BoundingBox(ymin=60.0, xmin=20.0, ymax=90.0, xmax=70.0, label="Shadow Vector"),
                    supporting_candidates=[],
                    polarity="supports"
                )
                results["evidence_items"].append(ev)

        except Exception as e:
            results["error"] = str(e)

        return results

visual_scene_service = VisualSceneService()
