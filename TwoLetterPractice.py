score_to_letter_dist = {
    1:"aeilnorstu",
    2:"dg",
    3:"bcmp",
    4:"fhvwy",
    5:"k",
    8:"jx",
    10:"qz"
}

letter_to_score = {}
for score, letters in score_to_letter_dist.items():
    for letter in letters:
        letter_to_score[letter] = score

print(letter_to_score)
print(len(letter_to_score))

two_letter_words = []
with open("two_letter_words.txt", 'r') as in_file:
    for line in in_file:
        two_letter_words.extend([x.strip().lower() for x in line.split(", ")])

print(two_letter_words)
