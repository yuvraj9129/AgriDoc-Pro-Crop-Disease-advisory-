from typing import Dict, Tuple

import numpy as np
import cv2
from PIL import Image


def _to_hsv(image: Image.Image) -> np.ndarray:
    rgb = np.array(image)
    if rgb.ndim == 2:
        rgb = np.stack([rgb, rgb, rgb], axis=-1)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return hsv


def _fraction(mask: np.ndarray) -> float:
    total = mask.size
    if total == 0:
        return 0.0
    return float(mask.sum()) / float(total)


def _compute_masks(hsv: np.ndarray) -> Dict[str, np.ndarray]:
    h = hsv[:, :, 0].astype(np.uint8)  # 0-179 in OpenCV
    s = hsv[:, :, 1].astype(np.uint8)
    v = hsv[:, :, 2].astype(np.uint8)

    # Green leaf area mask
    green_mask = (
        (h >= 35) & (h <= 85) &  # green hues
        (s >= 50) & (v >= 50)
    )

    # Brown/dark spots (necrotic)
    brown_mask = (
        ((h >= 10) & (h <= 25) & (s >= 50) & (v <= 170)) |
        ((s <= 60) & (v <= 80))
    )

    # Powdery mildew: bright and low saturation on leaf areas
    powdery_mask = (s <= 40) & (v >= 200)

    # Yellowing (chlorosis): yellow hues with adequate brightness
    yellow_mask = (h >= 20) & (h <= 35) & (v >= 120)

    # Erode/dilate to stabilize noise
    kernel = np.ones((3, 3), np.uint8)
    brown_mask = cv2.morphologyEx(brown_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel, iterations=1) > 0
    powdery_mask = cv2.morphologyEx(powdery_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel, iterations=1) > 0
    yellow_mask = cv2.morphologyEx(yellow_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel, iterations=1) > 0
    green_mask = cv2.morphologyEx(green_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel, iterations=1) > 0

    return {
        "green": green_mask,
        "brown": brown_mask,
        "powdery": powdery_mask,
        "yellow": yellow_mask,
    }


def _decide_label(green_f: float, spot_f: float, powdery_f: float, yellow_f: float) -> Tuple[str, float]:
    # Thresholds chosen empirically for a simple heuristic
    if powdery_f >= 0.07 and green_f >= 0.1:
        strength = min(1.0, (powdery_f - 0.05) / 0.25 + 0.6)
        return "Powdery Mildew", float(strength)
    if spot_f >= 0.06 and green_f >= 0.1:
        strength = min(1.0, (spot_f - 0.04) / 0.3 + 0.55)
        return "Leaf Spot", float(strength)
    if yellow_f >= 0.15 and green_f >= 0.1:
        strength = min(1.0, (yellow_f - 0.1) / 0.4 + 0.5)
        return "Nutrient Deficiency", float(strength)
    # Healthy if enough green and limited issues
    if green_f >= 0.2 and max(spot_f, powdery_f, yellow_f) <= 0.08:
        strength = 0.7 - max(spot_f, powdery_f, yellow_f) * 0.5
        return "Healthy", float(max(0.5, strength))
    # Fallback
    residual = 1.0 - max(spot_f, powdery_f, yellow_f)
    return "Healthy", float(max(0.4, residual))


def analyze_leaf(image: Image.Image) -> Dict:
    """
    Analyze a leaf image using simple color-based heuristics.

    Returns a dict: {label, confidence, metrics}
    """
    hsv = _to_hsv(image)
    masks = _compute_masks(hsv)

    green_fraction = _fraction(masks["green"]) 
    spot_fraction = _fraction(masks["brown"]) 
    powdery_fraction = _fraction(masks["powdery"]) 
    yellow_fraction = _fraction(masks["yellow"]) 

    label, confidence = _decide_label(green_fraction, spot_fraction, powdery_fraction, yellow_fraction)

    return {
        "label": label,
        "confidence": float(max(0.0, min(1.0, confidence))),
        "metrics": {
            "green_fraction": float(green_fraction),
            "spot_fraction": float(spot_fraction),
            "powdery_fraction": float(powdery_fraction),
            "yellow_fraction": float(yellow_fraction),
        },
    }


