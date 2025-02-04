import requests
import json
import time
import os
from urllib.parse import unquote, urlparse

class BaiduImageGenerator:
    def __init__(self):
        self.url = "https://image.baidu.com/aigc/generate"
        self.query_url = "https://image.baidu.com/aigc/query"
        
        # Split headers for different endpoints
        self.generate_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        self.query_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        self.output_dir = "generated_images"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_image(self, prompt, width=480, height=640):
        data = {
            'query': prompt,
            'querycate': '8',
            'width': str(width),
            'height': str(height),
            'modelParameter[quality]': '1',
            'modelParameter[id]': '1',
            'uploadPic': '',
            'productSource': 'image'
        }

        try:
            response = requests.post(self.url, data=data, headers=self.generate_headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return None

    def query_task(self, task_id, prompt, token, timestamp):
        params = {
            'taskid': task_id,
            'token': token,
            'timestamp': timestamp,
            'modelParameter[id]': '1',
            'modelParameter[quality]': '1',
            'source': 'wen_b_page',
            'query': prompt,
            'productSource': 'image'
        }

        try:
            response = requests.get(
                self.query_url, 
                params=params,  # Use params for GET request
                headers=self.query_headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying task: {e}")
            return None

    def wait_for_completion(self, task_id, prompt, token, timestamp, max_attempts=30, delay=2):
        """Poll the task status until completion or max attempts reached."""
        for attempt in range(max_attempts):
            result = self.query_task(task_id, prompt, token, timestamp)
            if not result:
                return None

            if result.get('isGenerate', False) and result.get('progress', 0) == 100:
                return result
            
            print(f"Progress: {result.get('progress', 0)}%")
            time.sleep(delay)
        
        return None

    def download_image(self, url, filename):
        """Download an image from URL."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False

    def save_images(self, result, prompt):
        """Save all generated images from the result."""
        if 'picArr' not in result:
            return []

        saved_files = []
        timestamp = int(time.time())
        
        for i, pic in enumerate(result['picArr']):
            url = pic.get('src')
            if not url:
                continue
                
            # Create filename from prompt
            safe_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in (' ', '-', '_'))
            filename = f"{safe_prompt}_{timestamp}_{i+1}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            if self.download_image(url, filepath):
                saved_files.append(filepath)
                print(f"Saved image to: {filepath}")

        return saved_files

def main():
    generator = BaiduImageGenerator()
    prompt = "可爱的小胖猫在床上睡觉，周围是玩具和毛绒玩具。"
    
    # Generate image
    result = generator.generate_image(prompt)
    if not result:
        print("Failed to start generation")
        return
        
    print("Generation started...")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Get task information from correct response format
    if 'status' not in result or 'taskid' not in result:
        print("Invalid response format")
        return
        
    task_id = result['taskid']
    token = result.get('token', '')
    timestamp = result.get('timestamp', '')
    
    # Wait for completion
    print("\nWaiting for generation to complete...")
    final_result = generator.wait_for_completion(task_id, prompt, token, timestamp)
    
    if not final_result:
        print("Generation failed or timed out")
        return
        
    # Save images
    saved_files = generator.save_images(final_result, prompt)
    if saved_files:
        print(f"\nSuccessfully saved {len(saved_files)} images")
        for file in saved_files:
            print(f"- {file}")
    else:
        print("No images were saved")

if __name__ == "__main__":
    main()
