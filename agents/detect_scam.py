"""
Refined scam detection module with improved error handling, 
performance optimizations, and better text highlighting.
"""

import os
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
                    "analysis": "No text found to analyze",
                    "scam_type": "Unknown",
                    "category": "Unknown"
                }
            
            # Enhanced system prompt for better scam detection
            system_prompt = (
                "You are a cybersecurity expert specializing in scam detection. "
                "Analyze text for common scam indicators including: urgency tactics, "
                "suspicious URLs, fake offers, phishing attempts, social engineering, "
                "grammar/spelling errors typical of scams, requests for personal info, "
                "cryptocurrency schemes, and fake authority claims. "
                "If scam_type is not applicable, set it to 'Unknown'."
            )
            
            user_prompt = (
                f"Analyze this text for scam indicators and return a JSON response with:\n"
                f"- 'scam_phrases': array of specific suspicious phrases found\n"
                f"- 'risk_level': 'Low', 'Medium', or 'High'\n"
                f"- 'confidence': confidence score (0-100)\n"
                f"- 'analysis': brief explanation of findings\n"
                f"- 'scam_type': scam type detected\n"
                f"- 'category': which sector this scam is targeting\n\n"
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
            "scam_type": "Unknown",
            "category": "Unknown"
        }

    def _validate_scam_result(self, result: Dict) -> Dict:
        """Validate and ensure required keys exist in scam detection result."""
        required_keys = {
            "scam_phrases": [],
            "risk_level": "Low",
            "confidence": 0,
            "analysis": "No analysis available",
            "scam_type": "Unknown",
            "category": "Unknown"
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

    
# Convenience functions for backward compatibility
def ocr_with_openai(image_bytes: bytes) -> str:
    """Extract text from image bytes using OpenAI Vision API."""
    detector = ScamDetector()
    return detector.ocr_with_openai(image_bytes)


def detect_scam_text(extracted_text: str) -> Dict:
    """Detect scam phrases in text using OpenAI."""
    detector = ScamDetector()
    return detector.detect_scam_text(extracted_text)