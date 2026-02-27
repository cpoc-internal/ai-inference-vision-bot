from openai import OpenAI
import yaml
with open("./config/config.yaml", "r") as f:
    config_yaml = yaml.safe_load(f)

def get_vllm_response(prompt, context, image_b64,available_images=None):
    client = OpenAI(base_url=config_yaml["base_url"], api_key="EMPTY")
    
    # Constructing multimodal content
    text_content = f"Context: {context}\n\nQuestion: {prompt}"
    content_list = [{"type": "text", "text": text_content}]
    image_list_str = ", ".join(available_images) if available_images else "None"

    system_prompt = f"""
    You are a helpful assistant. You have access to images extracted from the user's PDF.
    The available images are: {image_list_str}.
    If the user asks to see an image or if an image is highly relevant to your answer, 
    mention the filename exactly in your response like this: [SHOW_IMAGE: filename].
    """
    
    if image_b64:
        content_list.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
        })
    
    return client.chat.completions.create(
        model=config_yaml["vision_model3"],
        messages=[{"role": "user", "content": content_list}],
        stream=True
    )