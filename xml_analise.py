import xml.etree.ElementTree as ET

def extract_nodes(xml_file, target_hierarchy):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def find_nodes(node, hierarchy, level=0):
        if level >= len(hierarchy):
            return [node]

        tag = hierarchy[level]
        matching_nodes = []
        for child in node.findall("node"):
            if child.get("class") == tag:
                matching_nodes.extend(find_nodes(child, hierarchy, level + 1))

        return matching_nodes

    nodes = find_nodes(root, target_hierarchy)
    return nodes

# Exemplo de uso
xml_file = "C:/Users/bob/Documents/AutoLabelScreen-main/AutoLabelScreen-main/detect_element_screen/tests/20250225_171852 copy.xml"  # Substitua pelo nome do arquivo XML
target_hierarchy = [
    "android.widget.FrameLayout",
    "android.widget.LinearLayout",
    "android.widget.FrameLayout",
    "android.widget.FrameLayout",
    "android.widget.FrameLayout",
    "androidx.drawerlayout.widget.DrawerLayout",
    "android.view.ViewGroup",
    "android.widget.FrameLayout",
    "android.widget.ScrollView",
    "android.widget.LinearLayout",
    "android.widget.LinearLayout",
    "android.widget.EditText"
]

nodes = extract_nodes(xml_file, target_hierarchy)

for node in nodes:
    print(f"Texto: {node.get('text')}")
    print(f"Resource ID: {node.get('resource-id')}")
    print(f"Classe: {node.get('class')}")
    print(f"Bounds: {node.get('bounds')}")
    print("-" * 40)
