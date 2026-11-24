

import chat
import time
class fivequestions():
#if __name__ == '__main__':
    ctr=0
    time.sleep(2)
    while (ctr<5):
        question = input("Please enter your question: ")
        print("You asked: ", question)
        answer=chat.return_answer(question)
        print ("Answer is: ", answer)
    ctr=ctr+1
