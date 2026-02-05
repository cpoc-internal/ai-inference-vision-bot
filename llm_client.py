from openai import OpenAI

def get_vllm_response(prompt, context, image_b64, vllm_url, model_name):
    client = OpenAI(base_url=vllm_url, api_key="EMPTY")
    
    # Constructing multimodal content
    text_content = f"Context: {context}\n\nQuestion: {prompt}"
    content_list = [{"type": "text", "text": text_content}]
    
    if image_b64:
        content_list.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
        })
    
    return client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": content_list}],
        stream=True
    )