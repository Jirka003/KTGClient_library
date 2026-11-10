from ktgclient import KTGClient, HelpFuncs

url = "https://sametnagymjat.runasp.net/FUZZ"
wordlist = ["admin", "dashboard", "nananana","Workshopy"]

KTGClient.ktg_fuzz(url, wordlist, exclude_size=[5])


