
import json
import xml.dom.minidom


def pretty_print_xml(ugly_xml: str) -> str:
    try:
        dom = xml.dom.minidom.parseString(ugly_xml)
        xml_str = dom.toprettyxml()
        return '\n'.join([line for line in xml_str.split('\n') if line.strip()])  # remove empty lines
    except Exception as e:
        return ugly_xml


def pretty_print_json(ugly_json: str) -> str:
    try:
        return json.dumps(json.loads(ugly_json), indent=2, ensure_ascii=False, sort_keys=False)
    except Exception as e:
        return ugly_json


def find_xml_element(xml_str: str, element_name: str):
    i1 = xml_str.find(element_name)
    i2 = xml_str.find('<', i1 + len(element_name))
    return xml_str[i1 + len(element_name):i2] if i1 >= 0 and i2 >= 0 else None


def find_xml_element_plus(xml_str: str, element_name: str, start = 0):
    """

    :param start: Start index to search from
    :param xml_str: String to search in
    :param element_name: Element name to search for with namespace (e.g. "ns1:element")
    :return:
    """
    start_element = f"<{element_name}>"
    start = xml_str.find(start_element, start)
    end = xml_str.find(f"</{element_name}>", start)
    return xml_str[start + len(start_element):end] if start >= 0 and end >= 0 else None, end


def find_all_xml_elements(xml_str: str, element_name: str):
    elements = []
    start = 0
    while True:
        element, start = find_xml_element_plus(xml_str, element_name, start)
        if element is None:
            break
        elements.append(element)
    return elements
