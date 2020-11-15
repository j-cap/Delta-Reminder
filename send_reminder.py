
import sys

from utils_deltachat import check_sitzungen, send_mails

def main():

    print(sys.version)
    pw = sys.argv[1]
    new = check_sitzungen()
    send_mails(dates=new, pw=pw) #,end_to="jakobweber@hotmail.com")
    
if __name__ == "__main__":
    main()






# BHWiL3o68ed37C1
