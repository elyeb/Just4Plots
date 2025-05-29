import re

FOLDER = "/Users/elyebliss/Documents/jacqueline_transcripts/"

# file = "1_Leonie.txt"
# file ="2_enfants_de_Leonie.txt"
# file ="Colmar_2.txt"
# file = "Colmar_1.txt"
# file = "Rouff_2.txt"
# file = "Rouff_1.txt"
# file = "3_Untitled.txt"
# file = "2_Untitled.txt"
# file = "1_Untitled.txt"
files = [
    "1_Leonie.txt",
    "2_enfants_de_Leonie.txt",
    "3_histoire_de_Freddy.txt",
    "4_vente_de_patisserie.txt",
    "Rouff_2.txt",
    "Rouff_1.txt",
    "3_Untitled.txt",
    "2_Untitled.txt",
    "1_Untitled.txt",
]

for file in files:
    file_out = file.split(".")[0] + "_clean.txt"

    with open(FOLDER + file, "r", encoding="latin1") as f:
        doc = f.readlines()

    speakers = ["JACQUELINE: ", "SYLVIE: ", "PAUL: "]
    doc = [
        re.sub(r": ([a-z])", lambda match: f": {match.group(1).upper()}", line)
        for line in doc
    ]
    doc = "".join(doc)

    # remove double spaces and spaces around — .
    doc = re.sub(r" +", " ", doc)
    doc = re.sub(r" —", "—", doc)

    for s in speakers:
        doc = doc.replace(s, "\n\n" + s)

    with open(FOLDER + "clean_txt/" + file_out, "w", encoding="latin1") as f:
        f.write(doc)

# split into individual files for Youtube uploading
speakers = ["JACQUELINE: ", "SYLVIE: ", "PAUL: "]
Sections = [
    "Partie I – Léonie",
    "Partie II – Les Énfants de Léonie",
    "Partie III – Histoire de Freddy",
    "Partie IV – Vente de la Pâtisserie",
    "Partie V – Mariage",
    "Partie VI – Rouffach",
    "Partie VII - Tante Irène",
    "Partie VIII – Francis",
    "Partie IX - Margaux",
]
outfile_dict = {
    "Partie I – Léonie": "1_Leonie.txt",
    "Partie II – Les Énfants de Léonie": "2_enfants_de_Leonie.txt",
    "Partie III – Histoire de Freddy": "3_histoire_de_Freddy.txt",
    "Partie IV – Vente de la Pâtisserie": "4_vente_de_patisserie.txt",
    "Partie V – Mariage": "5_mariage.txt",
    "Partie VI – Rouffach": "6_rouffach.txt",
    "Partie VII - Tante Irène": "7_tante_irene.txt",
    "Partie VIII – Francis": "8_francis.txt",
    "Partie IX - Margaux": "9_margaux.txt",
}
with open(FOLDER + "clean_txt/" + "combined.txt", "r", encoding="utf-16") as f:
    doc = f.readlines()
doc = "".join(doc)

escaped_delimiters = [re.escape(d) for d in Sections]
pattern = '|'.join(escaped_delimiters)
doc = re.split(pattern, doc)
doc = doc[1:]

new_doc = []
for d in doc:
    d = re.sub(r" +", " ", d)
    d = d.replace("\n", "")
    new_doc.append(d)

outfile_keys = list(outfile_dict.keys())
for i in range(0,len(outfile_keys)):
    outfile = outfile_keys[i]
    file = outfile_dict[outfile]
    
    with open(FOLDER + "clean_txt/" + file, "w", encoding="utf-16") as f:
        f.write(new_doc[i])