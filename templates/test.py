s = "This is duplicate duplicate string string"
no_of_duplicate = 0
if len(s) >  1:
    duplicate_word = []
    for i in s.split(" "): 
        if i not in duplicate_word and s.count(i) > 1 :
            duplicate_word.append(i)
            no_of_duplicate += 1
print(f"No of duplicate words = {no_of_duplicate}")