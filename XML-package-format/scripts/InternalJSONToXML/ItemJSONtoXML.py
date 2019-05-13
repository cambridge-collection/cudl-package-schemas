#!/usr/bin/python3

import xml.etree.ElementTree as ET
import json
import ntpath
import os
import xml.dom.minidom as minidom
import urllib
import sys
import getopt
import re
import ItemValidation
import requests


def main(argv):
    input_file = ""
    output_file = ""
    json_data = None
    id = ""
    username = None
    password = None

    try:
        opts, args = getopt.getopt(argv, "i:o:v:up", ["input=", "output=", "validation=", "username=", "password="])

        if len(argv) not in [6, 10]:
            raise getopt.GetoptError("Incorrect number of arguments")

    except getopt.GetoptError as e:
        print(e.msg)
        print('Usage is: ItemJSONtoXML.py -i <inputfile> -o <outputfile> --validation True or')
        print('          ItemJSONtoXML.py -i <inputURL> -o <outputfile> --validation True or')
        print('          ItemJSONtoXML.py -i <inputURL> -o <outputfile> '
              '--validation True --username <urlusername> --password <userpass>')
        sys.exit()
    for opt, arg in opts:
        if opt in ("-i", "--input"):
            input_file = arg
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-v", "--validation"):
            validation = arg
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg

    if _is_url(input_file):

        if not username or not password:
            r = requests.get(input_file)
        else:
            r = requests.get(input_file, auth=(username, password))
        json_data = r.text

        if r.status_code != 200:
            raise Exception("Problem getting JSON from URL, error code: " + str(r.status_code))

        # Get id from file name.
        a = urllib.parse.urlparse(input_file)
        id = os.path.basename(a.path).replace('.json', '')

    else:
        with open(input_file, 'r') as f:
            json_data = f.read()
            # Get id from file name.
            id = ntpath.basename(f.name.replace('.json', ''))

    if validation.lower() == 'true':
        print("validating " + id + " ...")
        ItemValidation.validate(json_data)

    print("generating XML for " + id + " ...")
    # Requires a .json file as input.
    json_obj = json.loads(json_data)

    item = ET.Element("item", {'xmlns': 'http://cudl.lib.cam.ac.uk/1.0/item',
                               'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                               'xsi:schemaLocation': 'http://cudl.lib.cam.ac.uk/1.0/item item.xsd',
                               'id': id})

    # Write out the iiifenabled and tagging status flags if present
    flags = ET.SubElement(item, 'flags')

    iiifenabled_value = json_obj.get("iiifenabled", "")
    if iiifenabled_value != "":
        iiifenabled = ET.SubElement(flags, 'iiifenabled')
        iiifenabled.text = json_obj.iiifenabled

    taggingstatus_value = json_obj.get("taggingstatus", "")
    if taggingstatus_value != "":
        taggingstatus = ET.SubElement(flags, 'taggingstatus')
        taggingstatus.text = json_obj.taggingstatus

    # Write out the resources flags
    resources = ET.SubElement(item, 'resources')

    # Metadata
    # Requires sourceData defined.
    # assume sourceData ends in ".../<sourceFormat>/.../"
    # e.g. /v1/metadata/tei/PH-GEOGRAPHY-35KAB-00034/
    resource = ET.SubElement(resources, 'resource')
    res_type = ET.SubElement(resource, 'type')
    res_type.text = "metadata"
    source_data = json_obj.get("sourceData")
    source_data_list = list(filter(None, source_data.split("/")))
    representation = ET.SubElement(resource, 'representation')
    representation.text = source_data_list[len(source_data_list) - 2]
    location = ET.SubElement(resource, 'location')
    location.text = source_data

    # Image resources
    # Requires IIIFImageURL in page.
    for page in json_obj.get("pages"):
        resource = ET.SubElement(resources, 'resource')
        res_type = ET.SubElement(resource, 'type')
        res_type.text = "image"
        representation = ET.SubElement(resource, 'representation')
        representation.text = os.path.splitext(page.get("IIIFImageURL"))[1][1:]
        location = ET.SubElement(resource, 'location')
        location.text = page.get("IIIFImageURL")

    xmlstr = ET.tostring(item, encoding='UTF-8', method='xml')
    dom = minidom.parseString(xmlstr)
    xml = dom.toprettyxml(indent="   ", encoding='UTF-8')

    # create dir if it does not exist
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "wb") as f:
        f.write(xml)

    print("done.")


def _is_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url)


if __name__ == "__main__":
    main(sys.argv[1:])
