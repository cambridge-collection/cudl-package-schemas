# CUDL JSON Package Format

This is currently a work in progress and subject to change.

These formats are designed to be simple for people to read and interpret and for users to handcraft if needed.

These formats define the users, collections and sites that make up a release for the CUDL (MUDL etc) digital library platform. These are used when adding or updating the site content.

The files that can be contained in an update are:

- `item.json` — this defines the metadata and properties for a book/manuscript. e.g. [MS-HEBREW-GASTER-00086.json][gaster-example]
- `collections.json` — This includes a text and html description of the collection and the items that it contains. e.g. Hebrew.json
- `site-dataset.json` — This is a file that specifies which collections make up the DL site. e.g. Manchester-data.json
- `site-ui.json` — This is a file that specifies the rest of the site, like the data for the news, faq, etc pages. e.g Manchester-ui.json

[gaster-example]: examples/MUDL/MS-HEBREW-GASTER-00086/MS-HEBREW-GASTER-00086.json

They are designed to be well defined and self-contained so that scripts can be written to convert existing content to this format for ingest into the DL, or for tools to be crafted to allow easy generation of new content.

These files will be used by the [`cudl-pack`](https://bitbucket.org/CUDL/cudl-pack/) program, which will convert these files to the internal formats used within the digital library and are used on ingest to load or update the site content.

## Item Schemas

There is a base item schema ([schemas/item.schema.json](schemas/item.schema.json)) which defines the structure which all digital library items will follow, and a specific schema per instance, which allows for variations in properties used for different institutions. So for Manchester data the [mudl.item.schema.json](schemas/mudl.item.schema.json) should be used and this extends the base schema with specific properties to help in data creation.

The schemas are as currently as restrictive as possible to catch any potential problems with data as soon as possible in the loading process.

There are three top level sections in the item schemas: properties, descriptions and pages. 

 - Properties holds the values used by the DL application for searching, display etc.
  such as "textDirection": "R", These values can be strings, numbers, booleans, 
  or Arrays of strings, numbers or booleans (not objects as we want a flat list 
  rather than a hierarchy).

 - Description is for metadata for display, such as "abstract", or "classmark".
 I have limited this to strings or arrays of strings as it's for display.
 
 - Pages is used to hold the information for each page, such as "image" or "label".
  This is limited to the information which we support for the page level. 
  Which for the moment is label, order, image, transcription and translation.
  

## Publishing

The schemas are published as a tarball NPM package on S3 at: `https://cudl-artefacts.s3.eu-west-1.amazonaws.com/projects/cudl-packaging/dist/cudl-schema-package-json-<version>.tgz`

The `Makefile` here is used to build and publish versions. To publish a release, set the version in `package.json` (or use the `$ npm version` command), then run `$ make` to build the package. Running `$ make publish` will build and then publish the package to S3 (you'll need to have credentials set up for AWS CLI).
