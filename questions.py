import random

# path to question file
QUESTION_PATH = "Resource/questions.txt"

class Questions:
    
    def __init__(self):
        self._questionArray = []
        # load all questions from disk to memory
        f = open(QUESTION_PATH, 'r')
        for line in f:
            q = line[0:len(line)-1]
            self._questionArray.append(q)

    # get one question randomly. May be the same one as the previous question
    def getRandomQuestion(self):
        i = random.randrange(len(self._questionArray))
        return self._questionArray[i]


if __name__ == '__main__':
    q = Questions()
    print(q.getRandomQuestion())
