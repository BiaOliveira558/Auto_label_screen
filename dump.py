import os
import xml.etree.ElementTree as ET
import cv2
from datetime import datetime
import time
import subprocess

# Caminhos base
BASE_PATH = r"C:\Users\bob\Documents\AutoLabelScreen\detect_element_screen\teste"
IMG_DIR = os.path.join(BASE_PATH, "images")
XML_DIR = os.path.join(BASE_PATH, "xmls")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(XML_DIR, exist_ok=True)

# Lista de nomes amigáveis dos apps
apps = [
    "classroom",
    "calculadora",
    "chrome",
    "fotos",
    "play store",
    "apresentações",
    "google lens",
    "play games",
    "snapseed",
    "chat",
    "google cloud",
    "relogio",
    "tarefas",
    "webdevtools"
]

def get_installed_packages():
    """Obtém lista de pacotes de usuário instalados no aparelho via adb."""
    try:
        output = subprocess.check_output(["adb", "shell", "pm", "list", "packages", "-3"], text=True)
        packages = [line.split(":")[-1].strip() for line in output.splitlines() if line.strip()]
        return packages
    except subprocess.CalledProcessError:
        print("[ERRO] Falha ao listar pacotes instalados. Verifique se o dispositivo está conectado.")
        return []

def find_package_for_app(app_name, installed_packages):
    """
    Tenta encontrar o pacote mais provável para o app com base no nome amigável.
    Faz correspondência parcial (case-insensitive).
    """
    app_lower = app_name.lower().replace(" ", "")
    matches = [pkg for pkg in installed_packages if app_lower in pkg.lower().replace(".", "")]
    if matches:
        return matches[0]
    return None

def capture_screen(app_name, package):
    """Abre o app, captura screenshot e dump da interface."""
    if not package:
        print(f"[!] Pacote não encontrado para '{app_name}'. Pulando.")
        return None, None

    print(f"\n[📱] Abrindo app: {app_name} ({package})")

    # Abre o app no dispositivo
    os.system(f"adb shell monkey -p {package} 1 > NUL 2>&1")
    time.sleep(3)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = os.path.join(IMG_DIR, f"{app_name}_{timestamp}.png")
    dump_name = os.path.join(XML_DIR, f"{app_name}_{timestamp}.xml")

    # Screenshot
    os.system("adb shell screencap -p /sdcard/screenshot.png")
    os.system(f"adb pull /sdcard/screenshot.png \"{image_name}\" > NUL 2>&1")

    # Dump da interface
    os.system("adb shell uiautomator dump /sdcard/view_dump.xml")
    os.system(f"adb pull /sdcard/view_dump.xml \"{dump_name}\" > NUL 2>&1")

    print(f"  ├─ Screenshot: {image_name}")
    print(f"  └─ Dump XML:   {dump_name}")
    return image_name, dump_name

def parse_dump(dump_file):
    """Extrai elementos clicáveis e seus bounds do XML."""
    tree = ET.parse(dump_file)
    root = tree.getroot()
    elements = []

    for idx, node in enumerate(root.iter("node")):
        bounds = node.get("bounds")
        class_name = node.get("class")
        index = node.get("index")
        if bounds and class_name:
            coords = [int(x) for x in bounds.replace("[", " ").replace("]", " ").replace(",", " ").split()]
            if len(coords) == 4:
                elements.append((idx, class_name, coords, index))
            else:
                print(f"AVISO: Elemento {idx} ignorado, coordenadas inválidas: {coords}")

    return elements

def draw_bounding_boxes(image_path, elements):
    """Desenha retângulos dos elementos e salva imagem anotada."""
    img = cv2.imread(image_path)
    annotated_image = image_path.replace(".png", "_annotated.png")

    for idx, class_name, (x1, y1, x2, y2), index in elements:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{index}:{idx}: {class_name}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    cv2.imwrite(annotated_image, img)
    return annotated_image

def save_annotations(annotation_file, elements):
    """Salva as anotações em formato texto."""
    with open(annotation_file, "w", encoding="utf-8") as f:
        for idx, class_name, (x1, y1, x2, y2), index in elements:
            f.write(f"{idx} {class_name} {x1} {y1} {x2} {y2} {index}\n")

if __name__ == "__main__":
    print("\n========== INÍCIO DO LOOP DE CAPTURA ==========\n")

    installed_packages = get_installed_packages()
    print(f"Foram encontrados {len(installed_packages)} pacotes instalados no dispositivo.\n")

    for app in apps:
        package = find_package_for_app(app, installed_packages)
        img_file, dump_file = capture_screen(app, package)
        if not img_file or not dump_file:
            continue

        try:
            elements = parse_dump(dump_file)
            annotation_file = img_file.replace(".png", ".txt")
            save_annotations(annotation_file, elements)
            print(f"  ✔ Captura salva e anotada para: {app}\n")
        except Exception as e:
            print(f"[ERRO] Falha ao processar {app}: {e}\n")

    print("\n========== LOOP CONCLUÍDO ==========")
