class Dictionary:
    def __init__(self):
        self._all_words = None
    
    @property
    def all_words(self):
        if self._all_words is None:
            print("Initializing Dictionary")
            self._all_words = set()
            with open("Collins Scrabble Words (2019).txt",  "r", encoding='utf8') as file:

                file.readline()
                file.readline()
                for line in file:
                    self._all_words.add(line.strip().capitalize())
        return self._all_words
    
    def check_word(self, word: str):
        return word.strip().capitalize() in self.all_words

        
if __name__ == "__main__":
    d = Dictionary()
    words = ["AARDVARK", "  RIBOSOMES ", "cAT"]
    fake_words = ["avsdfa", "AARDVARKSS"]
    all_correct = True
    for word in words:
        if not d.check_word(word):
            all_correct = False
            print(f"Got {word} as a non-word when it is a word")
    for word in fake_words:
        if d.check_word(word):
            all_correct = False
            print(f"Got {word} as a word when it is not a word")
    if all_correct:
        print("all correct")
    else:
        print("No all correct")