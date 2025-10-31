import requests, base64, xml.etree.ElementTree as ET, re, os, cv2
from typing import Dict, Any, List
import time


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llava:13b"

ATTR_ORDER = [
    "index","text","resource-id","class","package","content-desc",
    "checkable","checked","clickable","enabled","focusable","focused",
    "scrollable","long-clickable","password","selected","bounds"
]

INCLUDE_HINTS = [
    "more options", "mais opções", "More Actions", "more_actions_button",
    "⋮", "...", "Mais ações"
]


def mark_node_on_image(node_attrs: Dict[str, str], image_path: str, output_dir: str, scale_percent: int = 50) -> str:
    """Marca o nó identificado na imagem original e salva uma cópia anotada."""
    if "bounds" not in node_attrs:
        raise ValueError("O atributo 'bounds' não foi encontrado no nó selecionado.")

    os.makedirs(output_dir, exist_ok=True)
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    bounds = node_attrs["bounds"].replace("][", ",").replace("[", "").replace("]", "")
    x1, y1, x2, y2 = map(int, bounds.split(","))

    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

    label = node_attrs.get("class", "Elemento")
    cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    output_path = os.path.join(output_dir, f"{name}_annotated{ext}")

    cv2.imwrite(output_path, image)
    print(f"Imagem anotada salva em: {output_path}")

    #width = int(image.shape[1] * scale_percent / 100)
    #height = int(image.shape[0] * scale_percent / 100)
    #resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    #cv2.imshow("Elemento Marcado", resized)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    return output_path


def query_vlm_node(xml_path: str, image_path: str, element_hint: str = "três pontinhos / more options") -> Dict[str, Any]:
    """Lê o dump XML e imagem, identifica o nó alvo (via filtro ou VLM) e retorna os atributos do nó escolhido."""

    def load_image_as_base64(path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def extract_overflow_candidates(xml_path: str) -> List[Dict[str, Any]]:
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

    def node_to_xml_line(attrs: Dict[str, Any]) -> str:
        parts = []
        for key in ATTR_ORDER:
            if key in attrs:
                parts.append(f'{key}="{attrs[key]}"')
        for k, v in attrs.items():
            if k not in ATTR_ORDER:
                parts.append(f'{k}="{v}"')
        return "<node " + " ".join(parts) + " />"

    candidates = extract_overflow_candidates(xml_path)
    print(candidates)
    print(f"Foram encontrados {len(candidates)} candidatos.")

    if not candidates:
        raise ValueError("Nenhum nó candidato encontrado no XML.")

    if len(candidates) == 1:
        print("Apenas um nó candidato encontrado. Retornando diretamente.")
        return candidates[0]

    xml_excerpt = "\n".join(
        [f"[{i}] {node_to_xml_line(c)}" for i, c in enumerate(candidates)]
    )
    img_b64 = load_image_as_base64(image_path)

    # --- PROMPT REFORÇADO: foco em localização espacial ---
    prompt = f"""
Você é um assistente de automação de testes de interface. 
Recebeu uma captura de tela e uma **lista de nós XML candidatos**. 
Cada nó possui um atributo `bounds="[x1,y1][x2,y2]"` que representa sua posição e tamanho na tela.

Seu objetivo é identificar **EXATAMENTE UM** nó da lista que representa o ícone **Mais Opções (3 pontinhos / more options)**.

Critério de decisão (OBRIGATÓRIO):
1. **Análise de Localização:** Use seu conhecimento de design de interfaces para determinar onde o Ícone "Mais Opções" (que **geralmente fica no canto superior direito**) está **visualmente** localizado na captura de tela.
2. **Prioridade em Coordenadas:** Compare **RIGOROSAMENTE** essa localização visual esperada com o atributo `bounds="[x1,y1][x2,y2]"` de **CADA** nó candidato na lista.

Regras absolutas:
1. Você deve escolher **somente um nó da lista fornecida abaixo**.
2. O nó escolhido **deve estar exatamente na lista**, sem inventar novos.
3. Sua resposta deve conter **somente a tag XML do nó escolhido**, em uma única linha.
4. Não escreva comentários, explicações, markdown, nem qualquer outro texto.

Lista de nós candidatos:
{xml_excerpt}
"""

    data = {
        "model": MODEL,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }
    start_time = time.time()
    
    resp = requests.post(OLLAMA_URL, json=data)
    
    end_time = time.time()
    # ----------------------------------------------------
    # >>> FIM DA MEDIÇÃO DE LATÊNCIA <<<
    # ----------------------------------------------------
    
    total_latency = end_time - start_time
    
    resp.raise_for_status()
    out = resp.json() # Armazena a resposta JSON completa
    
    # 🐛 CORREÇÃO APLICADA AQUI: Usa a variável 'out' definida acima
    raw = out.get("response", "").strip() 

    # --- SAÍDA DA MÉTRICA DE LATÊNCIA ---
    print(f"\n=======================================================")
    print(f"**MÉTRICA DE LATÊNCIA: Tempo total da Requisição:** {total_latency:.2f} segundos")
    
    # Opcional: Latência por Token (Métrica mais detalhada do Ollama)
    eval_duration = out.get("eval_duration") # Tempo de avaliação do modelo (em nanosegundos, geralmente)
    eval_count = out.get("eval_count")        # Tokens gerados
    
    if eval_duration and eval_count:
        # 1e9 para converter nanosegundos para segundos
        eval_duration_sec = eval_duration / 1e9 
        latency_per_token = eval_duration_sec / eval_count
        print(f"[Latência Detalhada: {latency_per_token * 1000:.2f} ms/token (Total: {eval_count} tokens)]")
    
    print(f"=======================================================\n")
    # --- FIM DA SAÍDA DA MÉTRICA ---

    match = re.search(r"<node\b[^>]+/>", raw)
    if not match:
        print(f"[Aviso] Resposta inesperada do modelo. Usando fallback.\nResposta recebida:\n{raw}\n")
        # fallback: escolhe o nó com maior x2 e menor y1 (heurística direta)
        def parse_bounds(bounds_str):
            coords = re.findall(r"\d+", bounds_str)
            return list(map(int, coords)) if len(coords) == 4 else [0, 0, 0, 0]

        candidates.sort(key=lambda c: (-parse_bounds(c["bounds"])[2], parse_bounds(c["bounds"])[1]))
        return candidates[0]

    raw_node = match.group(0)
    selected_node = dict(re.findall(r'(\w+)="([^"]*)"', raw_node))
    return selected_node


# --- Execução em lote ---
if __name__ == "__main__":
    base_dir = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste"
    img_dir = os.path.join(base_dir, "images")
    xml_dir = os.path.join(base_dir, "xmls")
    output_dir = os.path.join(base_dir, "marked")

    os.makedirs(output_dir, exist_ok=True)

    images = [f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    print(f"\nEncontradas {len(images)} imagens para processar em: {img_dir}\n")

    for img_name in images:
        img_path = os.path.join(img_dir, img_name)
        name, _ = os.path.splitext(img_name)
        xml_path = os.path.join(xml_dir, f"{name}.xml")

        if not os.path.exists(xml_path):
            print(f"[!] XML correspondente não encontrado para {img_name}. Pulando.\n")
            continue

        try:
            node_attrs = query_vlm_node(xml_path, img_path)
            if node_attrs:
                mark_node_on_image(node_attrs, img_path, output_dir, scale_percent=40)
        except Exception as e:
            print(f"[Erro] Falha ao processar {img_name}: {e}\n")

    print("\n[✔] Processamento concluído para todas as imagens.")