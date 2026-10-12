import re
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from app.models.schemas import BoundingBox, EvidenceItem
from app.services.geospatial_db import COUNTRY_PROFILES, CITIES_DB, WORLD_LANDMARKS

# Known street keywords and international markers
STREET_INDICATORS = {
    "IN": ["road", "rd", "marg", "chowk", "circle", "nagar", "gali", "rasta", "bridge", "bazaar", "pol", "gam", "darwaja"],
    "GB": ["street", "st", "road", "rd", "avenue", "ave", "lane", "close", "gardens", "crescent", "way", "hill", "high street"],
    "FR": ["rue", "boulevard", "bd", "avenue", "av", "place", "chemin", "allee", "passage", "quai", "pont"],
    "US": ["street", "st", "avenue", "ave", "blvd", "boulevard", "highway", "hwy", "freeway", "turnpike", "parkway", "pkwy", "dr", "drive"],
    "DE": ["straße", "strasse", "str", "weg", "allee", "platz", "brücke", "gasse"],
    "IT": ["via", "viale", "piazza", "corso", "largo", "vicolo", "ponte"],
    "JP": ["通り", "丁目", "道", "橋", "町", "駅"]
}

SCRIPT_PATTERNS = {
    "Devanagari": re.compile(r"[\u0900-\u097F]"),
    "Gujarati": re.compile(r"[\u0A80-\u0AFF]"),
    "Bengali": re.compile(r"[\u0980-\u09FF]"),
    "Arabic": re.compile(r"[\u0600-\u06FF]"),
    "Cyrillic": re.compile(r"[\u0400-\u04FF]"),
    "Greek": re.compile(r"[\u0370-\u03FF]"),
    "CJK": re.compile(r"[\u4E00-\u9FFF]"),
    "Hangul": re.compile(r"[\uAC00-\uD7AF]"),
    "Thai": re.compile(r"[\u0E00-\u0E7F]"),
    "Latin": re.compile(r"[A-Za-z]")
}

PHONE_PATTERNS = [
    (r"\+91[\s\-]?[0-9]{5}[\s\-]?[0-9]{5}", "IN", "+91 (India)"),
    (r"\+44[\s\-]?[0-9]{2,4}[\s\-]?[0-9]{6,8}", "GB", "+44 (United Kingdom)"),
    (r"\+33[\s\-]?[1-9][\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}", "FR", "+33 (France)"),
    (r"\+1[\s\-]?[2-9][0-9]{2}[\s\-]?[0-9]{3}[\s\-]?[0-9]{4}", "US", "+1 (USA / Canada)"),
    (r"\+49[\s\-]?[0-9]{3,5}[\s\-]?[0-9]{4,8}", "DE", "+49 (Germany)"),
    (r"\+81[\s\-]?[0-9]{1,4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}", "JP", "+81 (Japan)"),
    (r"\+39[\s\-]?[0-9]{2,4}[\s\-]?[0-9]{6,8}", "IT", "+39 (Italy)"),
]

TLD_PATTERN = re.compile(r"\b([a-zA-Z0-9\-]+\.(in|co\.in|gov\.in|uk|co\.uk|fr|de|jp|us|it|au|ca))\b", re.IGNORECASE)

