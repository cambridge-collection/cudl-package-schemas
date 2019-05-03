#!/usr/bin/python3

import xml.etree.ElementTree as ET
import os
import xml.dom.minidom as minidom
import sys
import getopt
import psycopg2


def main(argv):
    collection = None

    try:
        opts, args = getopt.getopt(argv, "h:o:d:u:p:c",
                                   ["host=", "output=", "db=", "username=", "password=", "collection="])

        if len(argv) not in [8, 10]:
            raise getopt.GetoptError("Incorrect number of arguments")

    except getopt.GetoptError as e:
        print(e.msg)
        print('Usage is: CollectionDBtoXML.py --host <dbhost> --output <outputfile> --db <database> '
              '--collection <collectionid> --username <dbusername> --password <dbuserpass>')
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h", "--host"):
            host = arg
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-d", "--db"):
            db = arg
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-c", "--collection"):
            collection = arg

    conn = None
    try:
        conn = psycopg2.connect(host=host, database=db, user=username, password=password)

        if collection:
            outputCollectionXML(collection, conn, output_file)

        # TODO We could extend this script to iterate through all collections.
        #else:
            # create a cursor
            # cur = conn.cursor()
            # cur.execute('SELECT collectionid from collections')
            # row = cur.fetchone()
            # collection = row[0]
            # cur.close
            # while row is not None:
            #     outputCollectionXML(collection, conn, output_file)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

    print("done.")


def outputCollectionXML(collection, conn, output_file):
    # create a cursor
    cursor = conn.cursor()

    cursor.execute('select collectionid, title, summaryurl, sponsorsurl, type, collectionorder, '
                   'parentcollectionid, metadescription  from collections where collectionid=%s', (collection,))

    ET.register_namespace("co", "http://cudl.lib.cam.ac.uk/1.0/CollectionType")
    ET.register_namespace("res", "http://cudl.lib.cam.ac.uk/1.0/ResourceType")

    xmlcollection = ET.Element("collection", {'id': collection, 'xmlns':'http://cudl.lib.cam.ac.uk/1.0/collection'})

    collectionrow = cursor.fetchone()

    collectionid = collectionrow[0]
    title = collectionrow[1]
    summaryurl = collectionrow[2]
    sponsorsurl = collectionrow[3]
    collectiontype = collectionrow[4]
    collectionorder = collectionrow[5]
    parentcollectionid = collectionrow[6]
    metadescription = collectionrow[7]

    xmltitle = ET.SubElement(xmlcollection, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}title')
    xmltitle.text = title

    xmltype = ET.SubElement(xmlcollection, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}type')
    xmltype.text = collectiontype

    xmlmeta = ET.SubElement(xmlcollection, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}metaDescription')
    xmlmeta.text = metadescription

    xmlresources = ET.SubElement(xmlcollection, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}resources')

    # Summary
    xmlresource = ET.SubElement(xmlresources, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}resource')
    xmlrestype = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}type')
    xmlrestype.text = "webcontent"
    xmlresrep = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}representation')
    xmlresrep.text = "html"
    xmlrestar = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}target')
    xmlrestar.text = "summary"
    xmlresloc = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}location')
    xmlresloc.text = summaryurl

    # Sponsors
    xmlresource = ET.SubElement(xmlresources, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}resource')
    xmlrestype = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}type')
    xmlrestype.text = "webcontent"
    xmlresrep = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}representation')
    xmlresrep.text = "html"
    xmlrestar = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}target')
    xmlrestar.text = "sponsors"
    xmlresloc = ET.SubElement(xmlresource, '{http://cudl.lib.cam.ac.uk/1.0/ResourceType}location')
    xmlresloc.text = sponsorsurl

    # Items
    cursor.close()
    cursor = conn.cursor()
    cursor.execute('select itemid from itemsincollection where collectionid=%s order by itemorder', (collection,))
    row = cursor.fetchone()
    if row is not None:
        xmlitems = ET.SubElement(xmlcollection, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}items')
        while row is not None:
            xmlitem = ET.SubElement(xmlitems, '{http://cudl.lib.cam.ac.uk/1.0/CollectionType}item',  {'id': row[0]})
            row = cursor.fetchone()

    cursor.close()

    # Write out the file

    xmlstr = ET.tostring(xmlcollection, encoding='UTF-8', method='xml')
    dom = minidom.parseString(xmlstr)
    xml = dom.toprettyxml(indent="   ", encoding='UTF-8')

    # create dir if it does not exist
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "wb") as f:
        f.write(xml)

    print("collection done")


if __name__ == "__main__":
    main(sys.argv[1:])
