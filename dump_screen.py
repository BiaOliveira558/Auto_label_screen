import os
import xml.etree.ElementTree as ET
import cv2
from datetime import datetime


def capture_screen():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = f"C:/Users/bob/Documents/AutoLabelScreen/detect_element_screen/teste/images/{timestamp}.png"
    dump_name = f"/Users/bob/Documents/AutoLabelScreen/detect_element_screen/teste/xmls/{timestamp}.xml"

    # Captura de tela
    os.system("adb shell screencap -p /sdcard/screenshot.png")
    os.system(f"adb pull /sdcard/screenshot.png {image_name}")

    # Captura do dump da tela
    os.system("adb shell uiautomator dump /sdcard/view_dump.xml")
    os.system(f"adb pull /sdcard/view_dump.xml {dump_name}")

    return image_name, dump_name


def parse_dump(dump_file):
    tree = ET.parse(dump_file)
    root = tree.getroot()
    elements = []

    for idx, node in enumerate(root.iter("node")):
        bounds = node.get("bounds")
        class_name = node.get("class")
        index = node.get("index")
        if bounds and class_name:
            coords = [int(x) for x in bounds.replace("[", " ").replace("]", " ").replace(",", " ").split()]
            if len(coords) == 4:  # Garante que temos x1, y1, x2, y2
                elements.append((idx, class_name, coords, index))
            else:
                print(f"AVISO: Elemento {idx} ignorado, coordenadas inválidas: {coords}")

    return elements


def draw_bounding_boxes(image_path, elements):
    img = cv2.imread(image_path)
    annotated_image = image_path.replace(".png", "_annotated.png")

    for idx, class_name, (x1, y1, x2, y2), index in elements:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{index}:{idx}: {class_name}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.imwrite(annotated_image, img)
    return annotated_image


def save_annotations(annotation_file, elements):
    with open(annotation_file, "w") as f:
        for idx, class_name, (x1, y1, x2, y2), index in elements:
            f.write(f"{idx} {class_name} {x1} {y1} {x2} {y2} {index}\n")


if __name__ == "__main__":
    img_file, dump_file = capture_screen()
    elements = parse_dump(dump_file)
    #annotated_img = draw_bounding_boxes(img_file, elements)
    #annotation_file = img_file.replace(".png", ".txt")
    #save_annotations(annotation_file, elements)

    print(f"Imagem original salva em: {img_file}")
    #print(f"Imagem anotada salva em: {annotated_img}")
    #print(f"Arquivo de marcação salvo em: {annotation_file}")