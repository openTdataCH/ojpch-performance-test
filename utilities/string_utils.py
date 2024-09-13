
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
