# this script finds the enviroment of two ipa symbols,
# and decides if they are phonemes or allophones.

### Imports ###
from ipapy import UNICODE_TO_IPA
from ipapy.ipastring import IPAString
from ipapy.ipachar import IPAConsonant
from ipapy.ipachar import IPAVowel
from ipatok import tokenise
import numpy as np
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog


### Functions ###

# This function finds the enviroment of a symbol within a given word, split to tokens
def get_neighbors(let, token_list, a_is_back=False):
    lst = []
    for i in [i for i in range(len(token_list)) if token_list[i] == let]:
        if i == 0:
            x = "#"
        else:
            x = make_valid_ipa(token_list[i - 1], a_is_back)

        if i == len(token_list) - 1:
            y = "#"
        else:
            y = make_valid_ipa(token_list[i + 1], a_is_back)
        lst.append((x, y))

    return lst


# this function recives two ipa symbols and a file with words.
# it outputs a dict of all the enviroments the symbols apeered in.
def find_env_with_diecretics(let1, let2, file_path, out_path, a_is_back=False):

    let_envs = {let1: [], let2: []}
    input_file = None
    output_file = None
    try:
        input_file = open(file_path, "r", encoding='utf8')
        output_file = open(out_path, "w", encoding="utf8")

        for line in input_file:

            line_toks = tokenise(line.strip())
            if let1 in line_toks:
                env = get_neighbors(let1, line_toks, a_is_back)
                let_envs[let1] += env
            if let2 in line_toks:
                env = get_neighbors(let2, line_toks, a_is_back)
                let_envs[let2] += env

        for let in let_envs:
            let_envs[let] = list(set(let_envs[let]))
            title = "enviroment for %s:" % let
            output_file.write(title + "\n" + "=" * len(title) + "\n")
            output_file.write("\n".join(["%s_%s" % tup for tup in let_envs[let]]) + "\n\n")

    except IOError:
        print("Faild to read from file")
    finally:
        if input_file:
            input_file.close()
        if output_file:
            output_file.close()
    return let_envs


# this function makes symbols with diacretics into valis ipa symbols
def make_valid_ipa(ipa_string, a_is_back=False):
    valid_ipa = ""
    try:
        if a_is_back and ipa_string == "a":
            valid_ipa = IPAVowel(name="open back unrounded vowel", descriptors=u"open back unrounded vowel",
                                 unicode_repr=u"a")
        else:
            valid_ipa = UNICODE_TO_IPA[u"%s" % ipa_string]
    except:
        ipa_string_list = list(IPAString(unicode_string=ipa_string))

        if str(ipa_string_list[0]) == "a":
            ipa_string_list[0] = IPAVowel(name="open back unrounded vowel", descriptors=u"open back unrounded vowel",
                                          unicode_repr=u"a")

        attrebiute_list = (ipa_string_list.pop(0)).name.split(" ")
        for diac in ipa_string_list:
            diac_attrbiute = diac.name.split(" ")[0]
            if diac_attrbiute == "voiced" and "voiceless" in attrebiute_list:
                attrebiute_list.remove("voiceless")
            elif diac_attrbiute == "voiceless" and "voiced" in attrebiute_list:
                attrebiute_list.remove("voiced")
            elif diac_attrbiute.endswith("ized"):
                diac_attrbiute = diac_attrbiute[:-4]
            attrebiute_list.append(diac_attrbiute)
        if "consonant" in attrebiute_list:
            valid_ipa = IPAConsonant(descriptors=attrebiute_list,
                                     name=" ".join(attrebiute_list),
                                     unicode_repr=u"%s" % ipa_string)
        else:
            valid_ipa = IPAVowel(descriptors=attrebiute_list,
                                 name=" ".join(attrebiute_list + ["voiced"]),
                                 unicode_repr=u"%s" % ipa_string)
    finally:
        return valid_ipa


# this function makes two list- one with the symbols, one with full description of the enviroments
def env_dict_to_lists(env_list, cls_dict):
    list_of_symbols = []
    list_of_proprties = []
    for env in env_list:
        list_of_symbols.append("%s_%s" % env)
        if env[0] != "#":
            x = env[0].name.split()
            cls_list = cls_dict.get(str(IPAString(unicode_string=str(env[0]))[0]), [])
            x += cls_list
        else:
            x = ["#"]
        if env[1] != "#":
            y = env[1].name.split()
            cls_list = cls_dict.get(str(IPAString(unicode_string=str(env[1]))[0]), [])
            y += cls_list
        else:
            y = ["#"]
        list_of_proprties.append((x, y))

    return list_of_symbols, list_of_proprties


