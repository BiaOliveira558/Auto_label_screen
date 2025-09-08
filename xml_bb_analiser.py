import os
import xml.etree.ElementTree as ET
import cv2

def extract_clickable_nodes(xml_file):

    tree = ET.parse(xml_file)
    root = tree.getroot()
    clickable_nodes = []

    def find_clickable_nodes(node):
        
        if (
        node.get("index") == "0"
    and node.get("text") == ""
    and node.get("resource-id") == ""
    and node.get("class") == "android.widget.ImageView"
    and node.get("package") == "com.google.android.apps.classroom"
    and node.get("content-desc") == ""
    and node.get("checkable") == "false"
    and node.get("checked") == "false"
    and node.get("clickable") == "false"
    and node.get("enabled") == "true"
    and node.get("focusable") == "true"
    and node.get("focused") == "false"
    and node.get("scrollable") == "false"
    and node.get("long-clickable") == "false"
    and node.get("password") == "false"
    and node.get("selected") == "false"
    and node.get("bounds") == "[0,65][158,223]"):
            
            clickable_nodes.append(node)

        for child in node.findall("node"):
            find_clickable_nodes(child)

    find_clickable_nodes(root)
    return clickable_nodes

def draw_bounding_boxes(image_path, xml_file, output_path="C:/Users/bob/Documents/teste.png", scale_percent=50):
    image = cv2.imread(image_path)

    # Extrai os elementos clicáveis do XML
    nodes = extract_clickable_nodes(xml_file)

    for node in nodes:
        bounds = node.get("bounds")
        if bounds:
            # Transformar "[x1,y1][x2,y2]" em coordenadas numéricas
            bounds = bounds.replace("][", ",").replace("[", "").replace("]", "")
            x1, y1, x2, y2 = map(int, bounds.split(","))

            # Desenhar um retângulo na imagem
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Adicionar o nome da classe do elemento
            class_name = node.get("class", "Desconhecido")
            cv2.putText(image, class_name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Redimensionar a imagem antes de exibir
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    # Salvar a imagem com os bounding boxes
    cv2.imwrite(output_path, image)
    print(f"Imagem salva com bounding boxes: {output_path}")

    # Exibir a imagem redimensionada com bounding boxes
    cv2.imshow("Bounding Boxes", resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Caminhos dos arquivos

image_path = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250615_215132.png"
xml_file = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste\20250615_215132.xml"

# Executar o script para desenhar os bounding boxes e redimensionar a imagem
draw_bounding_boxes(image_path, xml_file, scale_percent=20)  # Resize para 50% do tamanho original
