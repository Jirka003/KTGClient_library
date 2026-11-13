from ktgclient import KTGClient, HelpFuncs

##### not really important file, so nothing interesting here yet

url = "https://example.com/path_to_manipulate"
client = KTGClient()

r = client.ktg_simple_403_bypasser(url, change_request_method=True)
print(r)
