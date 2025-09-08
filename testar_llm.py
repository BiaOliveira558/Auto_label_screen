import requests, base64, json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2-vision:11b"  # ou o nome exato do `ollama list`

def load_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_generate(image_path):
    img_b64 = load_image_as_base64(image_path)

    data = {
        "model": MODEL,
        "prompt": "Descreva esta imagem em detalhes.",
        "images": [img_b64],  # aqui é "images" mesmo
        "stream": False
    }

    resp = requests.post(OLLAMA_URL, json=data)
    print("Status:", resp.status_code, resp.reason)
    print("Resposta bruta:\n", resp.text)

if __name__ == "__main__":
    img_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250615_215132.png"
    print("Testando chamada simples...")
    test_generate(img_file)
