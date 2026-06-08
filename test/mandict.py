
tasks = {
    "push_cert":0,
    "push_firm":1,
    "push_pers":0,
    "push_BLE":0,
}

paths = {
    "cert_path":"path/to/cert",
    "firmware_path":"path/to/firmware",
    "personality_path":"path/to/personality",
    "BLE_path":"path/to/BLE"
}

paths_empty = {
    "cert_path":None,
    "firmware_path":None,
    "personality_path":None,
    "BLE_path":None
}


progress_bar_object:object=None

if not progress_bar_object:
    print("progress bar does not exists")

# print(tasks.values())
# print(tasks.keys())

# if 1 in tasks.values():
#     print("lest roll")

# if any(isinstance(v, str) for v in paths_empty.values()):
#     print("path exists")

if tasks.get("push_firm"): 
    print("firmware task is selected")