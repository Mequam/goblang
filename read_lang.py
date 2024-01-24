import re

#moves everything after a #
def remove_comments(data : str)->str:
    return data.split("#")[0]


#generates a token setup for a given language file
def create_parse_tree(path : str):
    continuation = re.compile("\\s+.+")

    ret_val = {}
    last_entry = ""
    with open(path,'r') as f:
        for line in f:
            line = remove_comments(line[:-1]) #strip new lines at the end
            
            if line == "" or line == "\n":
                continue

            if continuation.match(line):
                ret_val[last_entry] += "|"+line.lstrip()
                continue
            
            split_data = line.split('=')
            
            
            if split_data[1] == "":
                add_to = split_data[1]

            ret_val[split_data[0]] = split_data[1]

            last_entry = split_data[0]
        else:
            print("end of the file")
        
        
        return ret_val



if __name__ == '__main__':
    print('[*] generating the parse tree')
    data = create_parse_tree("./example.lang")
    for entry in data:
        print(entry + str(data[entry]))
    print('[*] finished!')

