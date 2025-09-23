import requests, json, re
import xml.etree.ElementTree as ET

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gpt-oss:20b"  


# ordem padrão dos atributos do dump para remontar a tag
ATTR_ORDER = [
    "index","text","resource-id","class","package","content-desc",
    "checkable","checked","clickable","enabled","focusable","focused",
    "scrollable","long-clickable","password","selected","bounds"
]

# palavras-chave para identificar "more options"
INCLUDE_HINTS = ["more options", "mais opções", "opções", "⋮", "..."]

def parse_bounds(bstr):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bstr or "")
    return tuple(map(int, m.groups())) if m else None

def node_to_xml_line(node):
    attrs = node.attrib
    parts = []
    for key in ATTR_ORDER:
        if key in attrs:
            parts.append(f'{key}="{attrs[key]}"')
    # se tiver atributos extras não listados, inclui também
    for k, v in attrs.items():
        if k not in ATTR_ORDER:
            parts.append(f'{k}="{v}"')
    return "<node " + " ".join(parts) + " />"

def extract_overflow_candidates(xml_path):

    '''Pega o XML inteiro com ElementTree.
       Percorre todos os <node>.
       Para cada nó:
        Verifica se clickable="true".
            Se não for clicável, já descarta.

        Se for clicável, pega class, text e content-desc.
        Filtro pelo text: se text não está vazio → descarta.
        Filtro pelo content-desc:
            Aceita se content-desc estiver vazio OU contiver alguma palavra da lista de “more options / mais opções / opções / …”.
            Caso contrário → descarta.
       Se passar em tudo isso, adiciona o node.attrib na lista de candidatos.
       Depois, a lista de candidatos é montada em <node ... /> numerados e passada para a LLM.
    '''

    tree = ET.parse(xml_path)
    root = tree.getroot()
    candidates = []

    for node in root.iter("node"):
        # pega somente os clicaveis 
        if node.get("clickable") != "true":
            continue
        # pega os text e content - desc 
        text = (node.get("text") or "").strip().lower()
        #desc = (node.get("content-desc") or "").lower()

        # precisa ter texto vazio
        if text != "":
            continue

        # content-desc pode estar vazio ou conter alguma das palavras-chave
        #if not (desc == "" or any(h in desc for h in INCLUDE_HINTS)):
            #continue

        candidates.append(node.attrib)
    return candidates

def query_llama(xml_path, element_hint="três pontinhos / more options"):
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

    print("prompt")
    prompt = f"""
Você é um assistente de automação de testes.

Aqui estão os nós candidatos numerados do dump XML (cada linha já mostra o nó completo):

{xml_excerpt}

Tarefa:
- Identifique todos os nós que correspondem ao botão "{element_hint}" (três pontinhos / more options).
- Pode haver mais de uma ocorrência. Nesse caso, retorne todos os índices separados por vírgula (ex: 0,2,5).
- ⚠️ Instruções obrigatórias:
  * Responda apenas com os números dos índices (ex: 0 ou 0,2,5).
  * Não escreva explicações, não escreva a tag <node>, não escreva "Resposta:".
  * Só responda "NADA" se realmente nenhum candidato for plausível.
"""



    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    resp = requests.post(OLLAMA_URL, json=data)
    resp.raise_for_status()
    out = resp.json()

    #print("🔎 Resposta crua:", out)
    raw = out.get("response", "").strip()

    try:
        idx = int(raw)
        if 0 <= idx < len(candidates):
            attrs = " ".join([f'{k}="{v}"' for k, v in candidates[idx].items()])
            return f"<node {attrs} />"
        else:
            return f"Índice inválido ({idx}) retornado pelo modelo."
    except ValueError:
        return f"Resposta não numérica: {raw}"

if __name__ == "__main__":
    print("Entrando")

    xml_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250916_103957.xml"

    print("pergunta")
    result = query_llama(xml_file)
    print("Resultado do modelo:\n", result)
