import os
import sys

def git_push():
    try:
        os.system('git add .')
        os.system('git commit -m "commit message"')
        os.system('git push origin main')
        print("Git push successful")
    except Exception as e:
        print("Git push failed: ", str(e))

if __name__ == "__main__":
    git_push()
