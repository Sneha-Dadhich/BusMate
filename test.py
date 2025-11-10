def first_uni(word):
    freq = {}
    
    # Step 1: Count frequency of each character
    for w in word:
        if w in freq:
            freq[w] += 1
        else:
            freq[w] = 1

    # Step 2: Traverse original word again to preserve order
    for w in word:
        if freq[w] == 1:
            return w

    return -1  # if no non-repeating character found

print(first_uni("leetcode"))
print(first_uni("loveleetcode"))
print(first_uni("aabb"))
