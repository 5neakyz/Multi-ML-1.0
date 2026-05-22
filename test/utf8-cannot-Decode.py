#bytes
#UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf9 in position 42: invalid start byte

y = b'\x41'
x = b'01/01/70,00:02:12 VIN:JCB5XMLWTR3412149\xf9                  \r\n'
print(y.decode("utf-8",errors='replace'))


commands = ["esc","9","d","w","b",chr(1)]
for command in commands:
    if command =="esc":
        command = (chr(27))
    if command =="ctrla":
        command = (chr(1))
    print(command.encode())