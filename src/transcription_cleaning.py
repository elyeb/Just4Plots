
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
files = ["1_Leonie.txt",
         "2_enfants_de_Leonie.txt",
         "3_histoire_de_Freddy.txt",
         "4_vente_de_patisserie.txt",
         "Rouff_2.txt",
         "Rouff_1.txt",
         "3_Untitled.txt",
         "2_Untitled.txt",
         "1_Untitled.txt"]

for file in files:
    file_out = file.split(".")[0]+"_clean.txt"

    with open(FOLDER+file,"r",encoding="latin1") as f:
        doc = f.readlines()


    speakers = ["JACQUELINE: ","SYLVIE: ","PAUL: "]
    doc = [re.sub(r': ([a-z])', lambda match: f': {match.group(1).upper()}', line) for line in doc]
    doc = ''.join(doc)

    # remove double spaces and spaces around — .
    doc = re.sub(r' +', ' ', doc)
    doc = re.sub(r' —', '—', doc)

    for s in speakers:
        doc = doc.replace(s,"\n\n"+s)

    with open(FOLDER + "clean_txt/"+file_out, "w",encoding="latin1") as f:
        f.write(doc)