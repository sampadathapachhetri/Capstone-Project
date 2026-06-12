import csv
from lxml import etree

# Use csv writer instead of manual writing — handles commas in text automatically
output_file = open("drug_interactions.csv", "w", encoding="utf-8", newline="")
writer = csv.writer(output_file, quoting=csv.QUOTE_ALL)
writer.writerow(["drug1_id", "drug2_id", "description"])

context = etree.iterparse("full database.xml", events=("end",), huge_tree=True)

for event, elem in context:
    if elem.tag.endswith("drug"):
        drug1 = elem.find(".//{http://www.drugbank.ca}drugbank-id")
        if drug1 is not None:
            interactions = elem.find(".//{http://www.drugbank.ca}drug-interactions")
            if interactions is not None:
                for interaction in interactions.findall(".//{http://www.drugbank.ca}drug-interaction"):
                    drug2 = interaction.find(".//{http://www.drugbank.ca}drugbank-id")
                    desc = interaction.find(".//{http://www.drugbank.ca}description")
                    if drug2 is not None and desc is not None:
                        writer.writerow([drug1.text, drug2.text, desc.text])
        elem.clear()

output_file.close()
print("Done! ✅ Check drug_interactions.csv")