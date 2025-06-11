"""
LLM Processor sử dụng Gemma 3 cục bộ trong container hoặc thông qua Ollama
"""
import os
import json
import logging
import base64
import requests
import time
from typing import Dict, Any, Optional, List

# Thêm import cho transformers khi sử dụng mô hình cục bộ
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class LLMProcessor:
    """
    Xử lý văn bản và hình ảnh sử dụng Gemma 3
    """
    def __init__(self, model="google/gemma-2-2b", use_ollama=False):
        """
        Khởi tạo LLM processor
        
        Args:
            model: Mô hình cần sử dụng ("google/gemma-3b" hoặc model khác)
            use_ollama: Sử dụng Ollama (True) hoặc mô hình cục bộ (False)
        """
        self.model_name = model
        self.use_ollama = use_ollama
        self.use_local_model = os.environ.get("USE_LOCAL_MODEL", "true").lower() == "true"
        
        # Cấu hình Ollama (nếu sử dụng)
        self.ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Khởi tạo mô hình cục bộ (nếu sử dụng)
        self.tokenizer = None
        self.model = None
        
        if self.use_local_model and not self.use_ollama and TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading local model: {self.model_name}")
                # Sử dụng SafeTensors và float32 cho CPU
                model_kwargs = {
                    "low_cpu_mem_usage": True,
                    "torch_dtype": torch.float32
                }
                
                # Use the configured model instead of hardcoding
                model_name_to_use = self.model_name
                
                # Tải tokenizer và model
                self.tokenizer = AutoTokenizer.from_pretrained(model_name_to_use)
                # Add pad token if it doesn't exist
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name_to_use, 
                    device_map="auto" if torch.cuda.is_available() else "cpu",
                    **model_kwargs
                )
                logger.info("Local model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading local model: {e}")
                self.model = None
                self.tokenizer = None
        
        logger.info(f"Initializing LLM processor with model={self.model_name}, use_ollama={self.use_ollama}, use_local_model={self.use_local_model}")
        if self.use_ollama:
            logger.info(f"Ollama base URL: {self.ollama_base_url}")
    
    def enhance_text(self, text_input: str, language: str = "vie") -> str:
        """
        Cải thiện văn bản OCR sử dụng LLM
        
        Args:
            text_input: Văn bản cần cải thiện
            language: Ngôn ngữ của văn bản
        
        Returns:
            str: Văn bản đã được cải thiện
        """
        try:
            prompt = self._create_ocr_prompt(text_input, language)
            response = self._query_llm(prompt)
            enhanced = self._extract_ocr_text(response)
            
            # If LLM enhancement fails or returns empty, return original text
            if not enhanced or enhanced.strip() == "":
                logger.warning("LLM enhancement failed, returning original text")
                return text_input
            
            return enhanced
        except Exception as e:
            logger.error(f"Error in enhance_text: {e}")
            return text_input
    
    def extract_info(self, text: str, language: str = "vie") -> Dict[str, Any]:
        """
        Trích xuất thông tin từ văn bản CCCD/CMND
        
        Args:
            text: Văn bản cần trích xuất thông tin
            language: Ngôn ngữ của văn bản
        
        Returns:
            Dict[str, Any]: Thông tin đã trích xuất
        """
        prompt = self._create_extraction_prompt(text, language)
        response = self._query_llm(prompt)
        return self._extract_info_from_response(response)
    
    def _create_ocr_prompt(self, text_input: str, language: str) -> str:
        """
        Tạo prompt để cải thiện chất lượng OCR
        """
        if language.lower() in ["vi", "vie", "vietnamese"]:
            return f"""Hãy giúp tôi sửa chữa và cải thiện đoạn văn bản tiếng Việt đã được OCR.
Đoạn văn bản này có thể chứa lỗi nhận dạng, thiếu dấu câu hoặc dấu thanh không chính xác.
Hãy sửa các lỗi này nhưng giữ nguyên định dạng và cấu trúc của văn bản.

Văn bản cần sửa:
```
{text_input}
```

Văn bản đã được sửa:"""
        else:
            return f"""Please help me fix and improve this OCR-generated text.
This text may have recognition errors, missing punctuation, or incorrect formatting.
Please fix these issues while preserving the original format and structure.

Text to fix:
```
{text_input}
```

Corrected text:"""
    
    def _create_extraction_prompt(self, text: str, language: str) -> str:
        """
        Tạo prompt để trích xuất thông tin từ CCCD/CMND
        """
        if language.lower() in ["vi", "vie", "vietnamese"]:
            return f"""Dựa trên văn bản được nhận diện từ một CMND/CCCD Việt Nam, hãy trích xuất các thông tin sau:
- Số CMND/CCCD (id_number)
- Họ và tên (full_name)
- Ngày sinh (date_of_birth): định dạng DD/MM/YYYY
- Giới tính (gender)
- Quốc tịch (nationality)
- Quê quán (place_of_origin)
- Nơi thường trú (place_of_residence)
- Ngày hết hạn (expiry_date): định dạng DD/MM/YYYY nếu có
- Loại giấy tờ (document_type): "CCCD" hoặc "CMND"

Văn bản:
```
{text}
```

Hãy trả về kết quả ở định dạng JSON với các trường trên. Nếu không tìm thấy thông tin nào, hãy để trống trường đó."""
        else:
            return f"""Based on the text recognized from a Vietnamese ID card, please extract the following information:
- ID number (id_number)
- Full name (full_name)
- Date of birth (date_of_birth): format DD/MM/YYYY
- Gender (gender)
- Nationality (nationality)
- Place of origin (place_of_origin)
- Place of residence (place_of_residence)
- Expiry date (expiry_date): format DD/MM/YYYY if available
- Document type (document_type): "CCCD" or "CMND"

Text:
```
{text}
```

Please return the result in JSON format with the fields above. If any information is not found, leave that field empty."""
    
    def _query_llm(self, prompt: str) -> str:
        """
        Truy vấn LLM và trả về kết quả
        """
        try:
            if self.use_ollama:
                return self._query_ollama(prompt)
            elif self.use_local_model and self.model is not None and self.tokenizer is not None:
                return self._query_local_model(prompt)
            else:
                logger.warning("No valid LLM configuration available")
                return "LLM không khả dụng. Vui lòng kiểm tra cấu hình."
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return ""
    
    def _query_ollama(self, prompt: str) -> str:
        """
        Truy vấn Ollama và trả về kết quả
        """
        try:
            url = f"{self.ollama_base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return ""
    
    def _query_local_model(self, prompt: str) -> str:
        """
        Sử dụng mô hình cục bộ để tạo văn bản
        """
        try:
            logger.info("Querying local model")
            start_time = time.time()
            
            # Truncate prompt if too long to avoid memory issues
            max_prompt_length = 500
            if len(prompt) > max_prompt_length:
                prompt = prompt[:max_prompt_length] + "..."
            
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            # Generate with conservative parameters for faster response
            generate_kwargs = {
                "max_new_tokens": 200,  # Reduced from 1024
                "temperature": 0.7,
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "attention_mask": inputs.get("attention_mask")
            }
            
            # Generate with no_grad để tiết kiệm bộ nhớ
            with torch.no_grad():
                outputs = self.model.generate(inputs["input_ids"], **generate_kwargs)
                
            # Decode only the new tokens
            input_length = inputs["input_ids"].shape[1]
            if len(outputs[0]) > input_length:
                response = self.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
            else:
                response = ""
                
            logger.info(f"Local model response generated in {time.time() - start_time:.2f}s")
            return response.strip()
        except Exception as e:
            logger.error(f"Error querying local model: {e}")
            return ""
    
    def _extract_ocr_text(self, response: str) -> str:
        """
        Trích xuất văn bản từ phản hồi của LLM
        """
        if not response:
            return ""
        
        # Tìm văn bản giữa Corrected text: và cuối
        if "Văn bản đã được sửa:" in response:
            parts = response.split("Văn bản đã được sửa:")
            if len(parts) > 1:
                return parts[1].strip()
        elif "Corrected text:" in response:
            parts = response.split("Corrected text:")
            if len(parts) > 1:
                return parts[1].strip()
        
        return response.strip()
    
    def _extract_info_from_response(self, response: str) -> Dict[str, Any]:
        """
        Trích xuất thông tin JSON từ phản hồi của LLM
        """
        default_info = {
            "id_number": None,
            "full_name": None,
            "date_of_birth": None,
            "gender": None,
            "nationality": None,
            "place_of_origin": None,
            "place_of_residence": None,
            "expiry_date": None,
            "document_type": None
        }
        
        if not response:
            return default_info
        
        try:
            # Tìm JSON trong phản hồi
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                info = json.loads(json_str)
                
                # Đảm bảo tất cả các trường đều có
                for key in default_info:
                    if key not in info:
                        info[key] = default_info[key]
                
                return info
            else:
                # Trích xuất thông tin sử dụng các kỹ thuật đơn giản hơn
                return self._extract_info_manually(response)
        except json.JSONDecodeError:
            # Nếu không tìm thấy JSON hợp lệ, thử trích xuất thủ công
            return self._extract_info_manually(response)
        except Exception as e:
            logger.error(f"Error extracting info from response: {e}")
            return default_info
    
    def _extract_info_manually(self, response: str) -> Dict[str, Any]:
        """
        Trích xuất thông tin thủ công từ phản hồi văn bản
        """
        info = {
            "id_number": None,
            "full_name": None,
            "date_of_birth": None,
            "gender": None,
            "nationality": None,
            "place_of_origin": None,
            "place_of_residence": None,
            "expiry_date": None,
            "document_type": None
        }
        
        # Tìm kiếm các mẫu phổ biến trong văn bản
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                
                if "id" in key or "cmnd" in key or "cccd" in key or "number" in key:
                    info["id_number"] = value
                elif "name" in key or "họ và tên" in key or "họ tên" in key:
                    info["full_name"] = value
                elif "birth" in key or "ngày sinh" in key or "sinh" in key:
                    info["date_of_birth"] = value
                elif "gender" in key or "giới tính" in key or "sex" in key:
                    info["gender"] = value
                elif "national" in key or "quốc tịch" in key:
                    info["nationality"] = value
                elif "origin" in key or "quê quán" in key:
                    info["place_of_origin"] = value
                elif "residence" in key or "thường trú" in key or "nơi trú" in key:
                    info["place_of_residence"] = value
                elif "expiry" in key or "hết hạn" in key:
                    info["expiry_date"] = value
                elif "type" in key or "loại" in key:
                    info["document_type"] = value
        
        return info
