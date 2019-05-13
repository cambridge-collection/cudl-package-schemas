JSON Package Format

This is currently a work in progress and subject to change.

These formats are designed to be simple for people to read and interpret and for users to handcraft if needed.

These formats define the users, collections and sites that make up a release for the CUDL (MUDL etc) digital library
platform. These are used when adding or updating the site content.

They are designed to be well defined and self-contained so that scripts can be written to convert existing content
to this format for ingest into the DL, or for tools to be crafted to allow easy generation of new content.

These files will be used by the 'cudl-pack' module which will convert these files to the internal formats used within the
digital library and are used on ingest to load or update the site content. 