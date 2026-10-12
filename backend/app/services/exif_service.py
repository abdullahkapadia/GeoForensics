import os
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from app.services.geospatial_db import find_nearest_city

def _convert_to_degrees(value) -> Optional[float]:
    """Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format"""
    try:
        if isinstance(value, (tuple, list)):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        return float(value)
    except Exception:
        return None

def extract_exif_data(image_path: str) -> Dict[str, Any]:
    """
    Extracts all forensic EXIF tags, camera details, GPS coordinates,
    and timestamps from image file.
    """
    result = {
        "has_exif": False,
        "has_gps": False,
        "gps": None,  # {lat: float, lng: float, altitude: float, nearest_city: dict}
        "camera": {
            "make": None,
            "model": None,
            "lens": None,
            "software": None
        },
        "timestamps": {
            "datetime_original": None,
            "datetime_digitized": None,
            "file_modify_date": None
        },
        "image_attributes": {
            "width": 0,
            "height": 0,
            "format": None,
            "color_mode": None,
            "orientation": None
        },
        "raw_tags": {}
    }

    try:
        with Image.open(image_path) as img:
            result["image_attributes"]["width"] = img.width
            result["image_attributes"]["height"] = img.height
            result["image_attributes"]["format"] = img.format
            result["image_attributes"]["color_mode"] = img.mode

            exif_raw = img.getexif()
            if not exif_raw:
                return result

            result["has_exif"] = True
            gps_info = {}

            for tag_id, val in exif_raw.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                
                # Camera
                if tag_name == "Make":
                    result["camera"]["make"] = str(val).strip()
                elif tag_name == "Model":
                    result["camera"]["model"] = str(val).strip()
                elif tag_name == "Software":
                    result["camera"]["software"] = str(val).strip()
                elif tag_name in ("DateTime", "DateTimeOriginal"):
                    result["timestamps"]["datetime_original"] = str(val).strip()
                elif tag_name == "Orientation":
                    result["image_attributes"]["orientation"] = int(val) if isinstance(val, int) else str(val)

                if tag_name == "GPSInfo":
                    # Parse GPS tags
                    if isinstance(val, dict):
                        for gps_id, gval in val.items():
                            gname = GPSTAGS.get(gps_id, str(gps_id))
                            gps_info[gname] = gval
                    elif hasattr(val, "items"):
                        for gps_id, gval in val.items():
                            gname = GPSTAGS.get(gps_id, str(gps_id))
                            gps_info[gname] = gval

            # Also check if Ifd.GPSInfo exists in get_ifd
            try:
                gps_ifd = exif_raw.get_ifd(ExifTags.IFD.GPSInfo)
                if gps_ifd:
                    for gps_id, gval in gps_ifd.items():
                        gname = GPSTAGS.get(gps_id, str(gps_id))
                        gps_info[gname] = gval
            except Exception:
                pass

            if gps_info:
                lat = None
                lng = None
                
                lat_raw = gps_info.get("GPSLatitude")
                lat_ref = gps_info.get("GPSLatitudeRef", "N")
                lng_raw = gps_info.get("GPSLongitude")
                lng_ref = gps_info.get("GPSLongitudeRef", "E")

                if lat_raw and lng_raw:
                    lat_deg = _convert_to_degrees(lat_raw)
                    lng_deg = _convert_to_degrees(lng_raw)
                    
                    if lat_deg is not None and lng_deg is not None:
                        if str(lat_ref).upper() == "S":
                            lat_deg = -lat_deg
                        if str(lng_ref).upper() == "W":
                            lng_deg = -lng_deg

                        # Validate coordinate sanity
                        if -90 <= lat_deg <= 90 and -180 <= lng_deg <= 180 and not (lat_deg == 0 and lng_deg == 0):
                            nearest_city, dist_km = find_nearest_city(lat_deg, lng_deg)
                            result["has_gps"] = True
                            result["gps"] = {
                                "latitude": round(lat_deg, 6),
                                "longitude": round(lng_deg, 6),
                                "lat_ref": str(lat_ref),
                                "lng_ref": str(lng_ref),
                                "altitude": float(gps_info.get("GPSAltitude", 0)) if "GPSAltitude" in gps_info else None,
                                "nearest_city": nearest_city["city"] if nearest_city else None,
                                "nearest_country": nearest_city["country"] if nearest_city else None,
                                "distance_to_nearest_city_km": round(dist_km, 2) if nearest_city else None
                            }

    except Exception as e:
        result["error"] = str(e)

    return result
