import requests, json, re, base64
import xml.etree.ElementTree as ET

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llava:13b"   # modelo VLM (aceita imagem)

# ordem padrão dos atributos do dump para remontar a tag
ATTR_ORDER = [
    "index","text","resource-id","class","package","content-desc",
    "checkable","checked","clickable","enabled","focusable","focused",
    "scrollable","long-clickable","password","selected","bounds"
]

# Palavras-chave (atualizadas)
INCLUDE_HINTS = [
    "more options", 
    "mais opções", 
    "More Actions", 
    "more_actions_button", 
    "⋮", 
    "...",
    "Mais ações"
]
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
        content_desc = (node.get("content-desc") or "").strip().lower()
        
        if text != "":
            continue 
            
        is_keyword_match = any(hint.lower() in content_desc for hint in INCLUDE_HINTS)

       
        if content_desc != "" and not is_keyword_match:
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
    numbered = []
    for i, cand in enumerate(candidates):
        attrs = " ".join([f'{k}="{v}"' for k, v in cand.items()])
        numbered.append(f"[{i}] <node {attrs} />")
    xml_excerpt = "\n".join(numbered)

    print("carregando imagem")
    img_b64 = load_image_as_base64(image_path)

    print("prompt")
    prompt = f"""
Você é um Assistente de Automação de Testes altamente especializado em análise de interfaces e coordenadas. Sua única tarefa é identificar e retornar a tag XML correta.

Input:
- Captura de tela da interface.
- Lista de Nós XML (`{xml_excerpt}`).
- Elemento Alvo: **Ícone "Mais Opções" (3 pontinhos/more options)**.

Instruções:
1. **Análise de Localização:** Use seu conhecimento de design de interfaces para determinar onde o Ícone "Mais Opções" (que **geralmente fica no canto superior direito**) está **visualmente** localizado na captura de tela.
2. **Prioridade em Coordenadas:** Compare **RIGOROSAMENTE** essa localização visual esperada com o atributo `bounds="[x1,y1][x2,y2]"` de **CADA** nó candidato na lista.
3. **Seleção Única:** Selecione **APENAS UM NÓ** da lista que representa o Ícone "Mais Opções". O ícone aparece **SOMENTE UMA VEZ**.
4. **Não invente nós.** A seleção deve ser **EXCLUSIVA** da lista de entrada.
5. **Formato de Saída (Regra Absoluta):** A saída **DEVE ser uma única linha** contendo **SOMENTE a *tag* XML completa** (`<node ... />`), exatamente como está na lista.
6. **Não inclua justificativas, explicações ou qualquer texto extra.**

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

    #Validação: deve retornar APENAS um <node ... />
    if raw.startswith("<node") and raw.endswith("/>"):
        return raw
    else:
        return f"Resposta inválida: {raw}"

if __name__ == "__main__":
    print("Entrando")

    xml_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250916_104049.xml"
    img_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250916_104049.png"

    print("pergunta")
    result = query_llama(xml_file, img_file)
    print("Resultado do modelo:\n", result)
