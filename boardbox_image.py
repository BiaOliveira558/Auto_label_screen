import cv2

def draw_bounding_boxes(image_path, bounding_boxes, scale=0.25):
    # Carregar a imagem
    image = cv2.imread(image_path)

    if image is None:
        print("Erro ao carregar a imagem.")
        return

    # Redimensionar a imagem
    width = int(image.shape[1] * scale)
    height = int(image.shape[0] * scale)
    resized_image = cv2.resize(image, (width, height))

    # Ajustar bounding boxes proporcionalmente
    scaled_boxes = [(int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale)) for x1, y1, x2, y2 in bounding_boxes]

    # Desenhar bounding boxes na imagem redimensionada
    for box in scaled_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(resized_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Verde

    # Exibir a imagem
    cv2.imshow("Imagem com Bounding Boxes", resized_image)
    cv2.waitKey(0)  # Aguarda uma tecla para fechar
    cv2.destroyAllWindows()

# Exemplo de uso
image_path = "C:/Users/bob/Documents/AutoLabelScreen-main/AutoLabelScreen-main/detect_element_screen/tests/test.png"
bounding_boxes = [(38, 0, 1042, 2012)]  # Lista de bounding boxes (x1, y1, x2, y2)
draw_bounding_boxes(image_path, bounding_boxes) 
