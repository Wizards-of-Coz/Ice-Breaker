import random

QUESTION_PATH = "Resource/questions.txt"

class Questions:
    
    def __init__(self):
        self._questionArray = []
        f = open(QUESTION_PATH, 'r')
        for line in f:
            q = line[0:len(line)-1]
            self._questionArray.append(q)


    def getRandomQuestion(self):
        i = random.randrange(len(self._questionArray))
        return self._questionArray[i]


if __name__ == '__main__':
    q = Questions()
    print(q.getRandomQuestion())
