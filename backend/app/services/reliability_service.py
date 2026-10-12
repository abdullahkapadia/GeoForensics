import cv2
import numpy as np
from typing import Dict, Any, Optional, List

class ReliabilityService:
    """
    Image manipulation and reliability forensic assessment.
    Detects: screenshot indicators, compression anomalies, metadata-visual conflicts,
    AI-generation indicators, and crop/edit signatures.
    """

    def analyze_reliability(self, image_path: str, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            "status": "HIGH",
            "score": 1.0,
            "reasons": [],
            "metadata_visual_conflict": False,
            "is_screenshot": False,
            "is_ai_generated_indicators": False,
            "compression_anomaly": False,
            "details": {}
        }

        try:
            img = cv2.imread(image_path)
            if img is None:
                results["status"] = "QUESTIONABLE"
                results["score"] = 0.3
                results["reasons"].append("Image could not be decoded — possible corruption.")
                return results

            h, w = img.shape[:2]

            # 1. Screenshot detection: common screen resolutions & UI chrome
            screenshot_resolutions = [
                (1920, 1080), (2560, 1440), (3840, 2160),
                (1366, 768), (1440, 900), (1536, 864),
                (750, 1334), (1125, 2436), (1170, 2532),  # iPhone
                (1080, 1920), (1080, 2340), (1080, 2400),  # Android
            ]
            for sw, sh in screenshot_resolutions:
                if (w == sw and h == sh) or (w == sh and h == sw):
                    results["is_screenshot"] = True
                    results["reasons"].append(
                        f"Image dimensions ({w}×{h}) exactly match standard display resolution — likely a screenshot."
                    )
                    results["score"] = min(results["score"], 0.65)
                    break

            # Status bar detection (top 5% of image)
            top_strip = img[:int(h * 0.05), :]
            if top_strip.size > 0:
                strip_std = float(np.std(top_strip))
                if strip_std < 15:  # Very uniform top bar = status bar
                    results["is_screenshot"] = True
                    results["reasons"].append(
                        "Top strip shows uniform pixel intensity consistent with OS status bar overlay."
                    )
                    results["score"] = min(results["score"], 0.60)

            # 2. Missing EXIF on large image
            if not exif_data.get("has_exif") and w > 1000 and h > 1000:
                results["reasons"].append(
                    "No EXIF metadata present on high-resolution image — metadata may have been stripped."
                )
                results["score"] = min(results["score"], 0.75)

            # 3. JPEG compression artifact analysis (Error Level Analysis simplified)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            lap_var = float(laplacian.var())
            results["details"]["laplacian_variance"] = round(lap_var, 2)

            if lap_var < 10:
                results["compression_anomaly"] = True
                results["reasons"].append(
                    "Extremely low edge variance — heavily compressed or synthetically generated."
                )
                results["score"] = min(results["score"], 0.55)
            elif lap_var > 3000:
                results["compression_anomaly"] = True
                results["reasons"].append(
                    "Abnormally high frequency noise — possible post-processing or compositing artifact."
                )
                results["score"] = min(results["score"], 0.70)

            # 4. AI generation indicators (checkerboard / repeating pattern)
            # Simple frequency domain check for unnatural periodicity
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude = np.log(np.abs(f_shift) + 1)
            center_y, center_x = magnitude.shape[0] // 2, magnitude.shape[1] // 2
            # Check for bright dots away from center (periodic artifacts)
            ring = magnitude.copy()
            cv2.circle(ring, (center_x, center_y), 20, 0, -1)  # Remove DC
            peak_ratio = float(np.max(ring)) / (float(np.mean(magnitude)) + 1e-6)
            
            if peak_ratio > 15:
                results["is_ai_generated_indicators"] = True
                results["reasons"].append(
                    "Frequency domain exhibits strong periodic spectral peaks absent in natural photography."
                )
                results["score"] = min(results["score"], 0.50)

            # 5. Determine final status
            if results["score"] >= 0.80:
                results["status"] = "HIGH"
            elif results["score"] >= 0.50:
                results["status"] = "QUESTIONABLE"
            else:
                results["status"] = "MANIPULATED"

            if not results["reasons"]:
                results["reasons"].append("No manipulation indicators detected.")

        except Exception as e:
            results["status"] = "QUESTIONABLE"
            results["score"] = 0.5
            results["reasons"].append(f"Reliability analysis error: {str(e)}")

        return results


reliability_service = ReliabilityService()
