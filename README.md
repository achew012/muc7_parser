# muc7_parser
To extract info from the really old muc dataset and its painful formatting

To run:

1. Extract the file into the same directory and label it muc_7
2. To extract the information from the XML formatted files, run "python muc_parser.py" -> produces intermediate output, "muc7.json" 
3. To aggregate the information to a list of document objects (unique doc ids, coref, ner, events and relations for each document), run "python muc_formatter.py"

TODO:
1. Merge and handle the duplicate keys and text files in formal and dryrun datasets
2. Add indices for the labels to the text
3. Cluster the coref labels with their related peers