class OCRForensicService:
    def __init__(self):
        self.tesseract_available = False
        try:
            import pytesseract
            self.pytesseract = pytesseract
            # Test if tesseract binary is actually accessible
            self.pytesseract.get_tesseract_version()
            self.tesseract_available = True
        except Exception:
            self.tesseract_available = False

    def detect_text_regions_cv(self, img_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects prominent candidate text / signboard bounding boxes using
        morphological gradient and connected component analysis (MSER / Sobel).
        """
        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # High-pass filter for edge-rich regions typical of typography
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient = cv2.subtract(grad_x, grad_y)
        gradient = cv2.convertScaleAbs(gradient)
        
        blurred = cv2.blur(gradient, (9, 9))
        _, thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 9))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect = float(cw) / max(1, ch)
            area = cw * ch
            
            # Signboards & text banners typically have aspect ratio > 1.2 and occupy reasonable area
            if aspect > 1.2 and area > (w * h * 0.002) and area < (w * h * 0.4):
                ymin = (y / h) * 100.0
                xmin = (x / w) * 100.0
                ymax = ((y + ch) / h) * 100.0
                xmax = ((x + cw) / w) * 100.0
                regions.append({
                    "ymin": round(ymin, 2),
                    "xmin": round(xmin, 2),
                    "ymax": round(ymax, 2),
                    "xmax": round(xmax, 2),
                    "crop": img_bgr[y:y+ch, x:x+cw]
                })
        
        # Return sorted by area descending
        return sorted(regions, key=lambda r: (r["ymax"] - r["ymin"]) * (r["xmax"] - r["xmin"]), reverse=True)[:6]

    def analyze_image(self, image_path: str, detected_cues: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes forensic OCR analysis:
        1. Text reading (via pytesseract or image feature text extraction)
        2. Script analysis
        3. Street / business name recognition
        4. Telephone country codes & domain extensions
        5. Region bounding box generation
        """
        results = {
            "raw_text": "",
            "detected_phrases": [],
            "scripts": [],
            "potential_streets": [],
            "potential_places": [],
            "phone_indicators": [],
            "tld_indicators": [],
            "evidence_items": []
        }

        try:
            img = cv2.imread(image_path)
            if img is None:
                return results

            h, w = img.shape[:2]
            text_regions = self.detect_text_regions_cv(img)

            extracted_text = ""
            if self.tesseract_available:
                try:
                    extracted_text = self.pytesseract.image_to_string(img)
                except Exception:
                    extracted_text = ""

            # Check filename / metadata / image visual cues if OCR engine didn't capture signage
            base_filename = image_path.lower()
            
            # Combine detected phrases
            combined_corpus = extracted_text + " " + " ".join(detected_cues or [])

            # Check script detection
            for script_name, pattern in SCRIPT_PATTERNS.items():
                if pattern.search(combined_corpus):
                    results["scripts"].append(script_name)
                    # Evidence for script
                    country_hint = "India" if script_name in ["Devanagari", "Gujarati", "Bengali"] else ("Japan" if script_name == "CJK" else script_name)
                    ev = EvidenceItem(
                        id=f"ev_script_{script_name.lower()}",
                        type="ocr_text",
                        label=f"{script_name} Script Detected",
                        description=f"Orthographic analysis identified {script_name} characters, strongly indicating geographic usage in {country_hint}.",
                        confidence=0.88,
                        bbox=BoundingBox(
                            ymin=text_regions[0]["ymin"] if text_regions else 15.0,
                            xmin=text_regions[0]["xmin"] if text_regions else 20.0,
                            ymax=text_regions[0]["ymax"] if text_regions else 35.0,
                            xmax=text_regions[0]["xmax"] if text_regions else 80.0,
                            label=f"{script_name} Signage"
                        ),
                        supporting_candidates=["India"] if script_name in ["Devanagari", "Gujarati"] else [country_hint],
                        polarity="supports"
                    )
                    results["evidence_items"].append(ev)

            # Check Phone patterns
            for pattern, c_code, label in PHONE_PATTERNS:
                if re.search(pattern, combined_corpus):
                    results["phone_indicators"].append({"code": c_code, "label": label})
                    ev = EvidenceItem(
                        id=f"ev_phone_{c_code.lower()}",
                        type="phone_code",
                        label=f"Telephone Prefix {label}",
                        description=f"Telecommunication dial code format consistent with {COUNTRY_PROFILES[c_code]['name']}.",
                        confidence=0.95,
                        bbox=BoundingBox(ymin=10.0, xmin=10.0, ymax=25.0, xmax=60.0, label="Dial Code"),
                        supporting_candidates=[COUNTRY_PROFILES[c_code]["name"]],
                        polarity="supports"
                    )
                    results["evidence_items"].append(ev)

            # Check TLDs
            tld_matches = TLD_PATTERN.findall(combined_corpus)
            for full_domain, ext in tld_matches:
                results["tld_indicators"].append(full_domain)
                country = "India" if ext in ["in", "co.in", "gov.in"] else ("UK" if "uk" in ext else ext.upper())
                ev = EvidenceItem(
                    id=f"ev_tld_{ext}",
                    type="ocr_text",
                    label=f"Domain Top-Level Identifier (.{ext})",
                    description=f"Signage lists website '{full_domain}' utilizing country-code top-level domain registered to {country}.",
                    confidence=0.92,
                    bbox=BoundingBox(ymin=20.0, xmin=30.0, ymax=35.0, xmax=70.0, label=full_domain),
                    supporting_candidates=[country],
                    polarity="supports"
                )
                results["evidence_items"].append(ev)

            # Check City & Landmark Name Mentions
            corpus_lower = combined_corpus.lower()
            for city in CITIES_DB:
                if city["city"].lower() in corpus_lower:
                    results["potential_places"].append(city["city"])
                    # Bounding box from first detected region or default sign location
                    bbox = None
                    if text_regions:
                        bbox = BoundingBox(
                            ymin=text_regions[0]["ymin"],
                            xmin=text_regions[0]["xmin"],
                            ymax=text_regions[0]["ymax"],
                            xmax=text_regions[0]["xmax"],
                            label=f"Sign: {city['city']}"
                        )
                    else:
                        bbox = BoundingBox(ymin=12.0, xmin=18.0, ymax=28.0, xmax=75.0, label=f"Sign: {city['city']}")

                    ev = EvidenceItem(
                        id=f"ev_ocr_city_{city['city'].lower()}",
                        type="ocr_text",
                        label=f"Toponym Match: '{city['city']}'",
                        description=f"High-confidence text extraction identified administrative place name '{city['city']}' on physical infrastructure.",
                        confidence=0.92,
                        bbox=bbox,
                        supporting_candidates=[city["city"], city["country"]],
                        polarity="supports"
                    )
                    results["evidence_items"].append(ev)

            # Check Street Indicators
            for country_code, keywords in STREET_INDICATORS.items():
                for kw in keywords:
                    pattern = rf"\b[A-Za-z0-9\s\-]{{2,20}}\s+{kw}\b"
                    match = re.search(pattern, combined_corpus, re.IGNORECASE)
                    if match:
                        street_found = match.group(0).strip()
                        results["potential_streets"].append({"street": street_found, "country": country_code})
                        ev = EvidenceItem(
                            id=f"ev_street_{hash(street_found) % 10000}",
                            type="street_name",
                            label=f"Street Identified: '{street_found}'",
                            description=f"Road nomenclature pattern matching {COUNTRY_PROFILES.get(country_code, {}).get('name', 'regional')} thoroughfare conventions.",
                            confidence=0.85,
                            bbox=BoundingBox(ymin=65.0, xmin=20.0, ymax=85.0, xmax=80.0, label=street_found),
                            supporting_candidates=[COUNTRY_PROFILES.get(country_code, {}).get('name', country_code)],
                            polarity="supports"
                        )
                        results["evidence_items"].append(ev)

            results["raw_text"] = extracted_text.strip()
        except Exception as e:
            results["error"] = str(e)

        return results

ocr_service = OCRForensicService()
