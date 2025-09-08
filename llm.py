import requests, base64, json
from PIL import Image
import xml.etree.ElementTree as ET

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2-vision:11b"  # confirme com `ollama list`

def load_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_clickable_nodes(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    clickable_nodes = []
    for node in root.iter("node"):
        if node.get("clickable") == "true":
            clickable_nodes.append(node.attrib)
    return clickable_nodes

def query_llama(xml_path, screen_path, element_hint="três pontinhos / more options"):
    print("entrou função query")
    candidates = extract_clickable_nodes(xml_path)

    # monta cada nó clicável como uma linha XML
    xml_excerpt = ""
    for cand in candidates:
        attrs = " ".join([f'{k}="{v}"' for k, v in cand.items()])
        xml_excerpt += f"<node {attrs} />\n"

    print("carrega imagem")
    screen_b64 = load_image_as_base64(screen_path)

    print("prompt")
    prompt = f"""
Você é um assistente de automação de testes.

Aqui estão apenas os nós clicáveis do dump XML da tela:

{xml_excerpt}

E aqui está a captura de tela correspondente.

Tarefa:
Encontre qual desses nós representa o botão "{element_hint}" (três pontinhos / more options).

O famoso botão dos três pontinhos é o chamado overflow menu do Android.
Ele aparece na interface como três pontos alinhados (normalmente verticais ⋮, mas em alguns casos horizontais …) e serve para abrir opções extras que não cabem diretamente na barra principal. É a forma que o sistema usa pra esconder configurações, ações secundárias ou menus de contexto.

Características típicas:
Ícone simples, três bolinhas.
Frequentemente no canto superior direito da tela (mas pode estar dentro de cards, listas ou barras internas).
Abre um menu suspenso com mais ações.
Geralmente implementado como um Button ou ImageButton com clickable="true" no dump XML, mas sem resource-id ou content-desc preenchidos.

👉 Ou seja: é o lugar onde ficam as “opções escondidas” de cada tela.

⚠️ Instruções obrigatórias:
- Retorne apenas o nó completo **exatamente como aparece no XML**, em uma única linha.
- Não acrescente explicações, comentários ou outros nós.
- A saída deve começar com <node e terminar com />.

Exemplo de formato esperado (com valores fictícios):

<node index="1" text="" resource-id="android:id/statusBarBackground"
      class="android.view.View" package="com.google.android.apps.classroom" content-desc=""
      checkable="false" checked="false" clickable="false" enabled="true" focusable="false"
      focused="false" scrollable="false" long-clickable="false" password="false"
      selected="false" bounds="[0,0][1080,65]" />

"""

    data = {
        "model": MODEL,
        "prompt": prompt,
        "images": [screen_b64],
        "stream": False
    }

    resp = requests.post(OLLAMA_URL, json=data)
    resp.raise_for_status()
    out = resp.json()

    # Debug completo para entender a resposta
    print("🔎 Resposta crua do Ollama:\n", out)

    if "response" in out:
        return out["response"].strip() or "NADA"
    return json.dumps(out, indent=2)

if __name__ == "__main__":
    print("Entrando")

    xml_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250615_215132.xml"
    screen_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250615_215132.png"

    print("pergunta")
    result = query_llama(xml_file, screen_file)
    print("Resultado do modelo:\n", result)
