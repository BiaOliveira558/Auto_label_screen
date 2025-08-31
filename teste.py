import os
import xml.etree.ElementTree as ET
import cv2

def parse_bounds(bounds_str):
    """Converte '[x1,y1][x2,y2]' -> (x1, y1, x2, y2)"""
    b = bounds_str.replace("][", ",").replace("[", "").replace("]", "")
    return tuple(map(int, b.split(",")))  # x1, y1, x2, y2

def extract_overflow_menu_node(xml_file, img_width=None, appbar_max_y=300):
    """
    Tenta achar o botão de 'três pontinhos' (overflow) no topo direito.
    Heurística:
      - class == android.widget.Button
      - resource-id vazio
      - content-desc vazio
      - bounds no topo (y2 <= appbar_max_y)
      - encostado à direita (x2 muito próximo da largura da imagem, se conhecida)
    Retorna lista com o(s) node(s) candidato(s).
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    candidates = []

    def walk(node):
        if node.tag != "node":
            for child in node:
                walk(child)
            return

        cls = node.get("class", "")
        rid = node.get("resource-id", "")
        cdesc = node.get("content-desc", "")
        bounds = node.get("bounds")

        if cls == "android.widget.Button" and bounds:
            x1, y1, x2, y2 = parse_bounds(bounds)

            top_bar = (y2 <= appbar_max_y)
            empty_ids = (not rid) and (not cdesc)

            right_edge_ok = True
            if img_width is not None:
                # Considera como "encostado" se estiver a <= 20 px da borda direita
                right_edge_ok = (img_width - x2) <= 20

            if top_bar and empty_ids and right_edge_ok:
                candidates.append(node)

        for child in node.findall("node"):
            walk(child)

    walk(root)
    return candidates

def draw_bounding_boxes(image_path, xml_file,
                        output_path="C:/Users/bob/Documents/teste.png",
                        scale_percent=50):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Não consegui abrir a imagem: {image_path}")

    img_h, img_w = image.shape[:2]

    # Procura especificamente o botão de overflow (três pontinhos)
    nodes = extract_overflow_menu_node(xml_file, img_width=img_w, appbar_max_y=300)

    # Fallback opcional: se nada encontrado, não falhar silenciosamente
    if not nodes:
        print("Nenhum candidato a 'três pontinhos' encontrado pelas heurísticas.")
        print("Vou salvar apenas a imagem original, sem marcação.")
    else:
        for node in nodes:
            bounds = node.get("bounds")
            if not bounds:
                continue
            x1, y1, x2, y2 = parse_bounds(bounds)

            # Retângulo
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Rótulo
            label = "Overflow menu (3 pontinhos)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            txt_x = max(x1, 0)
            txt_y = max(y1 - 8, th + 4)
            cv2.rectangle(image, (txt_x, txt_y - th - 6), (txt_x + tw + 6, txt_y + 4), (0, 255, 0), -1)
            cv2.putText(image, label, (txt_x + 3, txt_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    # Redimensionar para exibir
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    # Salvar a imagem com bounding boxes
    cv2.imwrite(output_path, image)
    print(f"Imagem salva com bounding boxes: {output_path}")

    # Exibir a imagem redimensionada
    cv2.imshow("Bounding Boxes", resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Caminhos dos arquivos
image_path = r"C:\Users\bob\Documents\20250615_215132.png"
xml_file = r"C:\Users\bob\Documents\20250615_215132.xml"

# Executar
draw_bounding_boxes(image_path, xml_file, scale_percent=20)