# this function takes enviroment list and returns a relevant matrix
def make_env_mat(env_list, headers):
    mat = []
    for env in env_list:
        left = np.zeros(headers.shape)
        right = np.zeros(headers.shape)
        for prop in env[0]:
            left[headers == prop] = 1
        for prop in env[1]:
            right[headers == prop] = 1
        new_line = np.concatenate((left, right), axis=0)
        mat.append(new_line)
    return np.array(mat)


# this function find the commun enviroment for a symbol in a mat
def find_commun(mat, let, file, fields_list):
    out_file = None
    commun = np.zeros(shape=mat.shape[0])
    try:
        out_file = open(file, "a", encoding='utf8')
        commun = np.array(mat.all(axis=0))
        if commun.any():
            out_file.write("\nCommon env for %s:\n" % let)
            out_file.write("=" * len("common env for %s:"))
            out_file.write("\n")
            out_file.write(" ".join(fields_list[commun[:len(fields_list)] == 1]))
            out_file.write(" __ ")
            out_file.write(" ".join(fields_list[commun[len(fields_list):] == 1]))
            out_file.write("\n\n")

    except IOError:
        print("IO Error encounterd")
    finally:
        if out_file:
            out_file.close()
        return commun


# this function analaizes the enviroments
def analize_env(env_dict, path, ipa_1, ipa_2, include_class=False):
    out_file = None
    try:
        out_file = open(path, "a", encoding='utf8')
        if include_class:
            cls_dic = get_classes_dict("classes.txt")
        else:
            cls_dic = {}
        ipa1_sym_lst, ipa1_env_lst = env_dict_to_lists(env_dict[ipa_1], cls_dic)
        ipa2_sym_lst, ipa2_env_lst = env_dict_to_lists(env_dict[ipa_2], cls_dic)

        if not ipa1_env_lst or not ipa2_env_lst:
            out_file.write("At least one of the symbols did not appear at all in the file.")
            return "Bad info"

        # First test- minimal pairs
        for env in ipa1_sym_lst:
            if env in ipa2_sym_lst:
                out_file.write("Found minimal\\near-minimal pair:\n")
                out_file.write(str(env))
                out_file.write("\n%s and %s are different Phonemes." % (ipa_1, ipa_2))
                return "Phonemes"

        fields_list = []
        for tup in ipa2_env_lst + ipa1_env_lst:
            fields_list += tup[0]
            fields_list += tup[1]

        fields_list = np.array(list(set(fields_list)))

        mat1 = make_env_mat(ipa1_env_lst, fields_list)
        mat2 = make_env_mat(ipa2_env_lst, fields_list)

        commun_1 = find_commun(mat1, ipa_1, path, fields_list)
        commun_2 = find_commun(mat2, ipa_2, path, fields_list)

        if not commun_1.any() and not commun_2.any():
            out_file.write("Could not find commoun enviroment for either one.\n")
            out_file.write("Likely Phonemes, possibly bad data.")
            return "Phonemes"

        elif commun_1.any() and not commun_2.any():
            ind = compare_com_env_to_mat(commun_1, mat2)
            if ind == -1:
                out_file.write("%s never appered in commoun env for %s.\n" % (ipa_2, ipa_1))
                out_file.write("%s is likely an Allophone of %s.\n\n" % (ipa_1, ipa_2))
                out_file.write("Non-generelized rule for the process:\n")
                out_file.write("%s --> %s \\ " % (ipa_2, ipa_1))
                out_file.write(" ".join(fields_list[commun_1[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_1[len(fields_list):] == 1]))
                out_file.write("\n%s --> %s \\ e.w" % (ipa_2, ipa_2))
                return "Allophones"

            else:
                out_file.write("Found an enviroment for %s which matches commoun for %s:\n" % (ipa_2, ipa_1))
                out_file.write(ipa2_sym_lst[ind])
                out_file.write("\nLikely Phonemes.")
                return "Phonemes"

        elif commun_2.any() and not commun_1.any():
            ind = compare_com_env_to_mat(commun_2, mat1)
            if ind == -1:
                out_file.write("%s never appered in commoun env for %s.\n" % (ipa_1, ipa_2))
                out_file.write("%s is likely an Allophone of %s.\n\n" % (ipa_2, ipa_1))
                out_file.write("Non-generelized rule for the process:\n")
                out_file.write("%s --> %s \\ " % (ipa_1, ipa_2))
                out_file.write(" ".join(fields_list[commun_2[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_2[len(fields_list):] == 1]))
                out_file.write("\n%s --> %s \\ e.w" % (ipa_1, ipa_1))
                return "Allophones"
            else:
                out_file.write("\nFound an enviroment for %s which matches commoun for %s:\n" % (ipa_1, ipa_2))
                out_file.write(ipa1_sym_lst[ind])
                out_file.write("\nLikely Phonemes.")
                return "Phonemes"

        else:
            ind1 = compare_com_env_to_mat(commun_1, mat2)
            ind2 = compare_com_env_to_mat(commun_2, mat1)
            if ind2 != -1:
                out_file.write("\nFound an enviroment for %s which matches commoun for %s:\n" % (ipa_1, ipa_2))
                out_file.write(ipa1_sym_lst[ind2])
            if ind1 != -1:
                out_file.write("\nFound an enviroment for %s which matches commoun for %s:\n" % (ipa_2, ipa_1))
                out_file.write(ipa2_sym_lst[ind1])

            if ind1 != -1 and ind2 != -1:
                out_file.write("\nLikely Phonemes.")
                return "Phonemes"
            elif ind1 == -1 and ind2 != -1:
                # ipa2 comes first
                out_file.write("\n%s and %s are likely Allophones of the same phoneme.\n" % (ipa_2, ipa_1))
                out_file.write("The Phoneme might be different to these Allophones-\n")
                out_file.write("but out the two, %s is more likely to be the Phoneme.\n\n" % ipa_2)
                out_file.write("Non-generelized rule for the process:\n")
                out_file.write("[?] --> %s \\ " % ipa_2)
                out_file.write(" ".join(fields_list[commun_2[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_2[len(fields_list):] == 1]))
                out_file.write("\n[?] --> %s \\ " % ipa_1)
                out_file.write(" ".join(fields_list[commun_1[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_1[len(fields_list):] == 1]))

                return "Allophones"
            elif ind1 != -1 and ind2 == -1:
                # ipa1 comes first
                out_file.write("\n%s and %s are likely Allophones of the same phoneme.\n" % (ipa_2, ipa_1))
                out_file.write("The Phoneme might be different to these Allophones-\n")
                out_file.write("but out the two, %s is more likely to be the Phoneme.\n\n" % ipa_1)
                out_file.write("Non-generelized rule for the process:\n")
                out_file.write("[?] --> %s \\ " % ipa_1)
                out_file.write(" ".join(fields_list[commun_1[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_1[len(fields_list):] == 1]))
                out_file.write("\n[?] --> %s \\ " % ipa_2)
                out_file.write(" ".join(fields_list[commun_2[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_2[len(fields_list):] == 1]))

                return "Allophones"
            else:
                out_file.write("\n%s and %s are likely Allophones of the same phoneme.\n" % (ipa_2, ipa_1))
                out_file.write("The Phoneme might be different to these Allophones.\n")
                out_file.write("There is not enough info to determine the order of the rules,\n")
                out_file.write("or which is more likely the be the Phoneme if it is one of the two.\n\n")
                out_file.write("Non-generelized rule for the process:\n")
                out_file.write("[?] --> %s \\ " % ipa_1)
                out_file.write(" ".join(fields_list[commun_1[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_1[len(fields_list):] == 1]))
                out_file.write("\n[?] --> %s \\ " % ipa_2)
                out_file.write(" ".join(fields_list[commun_2[:len(fields_list)] == 1]))
                out_file.write(" __ ")
                out_file.write(" ".join(fields_list[commun_2[len(fields_list):] == 1]))

                return "Allophones"

    except IOError:
        print("Io Error")
    finally:
        if out_file:
            out_file.close()


# Check if any env in mat matches the commoun env of other ipa sym
def compare_com_env_to_mat(com, mat):
    relevant_inds = com == 1

    for i in range(mat.shape[0]):
        if mat[i][relevant_inds].all():
            return i
    return -1

# make a dict for natural classes from .txt file
def get_classes_dict(path):
    file = None
    cls_dict = {}
    try:
        file = open(path, encoding='utf8')
        for line in file:
            line = line.rstrip().split(":")
            cls = line[0]
            lets = line[1].split()
            for let in lets:
                cls_list = cls_dict.get(let, [])
                cls_list.append(cls)
                cls_dict[let] = cls_list
    except IOError:
        print("IO Error")
    finally:
        if file:
            file.close()
        return cls_dict


# Funtion for "go" button
def btn():
    full_path = path_entry.get().replace("/", "\\")
    out_path = full_path.split("\\")
    ipa1 = ipa1_entry.get()
    ipa2 = ipa2_entry.get()
    out_path = "\\".join(out_path[:-1]) + "\\%s_and_%s_enviroments_in_%s" % (ipa1, ipa2, out_path[-1])
    a_is_back = a_bool.get()
    include_class = class_bool.get()

    if not make_valid_ipa(ipa1) or not make_valid_ipa(ipa2):
        messagebox.showwarning("IPA Error",
                               "Problem with symbols input.\nMake sure both boxes include\nonly valid IPA signs and "
                               "diacretics.")
        return

    elif len(tokenise(ipa1)) != 1 or len(tokenise(ipa2)) != 1:
        messagebox.showwarning("IPA Error",
                               "Problem with symbols input.\nMake sure both boxes include\n one symbol, diacretics "
                               "optional.")
        return

    else:
        file = None
        try:
            file = open(full_path)
        except IOError:
            messagebox.showwarning("File Error",
                                   "Could not open input file.\nMake sure it is typed correctly,\nand not used by "
                                   "other programs.")
            return
        finally:
            if file:
                file.close()

    enviroments = find_env_with_diecretics(ipa1, ipa2, full_path, out_path, a_is_back=a_is_back)
    analize_env(enviroments, out_path, ipa1, ipa2, include_class=include_class)

    messagebox.showinfo("Done!", "A .txt file with the output\n as created at the same\nfolder as the input file.")

# function for file browser button
def browseFiles():
    path_entry.delete(0, tk.END)
    filepath = filedialog.askopenfilename(initialdir="/",
                                          title="Select a File",
                                          filetypes=(("Text files",
                                                     "*.txt*"),
                                                     ("all files",
                                                      "*.*")))
    path_entry.insert(0, filepath)


### Code ###
win = tk.Tk()

lbl_header1 = tk.Label(
    text="Phono",
    bg="#F2D7EE",
    padx=0,
    pady=20,
    fg="black",
    font=("Arial", 20)
)

lbl_header2 = tk.Label(
    text="Logic",
    bg="#F2D7EE",
    padx=0,
    pady=20,
    fg="#69306D",
    font=("Arial", 20)
)

button = tk.Button(
    text="Let's go!",
    width=10,
    height=1,
    bg="#69306D",
    fg="white",
    font=("Arial", 15),
    command=btn,
    pady=15,
    padx=10
)

entry_label = tk.Label(
    text="Enter the full path of a .txt file with words to analize:",
    bg="#F2D7EE",
    pady=30,
    fg="#0E103D",
    font=("Arial", 15)
)

path_entry = tk.Entry(width=40, font=("Arial", 13), bg="#D3BCC0", fg="#0E103D")

path_btn = tk.Button(
    text="Browse",
    bg="#69306D",
    fg="white",
    width=10,
    font=("Arial", 10),
    command=browseFiles)

ipa_entry_label = tk.Label(
    text="Enter two IPA symbols:",
    pady=20,
    fg="#0E103D",
    bg="#F2D7EE",
    font=("Arial", 15)
)

ipa1_entry = tk.Entry(
    width=5,
    font=("Arial", 15),
    bg="#D3BCC0",
    fg="#0E103D"
)

ipa2_entry = tk.Entry(
    width=5,
    font=("Arial", 15),
    bg="#D3BCC0",
    fg="#0E103D"
)

a_bool = tk.BooleanVar()
a_bool.set(True)

a_checkbox = tk.Checkbutton(
    text="Consider \"a\" as a back vowel",
    width=40,
    height=1,
    bg="#F2D7EE",
    fg="#0E103D",
    font=("Arial", 15),
    selectcolor="#F2D7EE",
    variable=a_bool,
    pady=20
)

class_bool = tk.BooleanVar()
class_bool.set(False)

class_checkbox = tk.Checkbutton(
    text="Include natural class in search",
    width=40,
    height=1,
    bg="#F2D7EE",
    fg="#0E103D",
    font=("Arial", 15),
    selectcolor="#F2D7EE",
    variable=class_bool,
    pady=20
)

lbl_header1.grid(column=0, row=0, sticky="E")
lbl_header2.grid(column=1, row=0, sticky="W")
entry_label.grid(columnspan=2, row=1)
path_btn.grid(column=1, row=2, pady=5)
path_entry.grid(columnspan=2, row=3)
ipa_entry_label.grid(row=4, column=0, columnspan=2)
ipa1_entry.grid(row=5, column=0, ipadx=5)
ipa2_entry.grid(row=5, column=1, ipadx=5)
a_checkbox.grid(row=6, columnspan=2)
class_checkbox.grid(row=7, columnspan=2)
button.grid(column=1, row=8, sticky="E")

win.configure(bg="#F2D7EE")
win.title("PhonoLogic")
# win.iconphoto(False, tk.PhotoImage(file="Resources\\icon.PNG"))
win.resizable(0, 0)
win.eval('tk::PlaceWindow . center')
win.mainloop()