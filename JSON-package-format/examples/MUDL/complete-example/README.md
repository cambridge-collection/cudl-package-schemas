# An example of the input directory structure for CDL items.  

This directory contains the recommended structure to package the input into the CDL platform. 

The top level shows a file which contains information for the whole site, showing which 
collections it contains and which UI assets it needs. 

The next level shows a directory for each collection which contains separate 
directories for each item and a within that further divides into file types for that item.

```
mysite
├── mysite-dataset.json
└── mysite-ui.json
├── pages
│   ├── contributors.html
│   ├── help.html
│   ├── images
│   │   ├── help-image1.jpg
│   │   ├── index-collection1-banner.jpg
│   │   ├── index-collection2-banner.jpg
│   │   └── news-image1.jpg
│   ├── index-carousel-1.html
│   ├── index-carousel-2.html
│   ├── index-latest-news.html
│   ├── news.html
│   └── terms.html
├── collection1
│   ├── collection1.json
│   ├── description
│   │   ├── images
│   │   │   └── collection1-image1.jpg
│   │   ├── sponsors.html
│   │   └── summary.html
│   ├── item1
│   │   ├── images
│   │   │   ├── item1-image1.jp2
│   │   │   ├── item1-image2.jp2
│   │   │   └── item1-image3.jp2
│   │   └── item1.json
│   │   └── item1.tei.xml
│   └── item2
│       ├── images
│       │   └── item2-image1.jp2
│       └── item2.json
│       └── item2.tei.xml

...
```
