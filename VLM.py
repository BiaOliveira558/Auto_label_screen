import requests, json, re, base64
import xml.etree.ElementTree as ET

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5vl:32b"   # agora VLM, aceita imagem

# ordem padrão dos atributos do dump para remontar a tag
ATTR_ORDER = [
    "index","text","resource-id","class","package","content-desc",
    "checkable","checked","clickable","enabled","focusable","focused",
    "scrollable","long-clickable","password","selected","bounds"
]

# palavras-chave para identificar "more options"
INCLUDE_HINTS = ["more options", "mais opções", "opções", "⋮", "..."]

def load_image_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def node_to_xml_line(node):
    attrs = node.attrib
    parts = []
    for key in ATTR_ORDER:
        if key in attrs:
            parts.append(f'{key}="{attrs[key]}"')
    for k, v in attrs.items():
        if k not in ATTR_ORDER:
            parts.append(f'{k}="{v}"')
    return "<node " + " ".join(parts) + " />"

def extract_overflow_candidates(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    candidates = []
    for node in root.iter("node"):
        if node.get("clickable") != "true":
            continue
        text = (node.get("text") or "").strip().lower()
        if text != "":
            continue
        candidates.append(node.attrib)
    return candidates

def query_llama(xml_path, image_path, element_hint="três pontinhos / more options"):
    print("entrou função query")
    candidates = extract_overflow_candidates(xml_path)
    print(candidates)
    if not candidates:
        return "Nenhum candidato encontrado."

    # monta candidatos numerados
    '''numbered = []
    for i, cand in enumerate(candidates):
        attrs = " ".join([f'{k}="{v}"' for k, v in cand.items()])
        numbered.append(f"[{i}] <node {attrs} />")
    xml_excerpt = "\n".join(numbered)

    print("carregando imagem")
    img_b64 = load_image_as_base64(image_path)

    print("prompt")
    prompt = f"""
Você é um assistente de automação de testes.

Aqui estão os nós candidatos numerados do dump XML (cada linha já mostra o nó completo):

{xml_excerpt}

E aqui está a captura de tela da interface.

Tarefa:
- Identifique qual ou quais desses nós correspondem ao ícone "{element_hint}".
- Baseie sua escolha principalmente na posição dos elementos (atributo `bounds`) em relação à imagem fornecida.
- Pode haver múltiplas ocorrências do ícone.
- Se baseie muito na localização dos ícones da imagem de input

⚠️ Instruções obrigatórias:
1. Responda apenas com os números dos índices correspondentes, separados por vírgula (exemplo: 0,2,5).
2. Não escreva explicações, não repita os nós em XML e não acrescente palavras como "Resposta:".
3. Se nenhum nó corresponder, responda exatamente com: NADA
"""

    data = {
        "model": MODEL,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }

    resp = requests.post(OLLAMA_URL, json=data)
    resp.raise_for_status()
    out = resp.json()
    raw = out.get("response", "").strip()

    # pode retornar múltiplos índices
    try:
        indices = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        nodes = []
        for idx in indices:
            if 0 <= idx < len(candidates):
                attrs = " ".join([f'{k}="{v}"' for k, v in candidates[idx].items()])
                nodes.append(f"<node {attrs} />")
        return "\n".join(nodes) if nodes else f"Índices inválidos retornados: {raw}"
    except Exception:
        return f"Resposta não numérica: {raw}"'''

if __name__ == "__main__":
    print("Entrando")

    xml_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250916_103957.xml"
    img_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250916_103957.png"

    print("pergunta")
    result = query_llama(xml_file, img_file)
    print("Resultado do modelo:\n", result)
