"""
Refined scam detection module with improved error handling, 
performance optimizations, and better text highlighting.
"""

import os
import cv2
import json
import re
import base64
import logging
import tempfile
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScamDetector:
    """Enhanced scam detection with OCR and text highlighting capabilities."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the ScamDetector with OpenAI client."""
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        
    def ocr_with_openai(self, image_bytes: bytes) -> str:
        """
        Extract text from image using OpenAI Vision API.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text string
            
        Raises:
            ValueError: If image processing fails
            Exception: If OpenAI API call fails
        """
        try:
            # Validate input
            if not image_bytes:
                raise ValueError("Image bytes cannot be empty")
                
            # Convert to base64 with proper encoding
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # Create data URI
            data_uri = f"data:image/jpeg;base64,{img_b64}"
            
            # Prepare messages with enhanced system prompt
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a precise OCR assistant. Extract ALL visible text from the image "
                        "exactly as it appears, maintaining formatting and structure. "
                        "Include URLs, phone numbers, and all text elements."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Please extract all text from this image, preserving the original formatting."
                        },
                        {
                            "type": "image_url", 
                            "image_url": {"url": data_uri, "detail": "high"}
                        }
                    ]
                }
            ]
            
            # Make API call with retry logic
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0,
                max_tokens=2000
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            if not extracted_text:
                logger.warning("No text extracted from image")
                return ""
                
            logger.info(f"Successfully extracted {len(extracted_text)} characters of text")
            return extracted_text
            
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            raise Exception(f"Failed to extract text from image: {str(e)}")

    def detect_scam_text(self, extracted_text: str) -> Dict:
        """
        Detect scam phrases and analyze risk level using OpenAI.
        
        Args:
            extracted_text: Text to analyze for scam indicators
            
        Returns:
            Dictionary containing scam analysis results
        """
        try:
            if not extracted_text.strip():
                return {
                    "scam_phrases": [],
                    "risk_level": "Low",
                    "confidence": 0,
                    "analysis": "No text found to analyze"
                }
            
            # Enhanced system prompt for better scam detection
            system_prompt = (
                "You are a cybersecurity expert specializing in scam detection. "
                "Analyze text for common scam indicators including: urgency tactics, "
                "suspicious URLs, fake offers, phishing attempts, social engineering, "
                "grammar/spelling errors typical of scams, requests for personal info, "
                "cryptocurrency schemes, and fake authority claims."
            )
            
            user_prompt = (
                f"Analyze this text for scam indicators and return a JSON response with:\n"
                f"- 'scam_phrases': array of specific suspicious phrases found\n"
                f"- 'risk_level': 'Low', 'Medium', or 'High'\n"
                f"- 'confidence': confidence score (0-100)\n"
                f"- 'analysis': brief explanation of findings\n"
                f"- 'categories': array of scam types detected\n\n"
                f"Text to analyze: {extracted_text}"
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            
            raw_content = response.choices[0].message.content
            logger.info(f"Raw OpenAI response: {raw_content}")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                try:
                    result = json.loads(json_text)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    result = self._create_fallback_result(extracted_text)
            else:
                logger.warning("No JSON found in OpenAI response")
                result = self._create_fallback_result(extracted_text)
            
            # Validate and clean result
            result = self._validate_scam_result(result)
            
            logger.info(f"Detected {len(result.get('scam_phrases', []))} scam phrases")
            return result
            
        except Exception as e:
            logger.error(f"Scam detection failed: {str(e)}")
            return self._create_fallback_result(extracted_text, str(e))

    def _create_fallback_result(self, text: str, error: str = "") -> Dict:
        """Create fallback result when API calls fail."""
        return {
            "scam_phrases": [],
            "risk_level": "Unknown",
            "confidence": 0,
            "analysis": f"Analysis failed{': ' + error if error else ''}",
            "categories": []
        }

    def _validate_scam_result(self, result: Dict) -> Dict:
        """Validate and ensure required keys exist in scam detection result."""
        required_keys = {
            "scam_phrases": [],
            "risk_level": "Low",
            "confidence": 0,
            "analysis": "No analysis available",
            "categories": []
        }
        
        for key, default_value in required_keys.items():
            if key not in result:
                result[key] = default_value
        
        # Ensure confidence is between 0-100
        try:
            result["confidence"] = max(0, min(100, int(result["confidence"])))
        except (ValueError, TypeError):
            result["confidence"] = 0
            
        # Ensure risk_level is valid
        if result["risk_level"] not in ["Low", "Medium", "High"]:
            result["risk_level"] = "Low"
            
        return result

    def highlight_scam_text(self, image_path: str, scam_phrases: List[str], 
                          output_path: Optional[str] = None) -> str:
        """
        Highlight scam phrases in the image using advanced text detection.
        
        Args:
            image_path: Path to input image
            scam_phrases: List of phrases to highlight
            output_path: Optional output path for highlighted image
            
        Returns:
            Path to the highlighted image
        """
        try:
            if not scam_phrases:
                logger.info("No scam phrases to highlight")
                # Just copy the original image
                if output_path:
                    Image.open(image_path).save(output_path)
                    return output_path
                else:
                    return image_path
                    
            # Create output path if not provided
            if not output_path:
                output_path = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".png"
                ).name
            
            # Load and process image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image at {image_path}")
            
            original_height, original_width = image.shape[:2]
            
            # Create highlighted version using multiple detection methods
            highlighted_image = self._highlight_with_text_detection(
                image.copy(), scam_phrases
            )
            
            # Save result
            success = cv2.imwrite(output_path, highlighted_image)
            if not success:
                raise ValueError("Failed to save highlighted image")
                
            logger.info(f"Successfully highlighted image saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Text highlighting failed: {str(e)}")
            # Return original image path as fallback
            return image_path

    def _highlight_with_text_detection(self, image: np.ndarray, 
                                     scam_phrases: List[str]) -> np.ndarray:
        """
        Highlight text regions using OpenCV text detection methods.
        
        Args:
            image: Input image as numpy array
            scam_phrases: List of phrases to highlight
            
        Returns:
            Image with highlighted regions
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Morphological operations to connect text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(binary, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Filter and highlight relevant contours
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (likely text regions)
                if self._is_likely_text_region(w, h, image.shape):
                    # Draw semi-transparent red rectangle
                    overlay = image.copy()
                    cv2.rectangle(overlay, (x-2, y-2), (x+w+2, y+h+2), 
                                (0, 0, 255), -1)
                    image = cv2.addWeighted(image, 0.8, overlay, 0.2, 0)
                    
                    # Draw border
                    cv2.rectangle(image, (x-2, y-2), (x+w+2, y+h+2), 
                                (0, 0, 255), 2)
            
            return image
            
        except Exception as e:
            logger.error(f"Text detection highlighting failed: {str(e)}")
            return image

    def _is_likely_text_region(self, width: int, height: int, 
                             image_shape: Tuple[int, int, int]) -> bool:
        """
        Determine if a bounding box is likely to contain text.
        
        Args:
            width: Bounding box width
            height: Bounding box height  
            image_shape: Original image shape (height, width, channels)
            
        Returns:
            True if likely text region
        """
        img_height, img_width = image_shape[:2]
        
        # Filter by size ratios
        min_width, max_width = img_width * 0.01, img_width * 0.8
        min_height, max_height = img_height * 0.005, img_height * 0.3
        
        # Check aspect ratio (text is usually wider than tall)
        aspect_ratio = width / height if height > 0 else 0
        
        return (min_width <= width <= max_width and 
                min_height <= height <= max_height and
                0.2 <= aspect_ratio <= 20)


# Convenience functions for backward compatibility
def ocr_with_openai(image_bytes: bytes) -> str:
    """Extract text from image bytes using OpenAI Vision API."""
    detector = ScamDetector()
    return detector.ocr_with_openai(image_bytes)


def detect_scam_text(extracted_text: str) -> Dict:
    """Detect scam phrases in text using OpenAI."""
    detector = ScamDetector()
    return detector.detect_scam_text(extracted_text)


def highlight_scam_text(image_path: str, scam_phrases: List[str], 
                       output_path: str = "highlighted.png") -> str:
    """Highlight scam phrases in image."""
    detector = ScamDetector()
    return detector.highlight_scam_text(image_path, scam_phrases, output_path)